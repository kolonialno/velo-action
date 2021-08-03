import os
import logging
import json
from pathlib import Path
import envargparse
from velo_action import octopus, gcp, gitversion
import github
from github import Github, Workflow

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(name="action")

VELO_DEPLOY_FOLDER_NAME = ".deploy"
VELO_PROJECT_NAME = "nube-velo-prod"


def valid_path(arg):
    try:
        path = Path(arg)
        return path
    except:
        raise Exception(f"{arg} is an invalid path.")


def parse_args():
    """[Parse input arguments]

    The Github action only provides input arguments to the container as environment variables,
    with INPUT_ prefiex on the argument name.

    This means every argument is parsed as a string.
    To replicate this behaviour when debugging locally all default values is also set to the string 'None'.

    Every githu action input, specified in action.yml, is also set do default string 'None'.
    Otherview you would get an env var in the container with no value, causing an error.

    Returns:
        [args]: [Parsed input arguments]
    """
    parser = envargparse.EnvArgParser(prog="Velo-action")

    parser.add_argument(
        "--version",
        env_var="INPUT_VERSION",
        type=str,
        default="None",
        required=False,
        help="Version used to generate release and tag image. This will overwrite the automatically generated gitversion if spesified.",
    )
    parser.add_argument("--log_level", env_var="INPUT_PYTHON_LOGGING_LEVEL", type=str, required=False, choices=["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"])
    parser.add_argument("--create_release", env_var="INPUT_CREATE_RELEASE", type=str, required=False, choices=["True", "False"], help="If true, create a release in Octopus deploy")
    parser.add_argument(
        "--github_workspace",
        env_var="GITHUB_WORKSPACE",
        type=valid_path,
        required=False,
        help="Path to the root folder in the repo to deploy. Must contain a .git folder for gitversion to work.",
    )  # workdir used by Github Actions,https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions#workdir
    parser.add_argument("--project", env_var="INPUT_PROJECT", type=str, default="None", required=False, help="Name of the project in Octopus Deploy to deploy to.")
    parser.add_argument(
        "--tenants",
        env_var="INPUT_TENANTS",
        type=str,
        default="None",
        required=False,
        help="Name of the tenants to deploy to. String seperated by a comma. Example: 'tenant1,tenant2'.",
    )
    parser.add_argument(
        "--deploy_to_environments",
        env_var="INPUT_DEPLOY_TO_ENVIRONMENTS",
        type=str,
        default="None",
        required=False,
        help="If specified trigger a deployment to the environment. Can be multiple values seperated by a comma. Example 'staging,prod'.",
    )
    parser.add_argument(
        "--service_account_key",
        env_var="INPUT_SERVICE_ACCOUNT_KEY",
        type=str,
        default="None",
        required=False,
        help="A Google Service Account key, either base64 encoded or as json.",
    )
    parser.add_argument("--octopus_cli_server_secret", env_var="INPUT_OCTOPUS_CLI_SERVER_SECRET", type=str, default="None", required=False)
    parser.add_argument("--octopus_cli_api_key_secret", env_var="INPUT_OCTOPUS_CLI_API_KEY_SECRET", type=str, default="None", required=False)
    parser.add_argument("--velo_artifact_bucket_secret", env_var="INPUT_VELO_ARTIFACT_BUCKET_SECRET", type=str, default="None", required=False)

    args = parser.parse_args()

    args.github_workspace = valid_path(args.github_workspace)
    logging.basicConfig(level=args.log_level)

    if args.version == "None":
        args.version = None

    if args.create_release == "True":
        assert args.project != "None", "project input argument must be specified."
        args.create_release = True
    else:
        args.create_release = False

    if args.deploy_to_environments != "None":
        args.deploy_to_environments = args.deploy_to_environments.split(",")
        args.create_release = True
        assert args.service_account_key != "None", "service_account_key input argument must be specified."
    else:
        args.deploy_to_environments = None

    if args.tenants != "None":
        args.tenants = args.tenants.split(",")
    else:
        args.tenants = []
    return args


def actions_output(key, value):
    logger.info(f"Setting Github actions output: {key}={value}")
    os.system(f'echo "::set-output name={key}::{value}"')


def action(args):
    logger.info("Starting Velo-action")
    logger.info(f"Repo root path is '{args.github_workspace}'")

    g = Github("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")
    w = Workflow()
    # w.create_dispatch(ref='master')

    if args.version is None:
        version = args.version
        logger.info(f"Manually overriding version to {version}")
        gv = gitversion.Gitversion(repo_path=args.github_workspace)
        version = gv.generate_version()
        logger.info(f"Gitversion={version}")
    else:
        version = args.version
        logger.info(f"Manually overriding version to {version}")

    actions_output("version", version)

    if args.create_release or args.deploy_to_environments:

        deploy_folder = args.github_workspace / VELO_DEPLOY_FOLDER_NAME
        if not Path(deploy_folder).is_dir():
            raise Exception(f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in repo root: {deploy_folder}.")

        g = gcp.Gcp(args.service_account_key)
        octopus_cli_server = g.lookup_data(args.octopus_cli_server_secret, VELO_PROJECT_NAME)
        octopus_cli_api_key = g.lookup_data(args.octopus_cli_api_key_secret, VELO_PROJECT_NAME)
        velo_artifact_bucket = g.lookup_data(args.velo_artifact_bucket_secret, VELO_PROJECT_NAME)

        octo = octopus.Octopus(api_key=octopus_cli_api_key, server=octopus_cli_server)

    if args.create_release:
        logger.info(f"Uploading artifacts to {velo_artifact_bucket}")
        g.upload_from_directory(deploy_folder, velo_artifact_bucket, f"{args.project}/{version}")

        commit_id = os.getenv("GITHUB_SHA")
        branch_name = os.getenv("GITHUB_REF")
        assert commit_id is not None, "The environment variable GITHUB_SHA must be present."
        assert len(commit_id) == 40, "The environment variable GITHUB_SHA must contain the full git commit hash with 40 characters."
        assert branch_name is not None, "The environment variable GITHUB_REF must be present, and contain the git branch name."
        release_notes = f'{json.dumps({"commit_id": commit_id, "branch_name": branch_name})}'

        logger.info(f"Creating a release for project '{args.project}' with version '{version}'")
        octo.create_release(version=version, project=args.project, release_notes=release_notes)

    if args.deploy_to_environments:

        for env in args.deploy_to_environments:
            logger.info(f"Deploying '{args.project}' version '{version}' to '{env}'")
            octo.deploy_release(version=version, environment=env, project=args.project, tenants=args.tenants)


if __name__ == "__main__":
    args = parse_args()
    action(args)
