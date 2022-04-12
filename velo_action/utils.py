import os
from pathlib import Path
from typing import List, Optional

from semantic_version import SimpleSpec, Version

from velo_action.settings import (
    APP_SPEC_FIELD_PROJECT,
    APP_SPEC_FIELD_VELO_VERSION,
    APP_SPEC_FILENAMES,
    VELO_RELEASE_GITUHB_URL,
    VELO_SEM_VER_SPEC_DOCS_URL,
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

    try:
        project = read_field_from_app_spec(APP_SPEC_FIELD_PROJECT, filepath)
    except ValueError as error:
        raise SystemExit(
            "'project' field is required in the AppSpec (app.yml). "
            "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
        ) from error

    try:
        value = read_field_from_app_spec(APP_SPEC_FIELD_VELO_VERSION, filepath)
    except ValueError as error:
        raise SystemExit(
            "'velo_version' field is required in the AppSpec (app.yml). "
            "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
        ) from error

    try:
        version_spec = SimpleSpec(value)
    except ValueError as error:
        raise SystemExit(  # pylint: disable=raise-missing-from
            f"{APP_SPEC_FIELD_VELO_VERSION}: '{value}' in the AppSpec is not a valid semantic version spesification.\n"
            f"See {VELO_SEM_VER_SPEC_DOCS_URL} for valid syntax,\n"
            f"and {VELO_RELEASE_GITUHB_URL} for valid releases."
        ) from error

    return VeloSettings(project=project, velo_version=version_spec)


def read_field_from_app_spec(field: str, filename: Path) -> str:
    """Read the project field from the app.yml.

    Cannot assume the app.yml is rendered,
    hence we cannot read the files as YAML.
    """
    with open(filename, encoding="utf-8") as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith(f"{field}:"):
                return line.split(":")[1].strip().strip('"').strip("'")
    raise ValueError(f"Could not find '{field}' in {filename}")


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
