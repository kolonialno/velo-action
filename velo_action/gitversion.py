import logging
import json
from velo_action import proc_utils
from pathlib import Path

logger = logging.getLogger(name="gitversion")


class Gitversion:
    def __init__(self, path: Path):
        self.path = path

        self._gitversion_cli_exists()
        self.version = self._version()
        logger.debug(f"Gitversion version={self.version}")

    def _gitversion_cli_exists(self):
        try:
            proc_utils.execute_process("gitversion", log_cmd=False, log_stdout=False, cwd=self.path)
        except Exception as e:
            raise Exception(
                "Gitversion Cli 'gitversion' is not installed. \
                 See https://gitversion.net/docs/usage/cli/installation for instructions."
            ) from e
        return True

    def _version(self):
        result = proc_utils.execute_process("gitversion /version", log_cmd=False, log_stdout=False, cwd=self.path)
        version = result[0]
        return version

    def generate_version(self):
        """Generate a GitVersion version

        Requires a initialised repo, aka .git folder and a GitVersion.yml configurations file.

        If GitVersion.yml is not found, one will be generated with the Mainline mode.
        https://gitversion.readthedocs.io/en/latest/input/docs/reference/versioning-modes/mainline-development/
        """
        gitversion_config_file = Path.joinpath(self.path, "GitVersion.yml")
        if not gitversion_config_file.is_file():
            logger.warning(f"GitVersion.yml not found in {self.path}.")
            logger.info("Creating GitVersion.yml with mode: Mainline.")

            gitversion = "---\nmode: Mainline\n"
            with open(gitversion_config_file, "w") as file:
                file.write(gitversion)

        result = proc_utils.execute_process("gitversion", log_cmd=False, log_stdout=False, cwd=self.path)
        version = json.loads("".join(result))
        semver = version.get("SemVer")
        return semver
