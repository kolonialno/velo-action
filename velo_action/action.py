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
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", default=logging.INFO, type=str, required=False)

    # workdir used by Github Actions.
    # https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions#workdir
    parser.add_argument("--github_workspace", env_var="GITHUB_WORKSPACE", default="/github/workspace", type=str, required=False)

    if os.getenv("INPUT_MODE") == "DEPLOY":
        parser.add_argument("--octopus_cli_server", env_var="INPUT_OCTOPUS_CLI_SERVER", type=str, required=True)
        parser.add_argument("--octopus_cli_api_key", env_var="INPUT_OCTOPUS_CLI_API_KEY", type=str, required=True)
        parser.add_argument("--service_account_key", env_var="INPUT_SERVICE_ACCOUNT_KEY", type=str, required=True)
        parser.add_argument("--project", env_var="INPUT_PROJECT", type=str, required=True)

        parser.add_argument("--velo_artifact_bucket", env_var="VELO_ARTIFACT_BUCKET", default="nube-velo-prod-deploy-artifacts", type=str, required=False)

    args = parser.parse_args()
    args.mode = args.mode.upper()

    if args.log_level not in ["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"]:
        logging.basicConfig(level=logging.INFO)
    return args


def action(args):
    logging.info("Velo Deploy Action")
    gv = gitversion.Gitversion()

    logging.info(f"Mode: {args.mode}")
    if args.mode == "VERSION":
        version = gv.generate_version(path=args.github_workspace)
        utils.github_action_output("version", version)

    elif args.mode == "DEPLOY":
        octopus_cli_server = os.getenv("INPUT_OCTOPUS_CLI_SERVER")
        octopus_cli_api_key = os.getenv("INPUT_OCTOPUS_CLI_API_KEY")

        path = str(args.github_workspace + "/.deploy")
        logging.info(f"Repo root path is {args.github_workspace}")
        logging.info(f"Looging for a .deploy folder in {path}...")
        assert Path(path).is_dir()

        version = gv.generate_version(path=args.github_workspace)

        octo = octopus.Octopus(apiKey=octopus_cli_api_key, server=octopus_cli_server)

        google_service_account_key = os.getenv("INPUT_SERVICE_ACCOUNT_KEY")
        if google_service_account_key is None:
            logging.error("Please set a Google Service Account Key.")
            sys.exit(1)

        try:
            google_service_account_key_json = json.loads(base64.b64decode(google_service_account_key.encode("ascii")).decode("ascii"))
        except binascii.Error:
            logging.warning("INPUT_SERVICE_ACCOUNT_KEY was not base64 encoded")

        logging.info("Authenticating using Google Service Account Key")
        # credentials = utils.authenticate_gcp(google_service_account_key_json)

        logging.info(f"Uploading artifacts to {args.velo_artifact_bucket}")
        utils.upload_from_directory(path, args.velo_artifact_bucket, f"{args.project}/{version}")

        logging.info(f"Creating a release for project {args.project} with version {version}")
        octo.creatRelease(args.project, version)

        logging.info(f"Deploying release for project {args.project} with version {version}")
        octo.deployRelease(args.project, version, args.environment)


if __name__ == "__main__":
    args = parse_args()
    action(args)
