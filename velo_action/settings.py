# pylint: disable=no-self-argument,no-self-use
from pathlib import Path
from typing import Any, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, BaseSettings, Field, ValidationError, validator
from semantic_version import SimpleSpec

from velo_action.version import generate_version

logger.remove()

SERVICE_NAME = "velo-action"
GIT_COMMIT_HASH_LENGTH = 40
VELO_TRACE_ID_NAME = "VeloTraceID"
APP_SPEC_FILENAME = ["app.yml", "app.yaml"]

# Name of the fields in the AppSpec.
# These must math what is set in the AppSpec in Velo repo.
APP_SPEC_FIELD_PROJECT = "project"
APP_SPEC_FIELD_VELO_VERSION = "velo_version"


class VeloSettings(BaseModel):
    """Model to parse the app.yml config file."""

    class Config:
        arbitrary_types_allowed = True

    project: str = Field(..., alias=APP_SPEC_FIELD_PROJECT)
    version_spec: Any = Field(..., alias=APP_SPEC_FIELD_VELO_VERSION)

    @validator("version_spec")
    def parse_as_semantic_version(cls, value) -> SimpleSpec:
        return SimpleSpec(value)


class GithubSettings(BaseSettings):
    """[Github Actions Workflow environment variables]

    Required environment variables. These are present by default in the
    Github Actions workflow.

    See list of available Github ACtion Env vars
    https://docs.github.com/en/actions/learn-github-actions/environment-variables

    NB: This is a seperate class since these fields do not have the 'INPUT_' prefix.
    """

    # pylint: disable=no-self-argument,no-self-use
    class Config:
        env_prefix = "GITHUB_"

    workspace: str
    sha: str
    ref_name: str
    server_url: str
    repository: str
    actor: str

    @validator("sha")
    def validate_commit_id(cls, value):
        if not value:
            raise ValidationError(
                "The environment variable GITHUB_SHA must be present."
            )
        if len(value) != GIT_COMMIT_HASH_LENGTH:
            raise ValidationError(
                "The environment variable GITHUB_SHA must contain the full git commit hash with 40 characters."
            )
        return value


class ActionInputs(BaseSettings):
    """[Parse action input arguments]

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

    workspace: Optional[str] = None
    deploy_to_environments: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458

    create_release: bool = False
    version: Optional[str] = None
    log_level: str = "INFO"

    # The secrets are fetched at runtime.
    octopus_api_key_secret: Optional[str] = "velo_action_octopus_api_key"
    octopus_server_secret: Optional[str] = "velo_action_octopus_server"

    # Optional since it is not needed for local testing
    service_account_key: Optional[str] = None

    tenants: Union[
        str, List[str]
    ] = []  # see https://github.com/samuelcolvin/pydantic/issues/1458

    velo_artifact_bucket_secret: Optional[str] = "velo_action_artifacts_bucket_name"

    wait_for_success_seconds: int = 0
    wait_for_deployment: bool = False

    @validator("create_release", always=True)
    def validate_create_release(cls, value, values):
        if value is True:
            return True

        if values["deploy_to_environments"]:
            return True
        return False

    @validator("version", always=True)
    def generate_version_if_no_supplied(cls, value):
        if value is None:
            return generate_version()
        return value

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
        "service_account_key",
        "octopus_server_secret",
        "octopus_api_key_secret",
        "velo_artifact_bucket_secret",
        "workspace",
        pre=True,
    )
    def normalize_str(cls, value):
        """Normalise the input from github actions so we get _real_ none-values"""
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
            return None

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


def resolve_workspace(
    action_inputs: ActionInputs, github_settings: GithubSettings
) -> str:
    """Use the workspace from the input arguments or the github settings.

    If `INPUT_WORKSPACE' from the action.yml is not set. We assume the `.deploy` folder
    is in the repo root.

    Path to this is given by the env var 'GITHUB_WORKSPACE' which is present in
    every Github Action Workflow
    """
    if action_inputs.workspace is None:
        return github_settings.workspace

    return action_inputs.workspace
