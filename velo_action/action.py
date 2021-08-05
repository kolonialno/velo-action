import os
import logging
import json
from pathlib import Path
import envargparse
from distutils.util import strtobool
from velo_action import octopus, github, gcp, gitversion

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(name="action")

VELO_DEPLOY_FOLDER_NAME = ".deploy"
VELO_PROJECT_NAME = "nube-velo-prod"

GITHUB_WORKSPACE = (os.getenv("GITHUB_WORKSPACE"),)


def valid_path(arg):
    path = Path(arg)
    if not path.is_dir():
        raise ValueError(f"path {path} is not a dir")
    return path


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
        default=None,
        required=False,
        help="Version used to generate release and tag image. \
              This will overwrite the automatically generated gitversion if spesified.",
    )
    parser.add_argument(
        "--log_level",
        env_var="INPUT_PYTHON_LOGGING_LEVEL",
        type=str,
        required=False,
        default="INFO",
        choices=["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"],
    )
    parser.add_argument(
        "--create_release",
        env_var="INPUT_CREATE_RELEASE",
        type=str,
        required=False,
        default="False",
        choices=["True", "False"],
        help="If true, create a release in Octopus deploy",
    )
    parser.add_argument(
        "--workspace",
        env_var="INPUT_WORKSPACE",
        required=False,
        help="Path to the root folder in the repo to deploy. \
              Must contain a .git folder for gitversion to work.",
    )
    parser.add_argument(
        "--project",
        env_var="INPUT_PROJECT",
        type=str,
        required=False,
        help="Name of the project in Octopus Deploy to deploy to.",
    )
    parser.add_argument(
        "--tenants",
        env_var="INPUT_TENANTS",
        type=str,
        required=False,
        help="Name of the tenants to deploy to. String seperated by a comma. Example: 'tenant1,tenant2'.",
    )
    parser.add_argument(
        "--deploy_to_environments",
        env_var="INPUT_DEPLOY_TO_ENVIRONMENTS",
        type=str,
        default=None,
        required=False,
        help="If specified trigger a deployment to the environment. \
              Can be multiple values seperated by a comma. Example 'staging,prod'.",
    )
    parser.add_argument(
        "--service_account_key",
        env_var="INPUT_SERVICE_ACCOUNT_KEY",
        type=str,
        required=False,
        help="A Google Service Account key, either base64 encoded or as json.",
    )
    parser.add_argument("--octopus_cli_server_secret", env_var="INPUT_OCTOPUS_CLI_SERVER_SECRET", type=str, required=False)
    parser.add_argument("--octopus_cli_api_key_secret", env_var="INPUT_OCTOPUS_CLI_API_KEY_SECRET", type=str, required=False)
    parser.add_argument("--velo_artifact_bucket_secret", env_var="INPUT_VELO_ARTIFACT_BUCKET_SECRET", type=str, required=False)
    parser.add_argument(
        "--progress",
        env_var="INPUT_PROGRESS",
        type=str,
        default="True",
        choices=["True", "False"],
        required=False,
        help="Show progress of the deployment.",
    )
    parser.add_argument(
        "--wait_for_deployment",
        env_var="INPUT_WAIT_FOR_DEPLOYMENT",
        type=str,
        default="True",
        required=False,
        choices=["True", "False"],
        help="Whether to wait synchronously for deployment in Octopus Deploy to finish.",
    )
    args = parser.parse_args()

    if not args.workspace:
        # EnvArgParser doesnt seem to accept variables in its "default" attribute, so this is the only way :-(
        args.workspace = os.getenv("GITHUB_WORKSPACE")
    args.workspace = valid_path(args.workspace)
    args.create_release = bool(strtobool(args.create_release))
    args.progress = bool(strtobool(args.progress))
    args.wait_for_deployment = bool(strtobool(args.wait_for_deployment))

    if args.deploy_to_environments:
        args.deploy_to_environments = args.deploy_to_environments.split(",")
    else:
        args.deploy_to_environments = []

    if args.tenants:
        args.tenants = args.tenants.split(",")
    else:
        args.tenants = []

    return args


def action(args):
    # TODO: These kind of logic verifiers (if this then that) should be separated into its own function to make it easily testable
    if args.deploy_to_environments:
        args.create_release = True

    logging.basicConfig(level=args.log_level)

    logger.info("Starting Velo-action")
    logger.info(f"service account: {args.service_account_key[:15]}")

    if args.version is None:
        gv = gitversion.Gitversion(path=args.workspace)
        version = gv.generate_version()
    else:
        version = args.version

    logger.info(f"Version: {version}")
    github.actions_output("version", version)

    if args.create_release or args.deploy_to_environments:
        deploy_folder = args.workspace / VELO_DEPLOY_FOLDER_NAME
        if not Path(deploy_folder).is_dir():
            raise Exception(f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in '{args.workspace}'.")

        if not args.service_account_key:
            raise ValueError("gcp service account key not specified")
        if not args.octopus_cli_server_secret:
            raise ValueError("octopus server secret not specified")
        if not args.octopus_cli_api_key_secret:
            raise ValueError("octopus api key secret not specified")
        if not args.velo_artifact_bucket_secret:
            raise ValueError("artifact bucket secret not specified")

        g = gcp.Gcp(args.service_account_key)
        octopus_cli_server = g.lookup_data(args.octopus_cli_server_secret, VELO_PROJECT_NAME)
        octopus_cli_api_key = g.lookup_data(args.octopus_cli_api_key_secret, VELO_PROJECT_NAME)
        velo_artifact_bucket = g.lookup_data(args.velo_artifact_bucket_secret, VELO_PROJECT_NAME)

        octo = octopus.Octopus(api_key=octopus_cli_api_key, server=octopus_cli_server)

        if args.create_release:
            logger.info(f"Uploading artifacts to '{velo_artifact_bucket}'")
            g.upload_from_directory(deploy_folder, velo_artifact_bucket, f"{args.project}/{version}")

            commit_id = os.getenv("GITHUB_SHA")
            branch_name = os.getenv("GITHUB_REF")
            assert commit_id is not None, "The environment variable GITHUB_SHA must be present."
            assert (
                len(commit_id) == 40
            ), "The environment variable GITHUB_SHA must contain the full git commit hash with 40 characters."
            assert (
                branch_name is not None
            ), "The environment variable GITHUB_REF must be present, and contain the git branch name."

            release_notes = f'{json.dumps({"commit_id": commit_id, "branch_name": branch_name})}'

            logger.info(f"Creating a release for project '{args.project}' with version '{version}'")
            octo.create_release(version=version, project=args.project, release_notes=release_notes)

        if args.deploy_to_environments:
            for env in args.deploy_to_environments:
                octo.deploy_release(
                    version=version,
                    environment=env,
                    project=args.project,
                    tenants=args.tenants,
                    progress=args.progress,
                    wait_for_deployment=args.wait_for_deployment,
                )


if __name__ == "__main__":
    args = parse_args()
    action(args)
