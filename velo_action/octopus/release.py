import sys
from typing import Dict, List, Optional

from loguru import logger
from semantic_version import SimpleSpec, Version

from velo_action.octopus.client import OctopusClient
from velo_action.settings import (
    APP_SPEC_FIELD_VELO_VERSION,
    VELO_RELEASE_GITUHB_URL,
    GithubSettings,
)
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
        self.client: OctopusClient = client

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

    def create(
        self,
        project_name: str,
        project_version: str,
        velo_version_spec: SimpleSpec,
        github_settings: GithubSettings,
    ) -> None:

        assert isinstance(
            velo_version_spec, SimpleSpec
        ), "velo_version_spec is not a SimpleSpec type"

        if self.exists(project_name, project_version, client=self.client):
            logger.info(
                f"Release '{project_version}' already exists at "
                f"'{self.client.baseurl}/app#/Spaces-1/projects/"
                f"{project_name}/deployments/releases/{project_version}'. "
                "Skipping..."
            )
            return None

        logger.info(
            f"Creating a release for project '{project_name}' with version '{project_version}'"
        )
        project_id = self.client.lookup_project_id(project_name)

        velo_version = self._resolve_velo_bootstrapper_version(velo_version_spec)
        if velo_version is None:
            sys.exit(
                f"Velo version spec '{velo_version_spec}' does not resolve to a valid Velo version. "
                f"Make sure the version requirement you set in '{APP_SPEC_FIELD_VELO_VERSION}' in the AppSpec exists. "
                f"You can find Velo releases at {VELO_RELEASE_GITUHB_URL}. "
                "Exiting..."
            )
        package = self._create_octopus_package_payload(
            package=VELO_BOOTSTRAPPER_ACTION_NAME, version=velo_version
        )

        payload = {
            "ProjectId": project_id,
            "Version": project_version,
            "ReleaseNotes": create_release_notes(github_settings),
            "SelectedPackages": package,
        }

        self._octo_object = self.client.post("api/releases", data=payload)
        return None

    @classmethod
    def _create_octopus_package_payload(
        cls, package: str, version: Version
    ) -> List[Dict[str, str]]:
        """Create payload for a Octopus Deploy pacakge to be used in a release."""
        return [{"ActionName": package, "Version": str(version)}]

    def _resolve_velo_bootstrapper_version(
        self, version_spec: SimpleSpec
    ) -> Optional[Version]:
        """Resolves the 'version_spec' to a valid 'velo-bootstrapper' package in Ocopus Deploy

        If non is found not return None.
        """
        velo_bootstrapper_versions = self.list_available_deploy_packages()
        return find_matching_version(
            versions=velo_bootstrapper_versions, version_to_match=version_spec
        )

    def form_variable_id_mapping(self) -> dict:
        """
        Returns a dict that maps all Project variable names to their variable id
        """
        links = self._octo_object["Links"]
        path = links["ProjectVariableSnapshot"]
        project_vars = self.client.get(path)
        variables = project_vars.get("Variables", [])
        var_ids = {v["Name"]: v["Id"] for v in variables}
        return var_ids

    def _determine_latest_deploy_packages(self, project_id) -> List[Dict[str, str]]:
        """
        A release needs to specify the version of all deployment steps. We fetch
        the latest version by selecting the highest available SemVer.
        """
        template: dict = self.client.get(
            f"api/projects/{project_id}/deploymentprocesses/template"
        )

        packages = []
        for pkg in template["Packages"]:
            ver = self.client.get(
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
        packages: dict = self.client.get(
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


def create_release_notes(github: GithubSettings) -> str:
    """Create release notes for a Octopus Deploy"""
    return f"""
<b>Commit</b>: <a href={github.server_url}/{github.repository}/commit/{github.sha}>{github.sha}</a>
<br>
<br>
<b>Branch name</b>: <a href={github.server_url}/{github.repository}/tree/{github.ref_name}>{github.ref_name}</a>
<br>
<br>
<b>Created by </b>: <a href={github.server_url}/{github.actor}>{github.actor}</a>
""".replace(
        "\n", " "
    )
