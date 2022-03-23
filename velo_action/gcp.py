import base64
import binascii
import json
import os
from functools import lru_cache
from typing import List

from google.api_core.exceptions import PermissionDenied
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import secretmanager, storage  # type: ignore
from google.oauth2 import service_account
from loguru import logger


class GCP:
    def __init__(self, service_account_key=None):
        self.scoped_credentials = None
        if service_account_key:
            self._auth_service_account(service_account_key)
        else:
            logger.info("Using local credentials.")

    @lru_cache
    def _get_storage_client(self):
        client = storage.Client(credentials=self.scoped_credentials)
        return client

    @lru_cache
    def _get_secrets_client(self):
        try:
            secrets_client = secretmanager.SecretManagerServiceClient(
                credentials=self.scoped_credentials
            )
        except DefaultCredentialsError as err:
            raise RuntimeError(
                "No valid credentials to access Google cloud. "
                "Please either specify the INPUT_SERVICE_ACCOUNT_KEY "
                "environment or authenticate using 'gcloud auth login'."
            ) from err

        return secrets_client

    def upload_from_directory(
        self, path, dest_bucket_name, dest_blob_name
    ) -> List[str]:
        client = self._get_storage_client()

        rel_paths = []
        for i in path.rglob("*"):
            rel_paths.append(i)

        bucket = client.get_bucket(dest_bucket_name)

        uploaded_files = []
        for local_file in rel_paths:
            relative_path = os.path.relpath(local_file, path)
            remote_path = os.path.join(dest_blob_name, relative_path)
            if os.path.isfile(local_file):
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_file)
                uploaded_files.append(relative_path)

        return uploaded_files

    def lookup_data(self, key, project_id, version=None):
        logger.debug(f"Looking for '{key}' in '{project_id}', with version '{version}'")
        secrets_client = self._get_secrets_client()
        if not version:
            version = self.get_highest_version(key, project_id)
        # noinspection PyTypeChecker
        try:
            secret = secrets_client.access_secret_version(
                request={
                    "name": f"projects/{project_id}/secrets/{key}/versions/{str(version)}"
                }
            ).payload.data.decode("utf-8")
        except PermissionDenied:
            msg = (
                f"Missing permission to access secret '{key}' in project '{project_id}'"
            )

            if not self.scoped_credentials:
                msg = msg + (
                    ". Elevate your permissions with:\nklipy power elevate --group "
                    "nube.project.editor.{project_id}"
                )
            raise SystemExit(msg)  # pylint: disable=raise-missing-from

        return secret

    def get_highest_version(self, key, project_id):
        secrets_client = self._get_secrets_client()
        parent = secrets_client.secret_path(project_id, key)
        logger.debug(f"Looking for new version for'{key}' in '{project_id}'")
        logger.debug(f"parent='{parent}'")
        logger.debug("----------------------")

        highest_found_version = None
        # noinspection PyTypeChecker
        for version in secrets_client.list_secret_versions(request={"parent": parent}):
            int_v = int(version.name.split("/")[-1])
            if not highest_found_version:
                highest_found_version = int_v
            elif int_v > highest_found_version:
                highest_found_version = int_v

        if not highest_found_version:
            raise ValueError("Secret not found")
        return highest_found_version

    def _auth_service_account(self, service_account_key):
        google_service_account_key_json_str = None
        try:
            google_service_account_key_json_str = base64.b64decode(
                service_account_key.encode("ascii")
            ).decode("ascii")
        except binascii.Error as err:
            logger.warning(f"INPUT_SERVICE_ACCOUNT_KEY was not base64 encoded. {err}")

        if google_service_account_key_json_str:
            service_account_info = json.loads(google_service_account_key_json_str)
        else:
            service_account_info = json.loads(service_account_key)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        self.scoped_credentials = credentials.with_scopes(
            ["https://www.googleapis.com/auth/cloud-platform"]
        )
