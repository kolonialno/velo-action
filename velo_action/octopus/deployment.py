from velo_action.octopus.client import OctopusClient


class Deployment:
    def __init__(self, project_name=None, version=None, client=None):
        self._client: OctopusClient = client
        self._project_id = client.get_project_id(name=project_name)
        self._version = version

    @classmethod
    def from_release(cls, release, client):
        dep = Deployment(client=client)
        dep._project_id = release.project_id()
        dep._version = release.version()
        return dep

    def create(self, env_name, tenants=None, wait_to_complete=False, variables=None):
        # Data involved in creating a deployment
        #
        # * ProjectID
        # * Version
        # * Package (consisting of ....)
        # * EnvironmentID
        # * VariableSet (ideally version form release)
        # * TenantID
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/projects/Projects-123
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/releases/Releases-7149
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/variables/variableset-Projects-123
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/releases/Releases-7149/snapshot-variables
        # https://octopusdeploy.prod.nube.tech/api/Spaces-1/variables/variableset-Projects-123-s-27-93NYL

        pass
