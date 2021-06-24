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


def valid_path(arg):
    try:
        path = Path(arg)
        return path
    except:
        raise Exception(f"{arg} is an invalid path.")


def parse_args():
    parser = envargparse.EnvArgParser(prog="Velo Action")

    parser.add_argument(
        "--create_release", env_var="INPUT_CREATE_RELEASE", type=str, default=False, required=False, choices=["True", "False"], help="If true, create a release in Octopus deploy"
    )
    parser.add_argument("--deploy", env_var="INPUT_DEPLOY", type=str, required=False, default=False, choices=["True", "False"], help="If true, deploy a relese Octopus deploy")
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", type=str, required=False, choices=["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"])

    # workdir used by Github Actions.
    # https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions#workdir
    parser.add_argument(
        "--github_workspace", env_var="GITHUB_WORKSPACE", type=valid_path, required=False, help="Path to the root folder in the repo to deploy. Must contain a .git folder."
    )

    args = parser.parse_args()
    args.github_workspace = valid_path(args.github_workspace)
    logging.basicConfig(level=args.log_level)

    if args.create_release or args.deploy:
        parser.add_argument("--octopus_project", env_var="INPUT_OCTOPUS_PROJECT", type=str, required=True, help="Name of the project in Octopus Deploy to target.")
        parser.add_argument("--octopus_tenants", env_var="INPUT_OCTOPUS_TENANTS", type=str, required=False, help="Name of the tenants to deploy to, seperated by a comma.")
        parser.add_argument("--octopus_cli_server", env_var="INPUT_OCTOPUS_CLI_SERVER", type=str, required=True)
        parser.add_argument("--octopus_cli_api_key", env_var="INPUT_OCTOPUS_CLI_API_KEY", type=str, required=True)
        parser.add_argument("--service_account_key", env_var="INPUT_SERVICE_ACCOUNT_KEY", type=str, required=True)
        parser.add_argument(
            "--velo_artifact_bucket", env_var="INPUT_VELO_ARTIFACTS_BUCKET_NAME", type=str, required=True, help="Name of the bucket where Velo stores deploy artifacts."
        )
        parser.add_argument(
            "--environments", env_var="INPUT_ENVIRONMENTS", type=str, required=False, choices=["prod", "staging"], help="Name of the environments to deploy to, seperated by comma."
        )

        args = parser.parse_args()

        args.octopus_tenants = args.octopus_tenants.split(",")

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

        octo.deploy_release(version=version, environments=args.environments, project=args.octopus_project, tenants=args.octopus_tenants)


if __name__ == "__main__":
    args = parse_args()
    action(args)
