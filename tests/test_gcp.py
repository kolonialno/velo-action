import os
from velo_action.gcp import Gcp
import pytest


def has_encoded_key():
    if os.getenv("INPUT_SERVICE_ACCOUNT_KEY"):
        return True
    return False


def has_unencoded_key():
    if os.getenv("INPUT_SERVICE_ACCOUNT_KEY_JSON"):
        return True
    return False


@pytest.mark.skipif(not has_encoded_key(), reason="no encoded key present in env")
def test_gcp_encoded():
    """ensure INPUT_SERVICE_ACCOUNT_KEY envvar exists in order to activate test"""
    g = Gcp(os.getenv("INPUT_SERVICE_ACCOUNT_KEY"))


@pytest.mark.skipif(not has_unencoded_key(), reason="no unencoded key present in env")
def test_gcp_un_encoded():
    """ensure INPUT_SERVICE_ACCOUNT_KEY_JSON envvar exists in order to activate test"""
    service_account_json = os.getenv("INPUT_SERVICE_ACCOUNT_KEY_JSON")

    service_account_json = service_account_json.replace(os.linesep, "")
    g = Gcp(service_account_json)
