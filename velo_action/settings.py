from typing import Optional, List, Union
from pydantic import BaseSettings, ValidationError, validator
import os
from pathlib import Path


class Settings(BaseSettings):
    """[Parse input arguments]

    The Github action only provides input arguments to the container as environment variables,
    with INPUT_ prefiex on the argument name.

    This means every argument is parsed as a string.
    To replicate this behaviour when debugging locally all default values is also set to the string 'None'.

    Every githu action input, specified in action.yml, is also set do default string 'None'.
    Otherview you would get an env var in the container with no value, causing an error.
    """
    class Config:
        env_prefix = "INPUT_"

    version: str = None
    log_level: str = "INFO"
    create_release: bool = False
    workspace: str = None  # both INPUT_WORKSPACE and GITHUB_WORKSPACE are valid
    project: str = None
    tenants: Union[str, List[str]] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458
    deploy_to_environments: Union[str, List[str]] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458
    service_account_key: str = None
    octopus_cli_server_secret: str = None
    octopus_cli_api_key_secret: str = None
    velo_artifact_bucket_secret: str = None
    progress: bool = True
    wait_for_deployment: bool = True

    @validator("deploy_to_environments", "tenants", pre=True)
    def validate(cls, val):
        if type(val) is str:
            return val.split(",")
        return val

    @validator("workspace")
    def lookup_from_alternative_envvar(cls, v):
        alt_lookup = os.getenv("GITHUB_WORKSPACE")
        if not v and alt_lookup:
            return alt_lookup
        return v

    @validator("version", "workspace", "project", "tenants", "deploy_to_environments", "service_account_key")
    def check_not_str_none(cls, v):
        """normalise the input from github actions so we get _real_ none-values"""
        if v == "None":
            return None
        elif v == "":
            return None
        return v

    @validator("tenants", "deploy_to_environments")
    def check_list_not_str_none(cls, v):
        """normalise the input from github actions so we get _real_ none-values"""
        if v == "None":
            return []
        elif v == "":
            return []
        return v

    @validator("workspace")
    def validate_valid_path(cls, v):
        path = Path(v)
        if not path.exists():
            raise ValidationError(f"path {path} does not exist")
        if not path.is_dir():
            raise ValidationError(f"path {path} is not a dir")
        return v
