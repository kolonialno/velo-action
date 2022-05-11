# pylint: disable=unused-argument
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from velo_action.main import VELO_DEPLOY_FOLDER_NAME, action


def test_generate_version_no_inputs(
    mock_generate_version_subprocess_run,
    default_action_inputs,
    default_github_settings,
):
    """Verify that the action generates and outputs version when no inputs are provided"""

    with TemporaryDirectory() as tempdir:
        os.mkdir(Path(tempdir).joinpath(VELO_DEPLOY_FOLDER_NAME))
        default_action_inputs.workspace = tempdir

        output = action(
            args=default_action_inputs,
            github_settings=default_github_settings,
        )
        assert output.version == "1af9c7c"
