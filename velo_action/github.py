import os
import logging

import requests

logger = logging.getLogger(name="github")


def actions_output(key, value):
    logger.debug("Github actions output:")
    os.system(f'echo "::set-output name={key}::{value}"')


def request_github_wf_data():
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_id = os.environ.get("PRECEDING_RUN_ID", "")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs"
    current_wf_url = f"{base_url}/{gh_run_id}/jobs"
    preceding_wf_url = f"{base_url}/{gh_preceding_run_id}/jobs"

    r = requests.get(current_wf_url, headers=github_headers)
    r.raise_for_status()
    actual_wf_jobs = r.json()

    if gh_preceding_run_id:
        r = requests.get(preceding_wf_url, headers=github_headers)
        r.raise_for_status()
        preceding_wf_jobs = r.json()

        preceding_wf_name = (
            n if (n := os.environ.get("PRECEDING_RUN_NAME", "")) else "CI"
        )
        total_action_dict = {
            preceding_wf_name: preceding_wf_jobs,
            os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs,
        }
    else:
        total_action_dict = {os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs}
    return total_action_dict


def request_commit_info(commit_sha):
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}
    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]

    r = requests.get(
        f"{gh_api_url}/repos/{gh_repo}/commits/{commit_sha}", headers=github_headers
    )
    r.raise_for_status()
    commit_info = r.json()
    return commit_info["commit"]
