from pathlib import Path
from typing import List, Optional, Union

from loguru import logger
from pydantic import BaseSettings, Field, validator

from velo_action.version import generate_version

logger.remove()
GIT_COMMIT_HASH_LENGTH = 40


class Settings(BaseSettings):
    """[Parse input arguments]

    The Github action only provides input arguments to the container as environment variables,
    with INPUT_ prefix on the argument name.

    This means every argument is parsed as a string.
    To replicate this behaviour when debugging locally all default values is also set to the string 'None'.

    Every github action input, specified in action.yml, is also set do default string 'None'.
    Otherwise you would get an env var in the container with no value, causing an error.
    """

    # pylint: disable=no-self-argument,no-self-use

    class Config:
        env_prefix = "INPUT_"

    project: str
    create_release: bool = False
    deploy_to_environments: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458

    log_level: str = "INFO"
    octopus_api_key_secret: str
    octopus_server_secret: str

    # Optional since it is not needed for local testing
    service_account_key: Optional[str] = None

    tenants: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458
    velo_artifact_bucket_secret: str
    version: Optional[str] = None
    wait_for_success_seconds: int = 0
    wait_for_deployment: bool = False

    # GITHUB_WORKSPACE is set in GitHub workflows
    workspace: str = Field(None, env=["input_workspace", "github_workspace"])

    commit_id: str = Field(env_var="GITHUB_SHA")
    branch_name: str = Field(env_var="GITHUB_REF")

    github_server_url: str = Field(env_var="GITHUB_SERVER_URL")
    github_repository: str = Field(env_var="GITHUB_REPOSITORY")

    @validator("commit_id")
    def validate_commit_id(cls, value):
        if not value:
            raise ValueError("The environment variable GITHUB_SHA must be present.")
        if len(value) != GIT_COMMIT_HASH_LENGTH:
            raise ValueError(
                "The environment variable GITHUB_SHA must contain the full git commit hash with 40 characters."
            )
        return value

    @validator("branch_name")
    def validate_branch_name(cls, value):
        if not value:
            raise ValueError(
                "The environment variable GITHUB_REF must be present, and contain the git branch name."
            )
        return value

    @validator("create_release", always=True)
    def create_release_if_deploy_to_envs(cls, value):
        if value is None:
            return generate_version()
        return value

    @validator("version", always=True)
    def generate_version_if_no_supplied(cls, _, values):
        if values["deploy_to_environments"]:
            return True
        return False

    @validator("deploy_to_environments", "tenants", pre=True)
    def split_list(cls, value):
        if value in ("None", ""):
            return []
        elif isinstance(value, str):
            return value.split(",")
        elif isinstance(value, list):
            return value
        else:
            raise ValueError("Needs to be a string with ',' as separator or a list.")

    @validator(
        "version",
        "log_level",
        "project",
        "service_account_key",
        "octopus_server_secret",
        "octopus_api_key_secret",
        "velo_artifact_bucket_secret",
        "workspace",
        pre=True,
    )
    def normalize_str(cls, value):
        """normalise the input from github actions so we get _real_ none-values"""
        if value in ("None", ""):
            return None
        return value

    @validator("log_level")
    def validate_log_level(cls, value):
        name = logger.level(value)
        if isinstance(name, str):
            raise ValueError()
        return value

    @validator("workspace")
    def absolute_path(cls, value):
        if value is None:
            value = "."

        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise ValueError(f"path '{path}' does not exist")
        if not path.is_dir():
            raise ValueError(f"path '{path}' is not a directory")
        return str(path)

    @validator("wait_for_deployment")
    def deprecate_wait_for_deployment(cls, val, values: dict):
        if val:
            logger.warning(
                "NOTE: The use of 'wait_for_deployment' is deprecated. Please use "
                "'wait_for_success_seconds' instead."
            )
            if not values["wait_for_success_seconds"]:
                values["wait_for_success_seconds"] = 600
        return False
