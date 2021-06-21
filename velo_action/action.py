import sys
import os
import os.path
import json
import base64
import binascii
import logging
import google.auth
from google.oauth2 import service_account
from pathlib import Path
import envargparse

print(sys.path)

from velo_action import octopus, utils, gitversion

BASE_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = envargparse.EnvArgParser(prog="Velo Action")

    parser.add_argument("--mode", "-m", env_var="INPUT_MODE", default="VERSION", type=str, required=False)
    parser.add_argument("--environment", env_var="ENVIRONMENT", default="staging", type=str, required=False)
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", default="INFO", type=str, required=False)

    if os.getenv("INPUT_MODE") == "DEPLOY":
        parser.add_argument("--octopus_cli_server", env_var="INPUT_OCTOPUS_CLI_SERVER", type=str, required=True)
        parser.add_argument("--octopus_cli_api_key", env_var="INPUT_OCTOPUS_CLI_API_KEY", type=str, required=True)
        parser.add_argument("--service_account_key", env_var="INPUT_SERVICE_ACCOUNT_KEY", type=str, required=True)
        parser.add_argument("--project", env_var="INPUT_PROJECT", type=str, required=True)

        parser.add_argument("--velo_artifact_bucket", env_var="VELO_ARTIFACT_BUCKET", default="nube-velo-prod-deploy-artifacts", type=str, required=False)
        parser.add_argument("--deploy_folder_path", env_var="DEPLOY_FOLDER_PATH", default=str(BASE_DIR / ".deploy"), type=str, required=False)

    args = parser.parse_args()
    args.mode = args.mode.upper()

    if args.log_level not in ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]:
        logging.basicConfig(level=logging.INFO)
    return args


def action(args):
    logging.info("Velo Deploy Action")
    gv = gitversion.Gitversion()

    if args.mode == "VERSION":
        version = gv.generate_version()
        os.system(f'echo "::set-output name=version::{version}"')

    elif args.mode == "DEPLOY":
        octopus_cli_server = os.getenv("INPUT_OCTOPUS_CLI_SERVER")
        octopus_cli_api_key = os.getenv("INPUT_OCTOPUS_CLI_API_KEY")

        # Use gcloud auth for authenticating when running on in dev mode.
        if args.environment == "dev":
            logging.debug("Authentication to GCP using Cloud SDK default credentials since environment is dev.")
            try:
                credentials, _ = google.auth.default()
            except google.auth.exceptions.DefaultCredentialsError as e:
                logging.error("No credentials were found, or the credentials found were invalid.")
        else:
            google_service_account_key = os.getenv("INPUT_SERVICE_ACCOUNT_KEY")
            if google_service_account_key is not None:
                try:
                    base64_bytes = google_service_account_key.encode("ascii")
                    message_bytes = base64.b64decode(base64_bytes)
                    message = message_bytes.decode("ascii")
                    google_service_account_key_json = json.loads(message)
                    _ = service_account.Credentials.from_service_account_info(google_service_account_key_json)
                except binascii.Error:
                    logging.error("INPUT_SERVICE_ACCOUNT_KEY was not base64 encoded")
            else:
                logging.warning("Env var INPUT_SERVICE_ACCOUNT_KEY was not present")

        version = gv.generate_version()
        octo = octopus.Octopus(apiKey=octopus_cli_api_key, server=octopus_cli_server)

        assert Path(args.deploy_folder_path).is_dir()
        path = str(args.deploy_folder_path)
        utils.upload_from_directory(path, args.velo_artifact_bucket, f"{args.project}/{version}")

        octo.creatRelease(args.project, version)

        octo.deployRelease(args.project, version, args.environment)


if __name__ == "__main__":
    args = parse_args()
    action(args)
