import os
import sys
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from velo_action import gcp, github
from velo_action.octopus.client import OctopusClient
from velo_action.octopus.deployment import Deployment
from velo_action.octopus.release import Release
from velo_action.settings import (
    VELO_TRACE_ID_NAME,
    ActionInputs,
    GithubSettings,
    resolve_workspace,
)
from velo_action.tracing_helpers import (
    construct_github_action_trace,
    init_tracer,
    print_trace_link,
    stringify_span,
)
from velo_action.utils import read_velo_settings

BASE_DIR = Path(__file__).resolve().parent.parent

VELO_DEPLOY_FOLDER_NAME = ".deploy"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} {message}"


def action(
    args: ActionInputs,
    github_settings: GithubSettings,
) -> None:  # pylint: disable=too-many-branches

    try:
        init_trace = False
        tracer = init_tracer(args.service_account_key, service="velo-action")
        span = construct_github_action_trace(
            tracer, args.token, args.preceding_run_ids, github_settings=github_settings
        )
        trace_id = stringify_span(span)
        init_trace = True
    except Exception as error:  # pylint: disable=broad-except
        trace_id = None
        logger.warning(f"Starting trace failed: {error}", exc_info=error)

    deploy_folder = Path.joinpath(Path(args.workspace), VELO_DEPLOY_FOLDER_NAME)  # type: ignore
    if not deploy_folder.is_dir():
        sys.exit(
            f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in '{args.workspace}'."
        )

    # Read secrets early to fail fast
    gcloud = gcp.GCP(
        project=args.velo_project, service_account_key=args.service_account_key
    )

    octopus_server = gcloud.lookup_data(args.octopus_server_secret, args.velo_project)
    octopus_api_key = gcloud.lookup_data(args.octopus_api_key_secret, args.velo_project)
    velo_artifact_bucket = gcloud.lookup_data(
        args.velo_artifact_bucket_secret, args.velo_project
    )
    os.chdir(args.workspace)  # type: ignore

    if not args.create_release and not args.deploy_to_environments:
        logger.warning("Nothing to do. Exciting now.")
        return None

    octo = OctopusClient(server=octopus_server, api_key=octopus_api_key)
    if args.create_release:
        release = Release(client=octo)
        velo_settings = read_velo_settings(deploy_folder)

        if release.exists(
            project_name=velo_settings.project, version=args.version, client=octo
        ):
            logger.info(
                f"Release '{args.version}' already exists at "
                f"'{release.client.baseurl}/app#/Spaces-1/projects/"
                f"{velo_settings.project}/deployments/releases/{args.version}'. "
                "If you want to recreate this release, please delete it first in Octopus Deploy."
                "Project -> Releases -> <Select Release> -> : menu in top right corner -> Delete. "
                "Skipping..."
            )
            return None

        files = gcloud.upload_from_directory(
            path=deploy_folder,
            dest_bucket_name=velo_artifact_bucket,
            dest_blob_name=f"{velo_settings.project}/{args.version}",
        )

        logger.info(
            f"Uploaded {len(files)} release files to "
            f"'https://console.cloud.google.com/storage/browser/{velo_artifact_bucket}/{velo_settings.project}/{args.version}'"
        )

        logger.info(
            f"Creating a release in Octopus Deploy for project '{velo_settings.project}' with version '{args.version}'"
        )
        release.create(
            project_name=velo_settings.project,
            project_version=args.version,
            github_settings=github_settings,
        )
        logger.info(
            f"See {release.client.baseurl}/app#/Spaces-1/projects/{velo_settings.project}/deployments/releases/{args.version}"
        )

    if args.deploy_to_environments:
        logger.info(f"Deploy to environments: {args.deploy_to_environments}")
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

    if init_trace:
        print_trace_link(span)

    # Set outputs in environment to be used by other
    # steps in the Github Action Workflows
    logger.info("Github actions outputs:")
    github.actions_output("version", args.version)

    logger.info("Done")
    return None


if __name__ == "__main__":
    try:
        gh = GithubSettings()
        s = ActionInputs()

        s.workspace = resolve_workspace(s, gh)

    except ValidationError as err:
        # Logger is not instantiated yet
        print(err)
        sys.exit(1)

    logger.add(sys.stdout, level=s.log_level, format=LOG_FORMAT)
    action(s, gh)
