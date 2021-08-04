import logging
import json
from velo_action import proc_utils

logger = logging.getLogger(name="octopus")


class Octopus:
    def __init__(self, api_key: str = None, server: str = None, base_space_id: str = "Spaces-1") -> None:
        self.api_key = api_key
        self.server = server
        self.base_space_id = base_space_id
        self._octo_cli_exists()
        self.octa_env_vars = {"OCTOPUS_CLI_API_KEY": self.api_key, "OCTOPUS_CLI_SERVER": self.server}

        # test connection to server
        try:
            proc_utils.execute_process("octo list-environments", log_cmd=False, env_vars=self.octa_env_vars, log_stdout=False)
        except:
            raise Exception(f"Could not connect to Octopus deploy server at {self.server}")

    def _octo_cli_exists(self):
        try:
            proc_utils.execute_process("octo", log_cmd=False, log_stdout=False)
        except:
            raise Exception("Octopus Cli 'octo' is not installed. See https://octopus.com/downloads/octopuscli for instructions")
        return True

    def _version(self):
        result = proc_utils.execute_process("octo --version", log_cmd=False, log_stdout=False)
        version = result[0]
        return version

    def list_tenants(self):
        cmd = "octo list-tenants --outputformat=json"
        result = proc_utils.execute_process(cmd, self.octa_env_vars, log_cmd=False, log_stdout=False)
        tenants_list = json.loads("".join(result))
        tenant_names = [o.get("Name") for o in tenants_list]
        return tenant_names

    def list_releases(self, project):
        cmd = f"octo list-releases --project={project} --outputformat=json"
        result = proc_utils.execute_process(cmd, self.octa_env_vars, log_stdout=False, log_cmd=False)
        releases_list = json.loads("".join(result))
        releases = releases_list[0].get("Releases")
        return releases

    def create_release(self, version, project, release_notes=None):
        releases = self.list_releases(project)
        exists = False
        if releases:
            for release in releases:
                if release.get("Version") == version:
                    logger.info(f"Release '{version}' already exists. Skipping...")
                    exists = True
                    break

        if not exists:
            cmd = f"octo create-release --version={version} --project={project} --releaseNotes='{release_notes}' --helpOutputFormat=Json"
            proc_utils.execute_process(cmd, self.octa_env_vars, log_stdout=True, forward_stdout=False)

    def deploy_release(self, version, project, environment, tenants=None, progress=None, wait_for_deployment=None, deployAt=None, noDeployAfter=None):
        args = ["--helpOutputFormat=Json"]
        if progress:
            args.append("--progress")
        if wait_for_deployment:
            args.append("--waitForDeployment")

        cmd = f"octo deploy-release --project={project} --version={version} --deployTo={environment}"
        cmd = cmd + " " + " ".join(str(x) for x in args)
        if tenants:
            octo_tenants = self.list_tenants()
            for tenant in tenants:
                if tenant not in octo_tenants:
                    raise Exception(f"Tenant '{tenant}' does not exist in Octopus Deploy, found '{octo_tenants}'.")

                cmd_tenant = f"--tenant={tenant}"
                proc_utils.execute_process(cmd + " " + cmd_tenant, env_vars=self.octa_env_vars, log_stdout=True, forward_stdout=False)
                logger.info(f"Deploying '{project}' '{tenant}' version '{version}' to '{environment}'")
        else:
            proc_utils.execute_process(cmd, env_vars=self.octa_env_vars, log_stdout=True, forward_stdout=False)
            logger.info(f"Deploying '{project}' version '{version}' to '{environment}'")
