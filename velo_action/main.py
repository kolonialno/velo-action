import os
import sys
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from velo_action import gcp, github, tracing_helpers
from velo_action.octopus.client import OctopusClient
from velo_action.octopus.deployment import Deployment
from velo_action.octopus.release import Release
from velo_action.release_note import create_release_notes
from velo_action.settings import (
    VELO_TRACE_ID_NAME,
    ActionInputs,
    GithubSettings,
    resolve_workspace,
)
from velo_action.utils import find_matching_version, read_app_spec
from velo_action.version import generate_version

BASE_DIR = Path(__file__).resolve().parent.parent

VELO_DEPLOY_FOLDER_NAME = ".deploy"
VELO_PROJECT_NAME = "nube-velo-prod"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} {message}"


def action(
    args: ActionInputs,
    github_settings: GithubSettings,
):  # pylint: disable=too-many-branches

    try:
        trace_id = tracing_helpers.start_trace(args.service_account_key)  # type: ignore
    except Exception as err:  # pylint: disable=broad-except
        trace_id = None
        logger.exception("Starting trace failed", exc_info=err)

    logger.info("Starting velo-action")

    # Read secrets early to fail fast
    gcloud = gcp.GCP(args.service_account_key)

    octopus_server = gcloud.lookup_data(args.octopus_server_secret, VELO_PROJECT_NAME)
    octopus_api_key = gcloud.lookup_data(args.octopus_api_key_secret, VELO_PROJECT_NAME)
    velo_artifact_bucket = gcloud.lookup_data(
        args.velo_artifact_bucket_secret, VELO_PROJECT_NAME
    )

    os.chdir(args.workspace)  # type: ignore

    logger.info(f"Deploy to environments: {args.deploy_to_environments}")
    if args.tenants:
        logger.info(f"Tenants: {args.tenants}")

    logger.info(f"Create release: {args.create_release}")
    logger.info(f"Version: {args.version}")

    github.actions_output("version", args.version)

    if not args.create_release and not args.deploy_to_environments:
        logger.warning("Nothing to do. Exciting now.")
        return

    deploy_folder = Path.joinpath(Path(args.workspace), VELO_DEPLOY_FOLDER_NAME)

    if not deploy_folder.is_dir():
        raise Exception(
            f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in '{args.workspace}'."
        )

    octo = OctopusClient(server=octopus_server, api_key=octopus_api_key)

    if args.create_release:
        velo_settings = read_app_spec(deploy_folder)

        logger.info(
            f"Uploading artifacts to '{velo_artifact_bucket}/{args.project}/{args.version}'"
        )

        gcloud.upload_from_directory(
            deploy_folder,
            velo_artifact_bucket,
            f"{velo_settings.project}/{args.version}",
        )

        logger.info(
            f"Creating a release for project '{velo_settings.project}' with version '{args.version}'"
        )

        release = Release(client=octo)

        velo_bootstrapper_versions = release.list_available_deploy_packages()
        matching_velo_version = find_matching_version(
            velo_bootstrapper_versions, velo_settings.verison
        )

        release.create(
            project_name=args.project,
            version=args.version,
            notes=create_release_notes(github_settings),
            velo_version=matching_velo_version,
        )

    if args.deploy_to_environments:
        deploy_vars = {}
        if trace_id:
            deploy_vars[VELO_TRACE_ID_NAME] = trace_id

        tenants = args.tenants or [None]  # type: ignore

        for env in args.deploy_to_environments:
            for ten in tenants:
                log = f"Deploying project '{velo_settings.project}' version '{args.version}' to '{env}' "
                if ten:
                    log += f"for tenant '{ten}'"
                logger.info(log)

                deploy = Deployment(
                    project_name=velo_settings.project,
                    version=args.version,
                    client=octo,
                )

                deploy.create(
                    env_name=env,
                    tenant=ten,
                    wait_seconds=args.wait_for_success_seconds,
                    variables=deploy_vars,
                )
    logger.info("Done")


if __name__ == "__main__":
    try:
        gh = GithubSettings()
        s = ActionInputs()

        s.workspace = resolve_workspace(s, gh)

    except ValidationError as err:
        logger.error(err)
        sys.exit(1)

    logger.add(sys.stdout, level=s.log_level, format=LOG_FORMAT)
    action(s, gh)
