import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
from opentelemetry.sdk.trace import TracerProvider  # type: ignore
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter  # type: ignore

from velo_action.settings import GithubSettings
from velo_action.tracing_helpers import construct_github_action_trace


def gh_token():
    if token := os.environ.get("GITHUB_TOKEN"):
        return token
    try:
        result = subprocess.run(
            ["gh", "auth", "status", "-t"], capture_output=True, text=True, check=True
        )
        return re.search(r"Token: (.*)\n", result.stderr).group(1)
    except Exception:
        return None


has_token = pytest.mark.skipif(not bool(gh_token()), reason="No Github token found")



class SpanList:
    def __init__(self):
        self.found_string_spans = []

    def write(self, span):
        span = json.loads(span)

        del span['context']['trace_id']
        del span['context']['span_id']
        del span['parent_id']

        if span['name'] == 'build and deploy':
            del span['end_time']  # Disregard because of dynamic end_time

        self.found_string_spans.append(json.dumps(span))

    @staticmethod
    def flush():
        print('flushed the toilet')


@has_token
def test_trace_creation():
    """
    This can also be done by setting the variables in env.dev-vars to something like this:

    INPUT_TOKEN=  Copy token from output of `gh auth status -t` uses GH cli
    INPUT_PRECEDING_RUN_IDS=

    # GitHub settings
    GITHUB_WORKSPACE=example-deploy-project
    GITHUB_SHA=519b2d7c3be0f251bac6593910d22d468f65f597
    GITHUB_REF_NAME=roald/test-new-velo-action
    GITHUB_SERVER_URL=https://github.com
    GITHUB_REPOSITORY=kolonialno/example-deploy-project
    GITHUB_ACTOR=rmstorm
    GITHUB_API_URL=https://api.github.com
    GITHUB_RUN_ID=2487831087
    GITHUB_WORKFLOW=CI
    """

    workspace = "example-deploy-project"
    repo = f"kolonialno/{workspace}"
    actor = "someone-awesome"

    tracing_attributes = {
        "build.repository": workspace,
        "build.actor": actor,
    }
    resource = Resource(attributes={SERVICE_NAME: "velo-action", **tracing_attributes})
    trace.set_tracer_provider(TracerProvider(resource=resource))

    span_list = SpanList()
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(ConsoleSpanExporter(out=span_list)))

    tracer = trace.get_tracer(__name__)

    gh_settings = GithubSettings(
        workspace=workspace,
        sha="519b2d7c3be0f251bac6593910d22d468f65f597",
        ref_name="roald/test-new-velo-action",
        server_url="https://github.com",
        repository=repo,
        actor=actor,
        api_url="https://api.github.com",
        run_id="2487831087",
        workflow="CI"
    )

    construct_github_action_trace(
        tracer,
        gh_token(),
        "",
        github_settings=gh_settings,
    )

    assert tracer.span_processor.force_flush()

    with (Path(__file__).parent / "action_trace_output.json").open('r') as f:
        required_spans = json.load(f)

    for span in required_spans:
        del span['context']['trace_id']
        del span['context']['span_id']
        del span['parent_id']

        if span['name'] == 'build and deploy':
            del span['end_time']  # Disregard because of dynamic end_time

        span_list.found_string_spans.remove(json.dumps(span))

    assert span_list.found_string_spans == []
