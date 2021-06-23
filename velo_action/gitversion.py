import subprocess
import os
import logging
import json
from pathlib import Path

logger = logging.getLogger(name="gitversion")


class Gitversion:
    def __init__(self):
        self._gitversion_cli_exists()

    def _gitversion_cli_exists(self):
        try:
            result = subprocess.run("gitversion", stdout=subprocess.PIPE, shell=False, capture_output=False)
        except:
            raise Exception("Gitversion Cli 'gitversion' is not installed. See https://gitversion.net/docs/usage/cli/installation for instructions.")
        return True

    def _version(self):
        """Version of the Gitversion CLI installed"""
        process = subprocess.run("gitversion /version", shell=True, capture_output=True)
        if process.returncode != 0:
            logger.warning(f"Process exited with return code {process.returncode}")
            raise Exception(f"gitversion error: {process.stderr}")

        version = str(process.stdout.decode("utf8")).rstrip("\n")
        return version

    def _create_gitversion_config_file(self, path):
        gitversion = "---\nmode: Mainline\n"
        try:
            f = open(path, "w")
            try:
                f.write(gitversion)
            finally:
                f.close()
        except IOError as e:
            logger.error(exc_info=e)
            raise Exception(f"Could not create file at {path}", exc_info=e)

    def generate_version(self, path):
        """Generate a GitVersion version

        Requires a initialised repo, aka .git folder and a GitVersion.yml configurations file.

        If GitVersion.yml is not found, one will be generated with the Mainline mode.
        https://gitversion.readthedocs.io/en/latest/input/docs/reference/versioning-modes/mainline-development/
        """
        gitversion_path = path + "/GitVersion.yml"
        if not os.path.isfile(gitversion_path):
            logger.warning("GitVersion.yml not found.")
            logger.warning("Creating GitVersion.yml with mode: Mainline.")
            self._create_gitversion_config_file(gitversion_path)

        if not os.path.isfile(gitversion_path):
            raise Exception("Did not find a 'GitVersion.yml' in repo root.")

        process = subprocess.run("gitversion", cwd=path, capture_output=True)
        if process.returncode != 0:
            logger.warning(f"Process exited with return code {process.returncode}")
            raise Exception(f"gitversion error: {process.stderr}")
        else:
            temp = process.stdout.decode("utf8")
            gitversion = json.loads(temp)
            version = gitversion.get("SemVer")
            return version
