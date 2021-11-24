# type: ignore
import base64
import json
import logging
import os
from functools import lru_cache

from google.cloud import secretmanager, storage
from google.oauth2 import service_account

logger = logging.getLogger(name="gcp")


class GCP:
    def __init__(self, service_account_key):
        google_service_account_key_json_str = None
        try:
            google_service_account_key_json_str = base64.b64decode(
                service_account_key.encode("ascii")
            ).decode("ascii")
        except Exception as e:
            logger.debug("INPUT_SERVICE_ACCOUNT_KEY was not base64 encoded")

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

    @lru_cache
    def _get_storage_client(self):
        client = storage.Client(credentials=self.scoped_credentials)
        return client

    @lru_cache
    def _get_secrets_client(self):
        secrets_client = secretmanager.SecretManagerServiceClient(
            credentials=self.scoped_credentials
        )
        return secrets_client

    def upload_from_directory(self, path, dest_bucket_name, dest_blob_name):

        client = self._get_storage_client()

        rel_paths = []
        for p in path.rglob("*"):
            rel_paths.append(p)

        bucket = client.get_bucket(dest_bucket_name)

        for local_file in rel_paths:
            relative_path = os.path.relpath(local_file, path)
            remote_path = os.path.join(dest_blob_name, relative_path)
            if os.path.isfile(local_file):
                blob = bucket.blob(remote_path)
                blob.upload_from_filename(local_file)

    def lookup_data(self, key, project_id, version=None):
        logger.info(f"Looking for '{key}' in '{project_id}', with version '{version}'")
        secrets_client = self._get_secrets_client()
        if not version:
            version = self.get_highest_version(key, project_id)
        # noinspection PyTypeChecker
        secret = secrets_client.access_secret_version(
            request={
                "name": f"projects/{project_id}/secrets/{key}/versions/{str(version)}"
            }
        ).payload.data.decode("utf-8")

        return secret

    def get_highest_version(self, key, project_id):
        secrets_client = self._get_secrets_client()
        parent = secrets_client.secret_path(project_id, key)
        logger.info(f"Looking for new version for'{key}' in '{project_id}'")
        logger.info(f"parent='{parent}'")
        logger.info("----------------------")

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
