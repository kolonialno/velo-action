import functools
import json
import logging
import os
import traceback
import urllib.parse
from datetime import datetime, timedelta
from time import sleep

import requests

logger = logging.getLogger(name="octopus")

_RELEASE_REGEX = r"^(|\+.*)$"
_MAX_WAIT_TIME = timedelta(seconds=10)


class Octopus:
    """
    Client to interact with the Octopus Deploy server
    """

    def __init__(self, server=None, api_key=None):
        self._baseurl = server
        self._headers = {"X-Octopus-ApiKey": f"{api_key}"}
        self._cached_environment_ids = {}
        self._verify_connection()

    def list_tenants(self):
        return self._get_request("/api/tenants/all")

    def list_releases(self, project_name):
        project_id = self.get_project_id(project_name)
        data = self._get_request(f"api/projects/{project_id}/releases")
        return data["Items"]

    def create_release(self, version, project_name, release_note_dict=None):
        project_id = self.get_project_id(project_name)
        if self._does_release_exist(project_id, version):
            logger.info(f"Release '{version}' already exists. Skipping...")
            return None

        return self._post_request(
            "/api/releases",
            data={
                "ProjectId": project_id,
                "Version": version,
                "ReleaseNotes": json.dumps(release_note_dict),
                "SelectedPackages": self._determine_latest_deploy_packages(project_id),
            },
        )

    def deploy_release(
        self,
        version,
        project_name,
        environment,
        tenants=None,
        wait_for_deployment=None,
        started_span_id="None",
    ):
        # Todo variable="GithubSpanID:{started_span_id}"

        if not tenants:
            tenants = [None]

        deployments = []
        for ten in tenants:
            deployments.append(
                self._deploy_tenant(project_name, version, environment, tenant=ten)
            )

        if wait_for_deployment:
            project_id = self.get_project_id(project_name)
            self._wait_for_completion(deployments, project_id, environment)

        return deployments

    def _wait_for_completion(self, deployments, project_id, environment):
        start = datetime.now()
        last = None
        while True:
            states = self._get_deployment_states(deployments, project_id, environment)
            num_completed = 0
            num_errored = 0
            for dep in deployments:
                state = states[dep["Id"]]
                num_completed = num_completed + state.get("IsCompleted", False)
                num_errored = num_errored + state.get("HasWarningsOrErrors", False)
                if state["ErrorMessage"]:
                    logger.info(f"{dep['Name']}: {state['ErrorMessage']}")

            current = {"completed": num_completed, "failed": num_errored}

            if current != last:
                logger.info(
                    f"Completed {current['completed']} / {len(deployments)} "
                    f"deployments with {current['failed']} errors"
                )

            if num_completed == len(deployments):
                break

            if _MAX_WAIT_TIME < datetime.now() - start:
                logger.warning(
                    f"Exceeded maximum wait time of {_MAX_WAIT_TIME} "
                    f"for the deployment. Proceeding anyway..."
                )
                break

            last = current
            sleep(1)

    def _get_deployment_states(self, deployments, project_id, environment):
        environment_id = self.get_environment_id(environment)
        release_ids = [d["ReleaseId"] for d in deployments]
        deployment_ids = [d["Id"] for d in deployments]
        states = {}
        progression = self._get_request(f"api/projects/{project_id}/progression")
        for rel in progression["Releases"]:
            if rel["Release"]["Id"] not in release_ids:
                continue

            if environment_id not in rel["Deployments"]:
                continue

            for dep in rel["Deployments"][environment_id]:
                if not dep["DeploymentId"] in deployment_ids:
                    continue

                states[dep["DeploymentId"]] = dep

        return states

    def _deploy_tenant(self, project_name, version, environment, tenant=None):
        logger.debug(
            f"Deploying '{project_name}' version '{version}' to '{environment}'"
        )
        data = self._post_request(
            "api/deployments",
            data={
                "EnvironmentId": self.get_environment_id(environment),
                "ProjectId": self.get_project_id(project_name),
                "ReleaseId": self.get_release_id(project_name, version),
                "TenantId": tenant,
            },
        )
        return data

    @functools.lru_cache
    def get_project_id(self, name):
        return self._get_request(f"api/projects/{name}").get("Id")

    @functools.lru_cache
    def get_release_id(self, project, version):
        project_id = self.get_project_id(project)
        return self._get_request(f"api/projects/{project_id}/releases/{version}")["Id"]

    def get_environment_id(self, environment):
        if not self._cached_environment_ids:
            data = self._get_request("api/environments/all")
            self._cached_environment_ids = {e["Name"]: e["Id"] for e in data}
        return self._cached_environment_ids.get(environment)

    def _verify_connection(self):
        try:
            self._get_request("api")
        except requests.RequestException as err:
            logger.error(
                "Could not establish connection with Octopus deploy server "
                f"at '{self._baseurl}'. Failed with '{err}'"
            )
        logger.debug(
            f"Successfully connected to Octopus deploy server '{self._baseurl}'"
        )

    def _get_request(self, path):
        url = urllib.parse.urljoin(self._baseurl, path)
        response = requests.get(url, headers=self._headers)
        logger.debug(
            f"{response.request.method} {response.url}: {response.status_code}"
        )
        return _handle_response(response)

    def _post_request(self, path, data):
        url = urllib.parse.urljoin(self._baseurl, path)
        response = requests.post(url, json=data, headers=self._headers)
        logger.debug(
            f"{response.request.method} {response.url}: {response.status_code}"
        )
        return _handle_response(response)

    def _determine_latest_deploy_packages(self, project_id):
        """
        A release needs to specify the version of all deployment steps. We fetch
        the latest version by selecting the highest available SemVer.
        """
        template: dict = self._get_request(
            f"api/projects/{project_id}/deploymentprocesses/template"
        )

        packages = []
        for pkg in template["Packages"]:
            ver = self._get_request(
                f"api/feeds/{pkg['FeedId']}/packages/versions?"
                f"packageId={pkg['PackageId']}&preReleaseTag={_RELEASE_REGEX}&take=1"
            )

            packages.append(
                {
                    "ActionName": (pkg["ActionName"]),
                    "Version": ver["Items"][0]["Version"],
                }
            )

        return packages

    def _does_release_exist(self, project_id, version):
        url = urllib.parse.urljoin(
            self._baseurl, f"api/projects/{project_id}/releases/{version}"
        )
        response = requests.head(url, headers=self._headers)
        return response.status_code == 200


def _handle_response(response):
    data = response.json()
    if 200 <= response.status_code < 300:
        return data

    elif response.status_code in [400, 404]:
        err: str = data.get("ErrorMessage", "Unknown error")

        errors = data.get("Errors", [])
        if errors:
            err = err + f" {'. '.join(errors)}"

        help_links = data.get("ParsedHelpLinks")
        if help_links:
            err = err + f" ({help_links})"
        raise RuntimeError(err)

    else:
        raise RuntimeError(
            f"{response.request.method} '{response.url}' failed with status "
            f"'{response.status_code}'"
        )


if __name__ == "__main__":
    try:
        octopus = Octopus(
            server=os.getenv("INPUT_OCTOPUS_SERVER"),
            api_key=os.getenv("INPUT_OCTOPUS_API_KEY"),
        )
        p = octopus.create_release("0.0.9999", "example-deploy-project")
        print(p)

    except BaseException as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
