import subprocess
import logging
import json
import os

logger = logging.getLogger(name="octopus")


class Octopus:
    def __init__(self, apiKey: str = None, server: str = None, baseSpaceId: str = "Spaces-1") -> None:
        self.apiKey = apiKey
        self.server = server
        self.baseSpaceId = baseSpaceId
        self._octo_cli_exists()

    def _releaseNotes(self):
        commit_id = os.getenv("GITHUB_SHA")
        branch_name = os.getenv("GITHUB_REF")
        return {"commit_id": commit_id, "branch_name": branch_name}

    def _octo_cli_exists(self):
        try:
            result = subprocess.run("octo", shell=True, capture_output=True)
        except:
            raise Exception("Octopus Cli 'octo' is not installed. See https://octopus.com/downloads/octopuscli for instructions")
        return True

    def _version(self):
        result = subprocess.run("octo --version", shell=True, capture_output=True)
        version = str(result.stdout.decode("utf8")).rstrip("\n")
        return version

    def creatRelease(self, project, version, releaseNotes=None):
        if releaseNotes is None:
            releaseNotes = str(self._releaseNotes())

        result = subprocess.run(
            args=["octo", "list-releases", f"--server={self.server}", f"--apiKey={self.apiKey}", f"--project={project}", "--outputformat=json"], capture_output=True
        )
        releases_list = json.loads(result.stdout.decode("utf8"))[0]
        releases = releases_list.get("Releases")

        exists = False
        for release in releases:
            if release.get("Version") == version:
                logger.info(f"Release {version} already exists. Skipping...")
                exists = True
                break

        if not exists:
            logger.info("Creating release")
            result = subprocess.run(
                args=[
                    "octo",
                    "create-release",
                    f"--server={self.server}",
                    f"--apiKey={self.apiKey}",
                    f"--project={project}",
                    f"--version={version}",
                    f"--releaseNotes={releaseNotes}",
                    "--helpOutputFormat=Json",
                ],
                capture_output=False,
            )

    def deployRelease(self, project, version, environment):
        logger.info("Deploying release")
        result = subprocess.run(
            args=[
                "octo",
                "deploy-release",
                "--helpOutputFormat=Json",
                f"--server={self.server}",
                f"--apiKey={self.apiKey}",
                f"--project={project}",
                f"--version={version}",
                f"--deployTo={environment}",
            ],
            capture_output=False,
        )
