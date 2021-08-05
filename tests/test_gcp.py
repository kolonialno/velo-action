import os
from velo_action.gcp import Gcp
import pytest


@pytest.mark.skip("manually activate")
def test_gcp_encoded():
    """paste in a base64-encoded service account json here to test"""
    g = Gcp('')


@pytest.mark.skip("manually activate")
def test_gcp_un_encoded():
    """paste in a regular json-formatted service account string (no encoding) here to test:"""
    service_account_json = ""

    service_account_json = service_account_json.replace(os.linesep, "")
    g = Gcp(service_account_json)
