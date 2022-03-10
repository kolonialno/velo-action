import sys
from pathlib import Path
from typing import List, Optional

import yaml
from semantic_version import SimpleSpec, Version

from velo_action.settings import APP_SPEC_FILENAME, VeloSettings


def resolve_app_spec_filename(deploy_folder: Path) -> Path:
    for filename in APP_SPEC_FILENAME:
        filepath = Path.joinpath(deploy_folder, filename)
        if filepath.is_file():
            return filepath
    raise FileNotFoundError(
        f"Did not find an app.yml or app.yaml file in '{deploy_folder}'"
    )


def read_app_spec(deploy_folder: Path) -> VeloSettings:  # type: ignore  # pylint: disable=inconsistent-return-statements
    """Parse the app.yml

    The attribute names to read from the app_spec (app.yml) at the root level.
    These must not be changed unless Velo is also changed.
    """
    filepath = resolve_app_spec_filename(deploy_folder)
    with open(filepath, "r", encoding="utf-8") as file:
        app_yml = file.read()
        velo_config = yaml.safe_load(app_yml)
    try:
        return VeloSettings.parse_obj(velo_config)
    except Exception as error:  # pylint: disable=broad-except
        # This allows for custom exit message when the app.yml is not valid.
        if error.args[0][0]._loc == "project":  # pylint: disable=protected-access
            sys.exit(  # pylint: disable=raise-missing-from
                "'project' field is required in the AppSpec (app.yml). "
                "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
            )
        if error.args[0][0]._loc == "velo_version":  # pylint: disable=protected-access
            sys.exit(  # pylint: disable=raise-missing-from
                "'velo_version' field is required in the AppSpec (app.yml). "
                "See https://centro.prod.nube.tech/docs/default/component/velo/app-spec/ for instructions."
            )


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
