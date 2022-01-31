# type: ignore
import logging
import os
import sys
from pathlib import Path

import pydantic

from velo_action import gcp, github, proc_utils, tracing_helpers
from velo_action.octopus.client import OctopusClient
from velo_action.octopus.deployment import Deployment
from velo_action.octopus.release import Release
from velo_action.settings import Settings

BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(name="action")

VELO_DEPLOY_FOLDER_NAME = ".deploy"
VELO_PROJECT_NAME = "nube-velo-prod"


def action(input_args: Settings):
    # TODO: These kind of logic verifiers (if this then that) should be separated into its own function to make it easily testable
    if input_args.deploy_to_environments:
        input_args.create_release = True

    logging.basicConfig(level=input_args.log_level)

    try:
        trace_id = tracing_helpers.start_trace(input_args.service_account_key)
    except Exception as err:
        trace_id = None
        logger.exception("Starting trace failed", exc_info=err)

    logger.info("Starting velo-action")
    os.chdir(input_args.workspace)

    if input_args.service_account_key:
        logger.info(f"service account: {input_args.service_account_key[:15]}")
    logger.info(f"deploy_to_environments: {input_args.deploy_to_environments}")
    logger.info(f"tenants: {input_args.tenants}")
    logger.info(f"create_release: {input_args.create_release}")

    if input_args.version is None:
        version = proc_utils.execute_process(
            "git rev-parse --short HEAD",
            log_stdout=True,
            forward_stdout=False,
        )[0]
    else:
        version = input_args.version

    logger.info(f"Version: {version}")
    github.actions_output("version", version)

    if not input_args.create_release and not input_args.deploy_to_environments:
        logger.warning("Nothing to do. Exciting now.")
        return

    deploy_folder = Path.joinpath(Path(input_args.workspace), VELO_DEPLOY_FOLDER_NAME)

    if not deploy_folder.is_dir():
        raise Exception(
            f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in '{input_args.workspace}'."
        )

    if not input_args.octopus_server_secret:
        raise ValueError("octopus server secret not specified")
    if not input_args.octopus_api_key_secret:
        raise ValueError("octopus api key secret not specified")
    if not input_args.velo_artifact_bucket_secret:
        raise ValueError("artifact bucket secret not specified")
    if not input_args.project:
        raise ValueError("project not specified")
    if not input_args.service_account_key:
        logger.warning("gcp service account key not specified")

    gcloud = gcp.GCP(input_args.service_account_key)
    octopus_server = gcloud.lookup_data(
        input_args.octopus_server_secret, VELO_PROJECT_NAME
    )
    octopus_api_key = gcloud.lookup_data(
        input_args.octopus_api_key_secret, VELO_PROJECT_NAME
    )
    velo_artifact_bucket = gcloud.lookup_data(
        input_args.velo_artifact_bucket_secret, VELO_PROJECT_NAME
    )

    octo = OctopusClient(server=octopus_server, api_key=octopus_api_key)

    if input_args.create_release:
        logger.info(f"Uploading artifacts to '{velo_artifact_bucket}'")
        gcloud.upload_from_directory(
            deploy_folder, velo_artifact_bucket, f"{input_args.project}/{version}"
        )

        commit_id = os.getenv("GITHUB_SHA")
        branch_name = os.getenv("GITHUB_REF")
        assert (
            commit_id is not None
        ), "The environment variable GITHUB_SHA must be present."
        assert (
            len(commit_id) == 40
        ), "The environment variable GITHUB_SHA must contain the full git commit hash with 40 characters."
        assert (
            branch_name is not None
        ), "The environment variable GITHUB_REF must be present, and contain the git branch name."

        release_note_dict = {
            "commit_id": commit_id,
            "branch_name": branch_name,
            "commit_url": f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/commit/{commit_id}",
        }
        logger.info(
            f"Creating a release for project '{input_args.project}' with version '{version}'"
        )

        release = Release(client=octo)
        release.create(
            project_name=input_args.project, version=version, notes=release_note_dict
        )

    if input_args.deploy_to_environments:
        deploy_vars = {}
        if trace_id:
            deploy_vars["GithubSpanID"] = trace_id

        tenants = input_args.tenants or [None]

        for env in input_args.deploy_to_environments:
            for ten in tenants:
                log = f"Deploying project '{input_args.project}' version '{version}' to '{env}' "
                if ten:
                    log += f"for tenant '{ten}'"
                else:
                    log += "without tenant"
                logger.info(log)

                deploy = Deployment(
                    project_name=input_args.project,
                    version=version,
                    client=octo,
                )

                deploy.create(
                    env_name=env,
                    tenant=ten,
                    wait_seconds=input_args.wait_for_success_seconds,
                    variables=deploy_vars,
                )
    logger.info("Done")


if __name__ == "__main__":
    try:
        s = Settings()
    except pydantic.ValidationError as err:
        logger.error(err)
        sys.exit(1)
    action(s)
