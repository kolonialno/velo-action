import subprocess
import os
import logging
import json

from velo_action.action import BASE_DIR


class Gitversion:
    def __init__(self):
        self._gitversion_cli_exists()

    def _gitversion_cli_exists(self):
        try:
            _ = subprocess.run("gitversion", shell=True, capture_output=True)
        except:
            raise Exception("Gitversion Cli 'gitversion' is not installed. See https://gitversion.net/docs/usage/cli/installation for instructions.")
        return True

    def _version(self):
        """Version of the Gitversion CLI installed"""
        result = subprocess.run("gitversion /version", shell=True, capture_output=True)
        version = str(result.stdout.decode("utf8")).rstrip("\n")
        return version

    def _create_gitversion_config_file(self, path):
        gitversion = """
            ---
            mode: Mainline
            """
        try:
            f = open(path, "w")
            try:
                f.write(gitversion)
            finally:
                f.close()
        except IOError as e:
            logging.error(f"Could not create GitVersion.yml file at {path}", exc_info=e)

    def generate_version(self, path):
        """Generate a GitVersion version

        Requires a initialised repo, aka .git folder and a GitVersion.yml configurations file.

        If GitVersion.yml is not found, one will be generated with the Mainline mode.
        https://gitversion.readthedocs.io/en/latest/input/docs/reference/versioning-modes/mainline-development/
        """
        assert os.path.isdir(path)

        gitversion_path = path + "/GitVersion.yml"

        if not os.path.isfile(gitversion_path):
            logging.warning("GitVersion.yml not found.")
            logging.warning("Creating GitVersion.yml with mode: Mainline.")
            self._create_gitversion_config_file(gitversion_path)

        assert os.path.isfile(gitversion_path)
        result = subprocess.run("gitversion", stdout=subprocess.PIPE, cwd=path).stdout.decode("utf8")

        logging.debug(f"Gitversion raw={result}")

        if result == "":
            raise Exception(f"Cannot find the .git directory at path {gitversion_path}")
        else:
            gitversion = json.loads(result)
            version = gitversion.get("SemVer")
            return version
