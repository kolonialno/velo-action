import logging
import os

import requests

logger = logging.getLogger(name="github")


def actions_output(key, value):
    logger.debug("Github actions output:")
    os.system(f'echo "::set-output name={key}::{value}"')


def request_github_workflow_data():
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_ids = os.environ.get("PRECEDING_RUN_IDS", "")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs"
    current_workflow_url = f"{base_url}/{gh_run_id}/jobs"

    r = requests.get(current_workflow_url, headers=github_headers)
    r.raise_for_status()
    total_action_dict = {os.environ["GITHUB_WORKFLOW"]: r.json()}

    if gh_preceding_run_ids:
        for gh_preceding_run_id in gh_preceding_run_ids.split(","):
            workflow_run_url = f"{base_url}/{gh_preceding_run_id}"

            r = requests.get(workflow_run_url, headers=github_headers)
            r.raise_for_status()
            preceding_wf_name = r.json()["name"]

            r = requests.get(f"{workflow_run_url}/jobs", headers=github_headers)
            r.raise_for_status()
            total_action_dict[preceding_wf_name] = r.json()
    return total_action_dict


def request_commit_info(commit_sha: str) -> dict:
    if "TOKEN" not in os.environ:
        return {"commit": {"message": "Unknown"}}
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}
    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]

    r = requests.get(
        f"{gh_api_url}/repos/{gh_repo}/commits/{commit_sha}", headers=github_headers
    )
    r.raise_for_status()
    return r.json()
