from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, validator
from semantic_version import SimpleSpec, Version


class VeloSettings(BaseModel):
    """Model to parse the app.yml config file."""

    project: str
    verison: str

    @validator("project")
    def validate_project(cls, field_value):
        assert (
            field_value is not None
        ), "The velo project name is missing, ensure theres a top level project attribute in the projects app.yml. "
        "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/."


def read_app_spec(deploy_folder: Path) -> VeloSettings:
    """Parse the app.yml

    The attribute names to read from the app_spec (app.yml) at the root level.
    These must not be changed unless Velo is also changed.
    """
    VELO_VERSION_APP_SPEC_ATTRIBUTE_NAME = "velo_version"
    VELO_PROJECT_APP_SPEC_ATTRIBUTE_NAME = "project"
    APP_SPEC_FILENAME = ["app.yml", "app.yaml"]

    for filename in APP_SPEC_FILENAME:
        filepath = Path.joinpath(deploy_folder, filename)
        if filepath.is_file():
            with open(filepath, "r") as file:
                app_yml = file.read()
                velo_config = yaml.safe_load(app_yml)
                return VeloSettings.parse_obj(velo_config)
                # return VeloSettings(
                #     version=velo_config.get(VELO_VERSION_APP_SPEC_ATTRIBUTE_NAME, None),
                #     version=velo_config.get(VELO_PROJECT_APP_SPEC_ATTRIBUTE_NAME, None),
                # )
        else:
            raise FileNotFoundError(
                f"Did not find an app.yml or app.yaml file in '{deploy_folder}'"
            )



def find_matching_version(versions: List[str], version_to_match: str) -> Optional[str]:
    """
    Finds the highest matching version in a list of versions.
    using the python semantic_version package.
    """
    versions = [Version.coerce(v) for v in versions]
    parsed_versions = SimpleSpec(str(version_to_match))
    matching_version = parsed_versions.select(versions)
    return str(matching_version)
