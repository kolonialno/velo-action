# type: ignore
import logging
from pathlib import Path
from typing import List, Union

from pydantic import BaseSettings, Field, validator

logger = logging.getLogger(name="octopus")


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

    create_release: bool = False
    deploy_to_environments: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458
    log_level: str = "INFO"
    octopus_api_key_secret: str = None
    octopus_server_secret: str = None
    project: str = None
    service_account_key: str = None
    tenants: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458
    velo_artifact_bucket_secret: str = None
    version: str = None
    wait_for_success_seconds: int = 0
    wait_for_deployment: bool = False

    # GITHUB_WORKSPACE is set in GitHub workflows
    workspace: str = Field(None, env=["input_workspace", "github_workspace"])

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
        name = logging.getLevelName(value)
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
                "The use of 'wait_for_deployment' is deprecated. Please use "
                "'wait_for_success_seconds' instead"
            )
            if not values["wait_for_success_seconds"]:
                values["wait_for_success_seconds"] = 600
        return False
