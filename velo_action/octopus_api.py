import json
import logging
import os
import traceback
import urllib.parse

import requests

logger = logging.getLogger(name="octopus")


class Octopus:
    """
    Client to interact with the Octopus Deploy server
    """

    def __init__(self, server=None, api_key=None):
        self._baseurl = server
        self._headers = {"X-Octopus-ApiKey": f"{api_key}"}
        self._verify_connection()

    def list_tenants(self):
        return self._get_request("/api/tenants/all")

    def list_releases(self, project):
        project_id = self.get_project_id(project)
        data = self._get_request(f"api/projects/{project_id}/releases")
        return data["Items"]

    def create_release(self, version, project, release_note_dict=None):
        project_id = self.get_project_id(project)
        if self._does_release_exist(project_id, version):
            logger.info(f"Release '{version}' already exists. Skipping...")
            return

        release_data = {
            "ProjectId": project_id,
            "Version": version,
            "ReleaseNotes": json.dumps(release_note_dict),
            "SelectedPackages": self._get_release_packages(project),
        }

        return self._post_request("/api/releases", data=release_data)

    def deploy_release(
        self,
        version,
        project,
        environment,
        tenants=None,
        progress=None,
        wait_for_deployment=None,
        started_span_id="None",
    ):
        pass

    def get_project_id(self, slug):
        data = self._get_request(f"api/projects/{slug}")
        return data["Id"]

    def _verify_connection(self):
        try:
            self._get_request("api")
        except requests.RequestException as e:
            logger.error(
                "Could not establish connection with Octopus deploy server "
                f'at "{self._baseurl}".'
            )
        logger.debug(
            f'Successfully connected to Octopus deploy server "{self._baseurl}"'
        )

    def _get_request(self, path):
        url = urllib.parse.urljoin(self._baseurl, path)
        response = requests.get(url, headers=self._headers)
        return _handle_response(response)

    def _post_request(self, path, data):
        url = urllib.parse.urljoin(self._baseurl, path)
        response = requests.post(url, json=data, headers=self._headers)
        return _handle_response(response)

    def _get_release_packages(self, project):
        project_id = self.get_project_id(project)
        template: dict = self._get_request(
            f"api/projects/{project_id}/deploymentprocesses/template"
        )

        packages = []
        for p in template["Packages"]:
            release_regex = "^(|\+.*)$"

            v = self._get_request(
                f"api/feeds/{p['FeedId']}/packages/versions?"
                f"packageId={p['PackageId']}&preReleaseTag={release_regex}&take=1"
            )

            packages.append(
                {"ActionName": (p["ActionName"]), "Version": v["Items"][0]["Version"]}
            )

        return packages

    def _does_release_exist(self, project_id, version):
        url = urllib.parse.urljoin(
            self._baseurl, f"api/projects/{project_id}/releases/{version}"
        )
        response = requests.head(url, headers=self._headers)
        return response.status_code == 200


def _handle_response(response):
    j = response.json()
    if 200 <= response.status_code < 300:
        return j

    elif response.status_code == 400:
        err: str = f"{j['ErrorMessage']} {'. '.join(j['Errors'])}"
        if j["ParsedHelpLinks"]:
            err = err + f" ({j['ParsedHelpLinks']})"
        raise RuntimeError(err)

    else:
        raise RuntimeError(
            f'{response.request.method} "{response.url}" failed with status "'
            f"{response.status_code}"
        )


if __name__ == "__main__":
    try:
        octopus = Octopus(
            server=os.getenv("INPUT_OCTOPUS_SERVER"),
            api_key=os.getenv("INPUT_OCTOPUS_API_KEY"),
        )
        project = "example-deploy-project"

        p = octopus.create_release("0.0.9999", project)
        print(p)

    except BaseException as ex:
        traceback.print_exception(type(ex), ex, ex.__traceback__)
