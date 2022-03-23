import os
import sys
from pathlib import Path
from typing import List, Optional

from semantic_version import SimpleSpec, Version

from velo_action.settings import (
    APP_SPEC_FIELD_PROJECT,
    APP_SPEC_FIELD_VELO_VERSION,
    APP_SPEC_FILENAMES,
    VeloSettings,
)


def resolve_app_spec_filename(deploy_folder: Path) -> Path:
    for filename in APP_SPEC_FILENAMES:
        filepath = Path.joinpath(deploy_folder, filename)
        if filepath.is_file():
            return filepath
    raise FileNotFoundError(
        f"Did not find an app.yml or app.yaml file in '{deploy_folder}'"
    )


def read_file(file: Path):
    if not os.path.exists(file):
        raise FileNotFoundError(f"{file} does not exist")

    with open(file, "r", encoding="utf-8") as stream:
        return stream.read()


def read_velo_settings(deploy_folder: Path) -> VeloSettings:
    """Parse the AppSpec (app.yml)"""
    filepath = resolve_app_spec_filename(deploy_folder)

    project = read_field_from_app_spec(APP_SPEC_FIELD_PROJECT, filepath)
    if project is None:
        sys.exit(  # pylint: disable=raise-missing-from
            "'project' field is required in the AppSpec (app.yml). "
            "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
        )
    velo_version = read_field_from_app_spec(APP_SPEC_FIELD_VELO_VERSION, filepath)
    if velo_version is None:
        sys.exit(  # pylint: disable=raise-missing-from
            "'velo_version' field is required in the AppSpec (app.yml). "
            "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
        )

    return VeloSettings(project=project, velo_version=velo_version)


def read_field_from_app_spec(field: str, filename: Path) -> Optional[str]:
    """Read the project field from the app.yml.

    Cannot assume the app.yml is rendered,
    hence we cannot read the files as YAML.
    """
    with open(filename, encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith(f"{field}:"):
                return line.split(":")[1].strip().strip('"').strip("'")
    return None


def find_matching_version(
    versions: List[str], version_to_match: SimpleSpec
) -> Optional[Version]:
    """
    Finds the highest matching version in a list of versions.
    using the python semantic_version package.
    """
    versions = [Version.coerce(v) for v in versions]
    matching_version = version_to_match.select(versions)
    return matching_version
