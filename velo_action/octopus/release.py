import json
import logging

from velo_action.octopus.client import OctopusClient

_RELEASE_REGEX = r"^(|\+.*)$"
logger = logging.getLogger(name="octopus")


class Release:
    _octo_object: dict = {}

    def __init__(self, client=None):
        self._client: OctopusClient = client

    @classmethod
    def from_project_and_version(
        cls, version, client: OctopusClient, project_name=None, project_id=None
    ):
        if not project_id:
            project_id = client.lookup_project_id(project_name)

        rel = cls(client=client)
        rel._octo_object = client.get(f"api/projects/{project_id}/releases/{version}")
        return rel

    def id(self) -> str:
        return self._octo_object.get("Id", "")

    def project_id(self) -> str:
        return self._octo_object.get("ProjectId", "")

    def version(self) -> str:
        return self._octo_object.get("Version", "")

    def create(self, project_name, version, notes=None, auto_select_packages=True):
        if self.exists(project_name, version, client=self._client):
            logger.info(f"Release '{version}' already exists. Skipping...")
            return None
        project_id = self._client.lookup_project_id(project_name)
        if auto_select_packages:
            packages = self._determine_latest_deploy_packages(project_id)
        else:
            packages = None

        obj = self._client.post(
            "api/releases",
            data={
                "ProjectId": project_id,
                "Version": version,
                "ReleaseNotes": json.dumps(notes),
                "SelectedPackages": packages,
            },
        )
        self._octo_object = obj

    def form_variable_id_mapping(self) -> dict:
        """
        Returns a dict that maps all Project variable names to their variable id
        """
        links = self._octo_object["Links"]
        path = links["ProjectVariableSnapshot"]
        project_vars = self._client.get(path)
        variables = project_vars.get("Variables", [])
        var_ids = {v["Name"]: v["Id"] for v in variables}
        return var_ids

    def _determine_latest_deploy_packages(self, project_id) -> list:
        """
        A release needs to specify the version of all deployment steps. We fetch
        the latest version by selecting the highest available SemVer.
        """
        template: dict = self._client.get(
            f"api/projects/{project_id}/deploymentprocesses/template"
        )

        packages = []
        for pkg in template["Packages"]:
            ver = self._client.get(
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

    @classmethod
    def exists(cls, project_name, version, client):
        project_id = client.lookup_project_id(project_name)
        return client.head(f"api/projects/{project_id}/releases/{version}")
