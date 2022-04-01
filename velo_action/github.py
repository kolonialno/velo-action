import os

import requests


def actions_output(key, value):
    """Output variables such that they can be used in GitHub Actions."""
    os.system(f'echo "::set-output name={key}::{value}"')


def request_github_workflow_data():
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_ids = os.environ.get("PRECEDING_RUN_IDS", "")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs"
    current_workflow_url = f"{base_url}/{gh_run_id}/jobs"

    req = requests.get(current_workflow_url, headers=github_headers)
    req.raise_for_status()
    total_action_dict = {os.environ["GITHUB_WORKFLOW"]: req.json()}

    if gh_preceding_run_ids:
        for gh_preceding_run_id in gh_preceding_run_ids.split(","):
            workflow_run_url = f"{base_url}/{gh_preceding_run_id}"

            req = requests.get(workflow_run_url, headers=github_headers)
            req.raise_for_status()
            preceding_wf_name = req.json()["name"]

            req = requests.get(f"{workflow_run_url}/jobs", headers=github_headers)
            req.raise_for_status()
            total_action_dict[preceding_wf_name] = req.json()
    return total_action_dict


def request_commit_info(commit_sha: str) -> dict:
    if "TOKEN" not in os.environ:
        return {"commit": {"message": "Unknown"}}
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}
    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]

    req = requests.get(
        f"{gh_api_url}/repos/{gh_repo}/commits/{commit_sha}", headers=github_headers
    )
    req.raise_for_status()
    return req.json()
