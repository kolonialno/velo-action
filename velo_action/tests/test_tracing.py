import os

import pytest

from velo_action.tracing_helpers import init_tracer


def test_init_tracer_without_service_account_key_raise_error():
    os.unsetenv("OTEL_TEMPO_PASSWORD")
    with pytest.raises(ValueError):
        init_tracer(service_acc_key=None, service="velo-action")
