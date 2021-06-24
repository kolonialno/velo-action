import sys
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

from velo_action import proc_utils, octopus, github, gcp, gitversion


BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(name="action")


def parse_args():
    parser = envargparse.EnvArgParser(prog="Velo Action")

    parser.add_argument("--create_release", env_var="INPUT_CREATE_RELEASE", type=str, required=False)
    parser.add_argument("--deploy", env_var="INPUT_DEPLOY", type=str, required=False)
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", type=str, required=False)

    # workdir used by Github Actions.
    # https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions#workdir
    parser.add_argument("--github_workspace", env_var="GITHUB_WORKSPACE", type=str, required=False)

    if os.getenv("INPUT_CREATE_RELEASE") or os.getenv("INPUT_DEPLOY"):
        parser.add_argument("--octopus_project", env_var="INPUT_OCTOPUS_PROJECT", type=str, required=True)
        parser.add_argument("--octopus_tenants", env_var="INPUT_OCTOPUS_TENANTS", type=str, required=False)
        parser.add_argument("--octopus_cli_server", env_var="INPUT_OCTOPUS_CLI_SERVER", type=str, required=True)
        parser.add_argument("--octopus_cli_api_key", env_var="INPUT_OCTOPUS_CLI_API_KEY", type=str, required=True)
        parser.add_argument("--service_account_key", env_var="INPUT_SERVICE_ACCOUNT_KEY", type=str, required=True)
        parser.add_argument("--velo_artifact_bucket", env_var="INPUT_VELO_ARTIFACTS_BUCKET_NAME", type=str, required=True)
        parser.add_argument("--environment", env_var="INPUT_ENVIRONMENT", type=str, required=False)

    args = parser.parse_args()

    valid_envs = ["PROD", "STAGING"]
    if str(args.environment).upper() not in valid_envs:
        raise Exception(f"Environment must be one of {valid_envs}, not {args.environment} ")

    args.octopus_tenants = args.octopus_tenants.split(",")

    log_levels = ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]
    if args.log_level not in log_levels:
        raise Exception(f"INPUT_PYTHON_LOGGING_LEVEL must be one of {log_levels} got '{args.log_level}'")

    args.github_workspace = Path(args.github_workspace)

    logger.info(f"Settings log level to {args.log_level}")
    logging.basicConfig(level=args.log_level)

    return args


def action(args):
    logger.info("Velo Deploy Action")
    logger.info(f"Repo root path is {args.github_workspace}")

    gv = gitversion.Gitversion()
    version = gv.generate_version(path=args.github_workspace)

    github.actions_output("version", version)

    if args.create_release:

        deploy_folder = args.github_workspace / ".deploy"
        if not Path(deploy_folder).is_dir():
            raise Exception("Did not find a '.deploy' folder in repo root.")

        version = gv.generate_version(path=args.github_workspace)
        logger.info(f"Gitversion={version}")

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

        octo.list_tenants()

        logger.info(f"Uploading artifacts to {args.velo_artifact_bucket}")
        gcp.upload_from_directory(client, deploy_folder, args.velo_artifact_bucket, f"{args.octopus_project}/{version}")

        logger.info(f"Creating a release for project '{args.octopus_project}' with version '{version}'")
        octo.create_release(version=version, project=args.octopus_project)

    if args.deploy:
        logger.info(f"Deploying release for project '{args.octopus_project}' with version '{version}'")

        octo.deploy_release(version=version, environment=args.environment, project=args.octopus_project, tenants=args.octopus_tenants)


if __name__ == "__main__":
    args = parse_args()
    action(args)
