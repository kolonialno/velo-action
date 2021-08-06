import json
import logging
import os
from pathlib import Path

from velo_action import octopus, github, gcp, gitversion
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

    logger.info("Starting Velo-action")
    if input_args.service_account_key:
        logger.info(f"service account: {input_args.service_account_key[:15]}")
    logger.info(f"deploy_to_environments: {input_args.deploy_to_environments}")
    logger.info(f"create_release: {input_args.create_release}")

    if input_args.version is None:
        gv = gitversion.Gitversion(path=Path(input_args.workspace))
        version = gv.generate_version()
    else:
        version = input_args.version

    logger.info(f"Version: {version}")
    github.actions_output("version", version)

    if input_args.create_release or input_args.deploy_to_environments:
        deploy_folder = Path.joinpath(Path(input_args.workspace), "VELO_DEPLOY_FOLDER_NAME")
        if not Path(deploy_folder).is_dir():
            raise Exception(f"Did not find a '{VELO_DEPLOY_FOLDER_NAME}' folder in '{input_args.workspace}'.")

        if not input_args.service_account_key:
            raise ValueError("gcp service account key not specified")
        if not input_args.octopus_cli_server_secret:
            raise ValueError("octopus server secret not specified")
        if not input_args.octopus_cli_api_key_secret:
            raise ValueError("octopus api key secret not specified")
        if not input_args.velo_artifact_bucket_secret:
            raise ValueError("artifact bucket secret not specified")
        if not input_args.project:
            raise ValueError("project not specified")

        g = gcp.Gcp(input_args.service_account_key)
        octopus_cli_server = g.lookup_data(input_args.octopus_cli_server_secret, VELO_PROJECT_NAME)
        octopus_cli_api_key = g.lookup_data(input_args.octopus_cli_api_key_secret, VELO_PROJECT_NAME)
        velo_artifact_bucket = g.lookup_data(input_args.velo_artifact_bucket_secret, VELO_PROJECT_NAME)

        octo = octopus.Octopus(api_key=octopus_cli_api_key, server=octopus_cli_server)

        if input_args.create_release:
            logger.info(f"Uploading artifacts to '{velo_artifact_bucket}'")
            g.upload_from_directory(deploy_folder, velo_artifact_bucket, f"{input_args.project}/{version}")

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

            logger.info(f"Creating a release for project '{input_args.project}' with version '{version}'")
            octo.create_release(version=version, project=input_args.project, release_notes=release_notes)

        if input_args.deploy_to_environments:
            for env in input_args.deploy_to_environments:
                octo.deploy_release(
                    version=version,
                    environment=env,
                    project=input_args.project,
                    tenants=input_args.tenants,
                    progress=input_args.progress,
                    wait_for_deployment=input_args.wait_for_deployment,
                )


if __name__ == "__main__":
    s = Settings()
    action(s)
