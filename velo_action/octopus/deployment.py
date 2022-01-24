import enum
import logging
import typing
from datetime import datetime, timedelta
from time import sleep

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.release import Release

_MAX_WAIT_TIME = timedelta(minutes=10)
logger = logging.getLogger(name="octopus")


class DeploymentState(enum.Enum):
    PROGRESS = enum.auto()
    SUCCESS = enum.auto()
    FAIL = enum.auto()
    TIMEOUT = enum.auto()


class Deployment:
    _octo_object: typing.Any = {}
    _release: Release = None

    def __init__(self, project_name=None, version=None, client=None):
        self._client: OctopusClient = client
        if project_name and version:
            self._release = Release.from_project_and_version(
                project_name=project_name, version=version, client=client
            )

    @classmethod
    def from_release(cls, release, client):
        dep = cls(client=client)
        dep._release = release
        return dep

    def id(self) -> str:
        return self._octo_object.get("Id", "")

    def project_id(self) -> str:
        return self._release.project_id() if self._release else ""

    def release(self) -> Release:
        return self._release

    def release_id(self) -> str:
        return self._release.id() if self._release else ""

    def create(self, env_name, tenant=None, wait_for_success=False, variables=None):
        """
        Deploy the current Release a specific env with an optional tenant
        """

        if not self._release:
            raise RuntimeError("Cannot create deployment. Release was not specified.")

        environment_id = self._client.lookup_environment_id(env_name)
        tenant_id = self._client.lookup_tenant_id(tenant)

        payload = {
            "EnvironmentId": environment_id,
            "ProjectId": self.project_id(),
            "ReleaseId": self.release_id(),
        }

        if tenant:
            payload["TenantId"] = tenant_id

        if variables:
            payload["FormValues"] = self._build_form_variables(
                environment_id, variables
            )

        self._octo_object = self._client.post("api/deployments", data=payload)

        if wait_for_success:
            result = self._wait_until_completed(
                environment_id=environment_id, tenant_id=tenant_id
            )
            if result == DeploymentState.SUCCESS:
                logger.info("Deployment finished successfully")
            elif result == DeploymentState.FAIL:
                raise RuntimeError("Deployment completed with error")
            elif result == DeploymentState.TIMEOUT:
                raise TimeoutError("Time limit exceeded while waiting for deployment")
            else:
                raise RuntimeError(f"Unexpected state '{result}'")

    def get_state(self, environment_id, tenant_id) -> DeploymentState:
        progression = self._client.get(f"api/projects/{self.project_id()}/progression")
        dep_state = {}

        for rel in progression["Releases"]:
            if rel["Release"]["Id"] != self.release_id():
                continue

            if environment_id not in rel["Deployments"]:
                continue

            for dep in rel["Deployments"][environment_id]:
                if self.id() != dep["DeploymentId"]:
                    continue

                if tenant_id and dep["TenantId"] != tenant_id:
                    continue

                dep_state = dep
                break

            if dep_state:
                break

        if dep_state["State"] == "Success":
            return DeploymentState.SUCCESS
        else:
            return DeploymentState.FAIL

    def _build_form_variables(self, environment_id, variables) -> dict:
        """
        Converts supplied dict of variable names and value into a dict of variable
        ids and values
        """

        form_variables = {}
        mapping = self._variable_name_to_id_mapping(environment_id)
        for name, value in variables.items():
            if name in mapping:
                form_variables[mapping[name]] = value
            else:
                logging.warning(
                    f"Supplied variable '{name}' is not a known project variable"
                )
        return form_variables

    def _wait_until_completed(self, environment_id, tenant_id) -> DeploymentState:
        logger.info(f"Waiting up to {_MAX_WAIT_TIME} for completion...")
        start = datetime.now()

        while True:
            state = self.get_state(environment_id=environment_id, tenant_id=tenant_id)
            if state == DeploymentState.SUCCESS:
                return state
            if datetime.now() > start + _MAX_WAIT_TIME:
                logger.warning(
                    f"Wait time {_MAX_WAIT_TIME} exceeded. Proceeding anyway"
                )
                return DeploymentState.TIMEOUT
            sleep(1)

    def _variable_name_to_id_mapping(self, environment_id):
        """
        Returns mapping of form variable names to their id

        The mapping does also exist in the VariableSet (api/variables/variableset-*)
        but that endpoint requires additional permissions.
        """
        preview = self._client.get(
            f"api/releases/{self.release_id()}/deployments/preview/{environment_id}"
        )
        form_elements = preview["Form"]["Elements"]

        return {e["Control"]["Name"]: e["Name"] for e in form_elements}
