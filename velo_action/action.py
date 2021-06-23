import sys

print(sys.path)
import os
import os.path
import logging
from pathlib import Path
import json
import base64
import binascii
import envargparse
from google.oauth2 import service_account
from google.cloud import storage

from velo_action import octopus, github, gcp, gitversion

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(name="action")


def parse_args():
    parser = envargparse.EnvArgParser(prog="Velo Action")

    parser.add_argument("--mode", "-m", env_var="INPUT_MODE", default="VERSION", type=str, required=False)
    parser.add_argument("--environment", env_var="ENVIRONMENT", default="staging", type=str, required=False)
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", type=str, required=False)

    # workdir used by Github Actions.
    # https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions#workdir
    parser.add_argument("--github_workspace", env_var="GITHUB_WORKSPACE", type=str, required=False)

    if os.getenv("INPUT_MODE") == "DEPLOY":
        parser.add_argument("--project", env_var="INPUT_PROJECT", type=str, required=True)
        parser.add_argument("--octopus_cli_server", env_var="INPUT_OCTOPUS_CLI_SERVER", type=str, required=True)
        parser.add_argument("--octopus_cli_api_key", env_var="INPUT_OCTOPUS_CLI_API_KEY", type=str, required=True)
        parser.add_argument("--service_account_key", env_var="INPUT_SERVICE_ACCOUNT_KEY", type=str, required=True)
        parser.add_argument("--velo_artifact_bucket", env_var="INPUT_VELO_ARTIFACTS_BUCKET_NAME", type=str, required=True)

    args = parser.parse_args()
    args.mode = args.mode.upper()

    log_levels = ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]
    if args.log_level not in log_levels:
        raise Exception(f"INPUT_PYTHON_LOGGING_LEVEL must be one of {log_levels} got '{args.log_level}'")

    logger.info(f"Settings log level to {args.log_level}")
    logging.basicConfig(level=args.log_level)

    return args


def action(args):
    logger.info("Velo Deploy Action")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Repo root path is {args.github_workspace}")

    gv = gitversion.Gitversion()
    version = gv.generate_version(path=args.github_workspace)

    github.actions_output("version", version)

    if args.mode == "DEPLOY":

        deploy_folder = str(args.github_workspace + "/.deploy")
        if not Path(deploy_folder).is_dir():
            raise Exception("Did not find a '.deploy' folder in repo root.")

        version = gv.generate_version(path=args.github_workspace)

        octo = octopus.Octopus(apiKey=args.octopus_cli_api_key, server=args.octopus_cli_server)

        try:
            google_service_account_key_json = json.loads(base64.b64decode(args.service_account_key.encode("ascii")).decode("ascii"))
        except binascii.Error:
            logger.debug("INPUT_SERVICE_ACCOUNT_KEY was not base64 encoded")

        credentials = service_account.Credentials.from_service_account_info(google_service_account_key_json)

        scoped_credentials = credentials.with_scopes(["https://www.googleapis.com/auth/cloud-platform"])

        try:
            client = storage.Client(credentials=scoped_credentials)
        except Exception as e:
            logger.error(exc_info=e)
            raise

        logger.info(f"Uploading artifacts to {args.velo_artifact_bucket}")
        gcp.upload_from_directory(client, deploy_folder, args.velo_artifact_bucket, f"{args.project}/{version}")

        logger.info(f"Creating a release for project '{args.project}' with version '{version}'")
        octo.creatRelease(args.project, version)

        logger.info(f"Deploying release for project '{args.project}' with version '{version}'")
        octo.deployRelease(args.project, version, args.environment)


if __name__ == "__main__":
    args = parse_args()
    action(args)
