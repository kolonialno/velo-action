from velo_action.version import generate_version


def test_generate_version():

    version = generate_version()
    assert len(version) >= 7
    assert len(version) <= 40
