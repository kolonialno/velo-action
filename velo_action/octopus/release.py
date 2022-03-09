from typing import List, Optional

from loguru import logger
from semantic_version import SimpleSpec

from velo_action.octopus.client import OctopusClient
from velo_action.utils import find_matching_version

_RELEASE_REGEX = r"^(|\+.*)$"

# This name is set in Octopus deploy when creating the StepTemplate
# https://octopusdeploy.prod.nube.tech/app#/Spaces-1/library/steptemplates/ActionTemplates-1?activeTab=settings
VELO_BOOTSTRAPPER_ACTION_NAME = "run velo"

# Id of the uploaded velo-bootstrapper NuGet package
# https://octopusdeploy.prod.nube.tech/app#/Spaces-1/library/builtinrepository/versions/velo-bootstrapper
VELO_BOOTSTRAPPER_PACKAGE_ID = "velo-bootstrapper"


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

    def id(self) -> str:  # pylint: disable=invalid-name
        return self._octo_object.get("Id", "")

    def project_id(self) -> str:
        return self._octo_object.get("ProjectId", "")

    def version(self) -> str:
        return self._octo_object.get("Version", "")

    def create(  # pylint: disable=inconsistent-return-statements
        self,
        project_name: str,
        project_version: str,
        velo_version: Optional[SimpleSpec] = None,
        notes: str = None,
    ) -> None:
        if self.exists(project_name, project_version, client=self._client):
            logger.info(
                f"Release '{project_version}' already exists at "
                f"'{self._client._baseurl}/app#/Spaces-1/projects/"  # pylint: disable=protected-access
                f"{project_name}/deployments/releases/{project_version}'. "
                "Skipping..."
            )
            return None
        project_id = self._client.lookup_project_id(project_name)

        packages = []

        version = self._resolve_velo_bootstrapper_version(velo_version)
        if version is None:
            packages = self._determine_latest_deploy_packages(project_id)
        else:
            packages.append(
                {"ActionName": VELO_BOOTSTRAPPER_ACTION_NAME, "Version": version}
            )

        payload = {
            "ProjectId": project_id,
            "Version": project_version,
            "ReleaseNotes": notes,
            "SelectedPackages": packages,
        }

        self._octo_object = self._client.post("api/releases", data=payload)

    def _resolve_velo_bootstrapper_version(
        self, velo_version: SimpleSpec
    ) -> Optional[SimpleSpec]:
        """Verifies that 'velo-bootstrapper' package in Ocopus Deploy exists with a
        'velo_version'.

        If not return None.
        """
        velo_bootstrapper_versions = self.list_available_deploy_packages()
        return find_matching_version(velo_bootstrapper_versions, velo_version)

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

    def list_available_deploy_packages(self) -> List[str]:
        """
        A release needs to specify the version of all deployment steps. We fetch
        the latest version by selecting the highest available SemVer.
        """
        packages: dict = self._client.get(
            (
                "api/Spaces-1/feeds/feeds-builtin/packages/versions?"
                f"packageId={VELO_BOOTSTRAPPER_PACKAGE_ID}&take=1000&includePreRelease=false&includeReleaseNotes=false"
            )
        )

        versions = []

        for pkg in packages["Items"]:
            versions.append(pkg["Version"])
        return versions

    @classmethod
    def exists(cls, project_name, version, client):
        project_id = client.lookup_project_id(project_name)
        return client.head(f"api/projects/{project_id}/releases/{version}")
