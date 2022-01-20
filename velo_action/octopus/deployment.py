import datetime
import logging
from datetime import datetime, timedelta
from time import sleep

from velo_action.octopus.client import OctopusClient
from velo_action.octopus.deployment_state import DeploymentState
from velo_action.octopus.release import Release

_MAX_WAIT_TIME = timedelta(seconds=20)
logger = logging.getLogger(name="octopus")


class Deployment:
    _octo_object = {}
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

    def create(self, env_name, tenant=None, wait_to_complete=False, variables=None):
        """
        Deploy the current Release a specific env with an optional tenant
        """

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
            form_variables = {}
            mapping = self._release.form_variable_id_mapping()
            for name, value in variables.items():
                if name in mapping:
                    form_variables[mapping[name]] = value
                else:
                    logging.warning(
                        f"Supplied variable '{name}' is not known in "
                        "the project variables"
                    )
            payload["FormValues"] = form_variables

        self._octo_object = self._client.post("api/deployments", data=payload)

        if wait_to_complete:
            self._wait_for_completion(
                environment_id=environment_id, tenant_id=tenant_id
            )

        # Data involved in creating a deployment
        #
        # * ProjectID
        # * Version
        # * EnvironmentID
        # * VariableSet (ideally version form release)
        # * TenantID
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/projects/Projects-123
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/releases/Releases-7149
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/variables/variableset-Projects-123
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/releases/Releases-7149/snapshot-variables
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/variables/variableset-Projects-123-s-27-93NYL

    def _wait_for_completion(self, environment_id, tenant_id):
        start = datetime.now()

        while True:
            state = self.get_deployment_state(
                environment_id=environment_id, tenant_id=tenant_id
            )
            if state.completed:
                logger.info("Deployment completed")
                break
            if start + _MAX_WAIT_TIME > datetime.now():
                logger.info(f"Wait time {_MAX_WAIT_TIME} exceeded. Proceeding anyway")
                break
            sleep(secs=1)

        return state.state == "Success"

    def get_deployment_state(self, environment_id, tenant_id) -> DeploymentState:
        progression = self._client.get(f"api/projects/{self.project_id()}/progression")

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

                return DeploymentState(
                    completed=dep["IsCompleted"],
                    error=dep["ErrorMessage"],
                    has_warning=dep["HasWarningsOrErrors"],
                    state=dep["State"],
                )
