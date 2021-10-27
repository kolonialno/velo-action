import base64
import datetime as dt
import logging
import os

import requests
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_span_in_context
import gcp

logger = logging.getLogger(name="action")


def init_tracer(g: gcp.Gcp, service="velo-action"):
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: service}))
    )
    password = g.lookup_data("tempo-basic-auth-password", "nube-observability-prod")
    basic_header = base64.b64encode(f"tempo:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {basic_header}"}
    otlp_exporter = OTLPSpanExporter(
        endpoint="https://tempo.infra.nube.tech:443/v1/traces",
        headers=headers,
    )

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    return trace.get_tracer(__name__)


def print_trace_link(span):
    trace_host = "https://grafana.infra.nube.tech"
    # Use this locally together with docker-compose in the velo-tracing directory
    # trace_host = "http://localhost:3000"
    logger.info(
        f"---\nSee trace at:\n{trace_host}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Tem"
        f"po%22,%7B%22queryType%22:%22traceId%22,%22query%22:%22{span.context.trace_id:x}%22%7D%5D\n---"
    )


def convert_time(input_time):
    return (
        round(dt.datetime.fromisoformat(input_time.replace("Z", "+00:00")).timestamp())
        * 1000000000  # required factor for otel span timing nanoseconds I guess?
    )


def trace_jobs(wf_jobs):
    start_times = []
    end_times = []
    job_spans = []

    for job in wf_jobs["jobs"]:
        if job["status"] == "queued":
            continue  # Do not trace jobs that are in the future

        new_job_span = make_empty_span_dict(job["name"])
        if job["started_at"]:
            span_start = convert_time(job["started_at"])
            new_job_span["start"] = span_start
            start_times.append(span_start)

        if job["completed_at"]:
            span_end = convert_time(job["completed_at"])
            new_job_span["end"] = span_end
            end_times.append(span_end)

        for step in job["steps"]:
            new_step_span = {
                "name": step["name"],
                "start": 0,
                "end": 0,
                "sub_spans": [],
            }
            if step["started_at"]:
                new_step_span["start"] = convert_time(step["started_at"])
            if step["completed_at"]:
                new_step_span["end"] = convert_time(step["completed_at"])
            new_job_span["sub_spans"].append(new_step_span)
        job_spans.append(new_job_span)
    end_time = max(end_times) if end_times else 0
    return min(start_times), end_time, job_spans


def recurse_add_spans(tracer, parent_span, sub_span_dict):
    # 0 is falsy so this will take now instead of 0 if the time isn't set
    span = tracer.start_span(
        sub_span_dict["name"],
        start_time=sub_span_dict["start"] or None,
        context=set_span_in_context(parent_span),
    )
    sub_span_dict["span"] = span
    for span_dict in sub_span_dict["sub_spans"]:
        recurse_add_spans(tracer, span, span_dict)
    span.end(sub_span_dict["end"] or None)


def request_github_wf_data():
    github_headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_id = os.environ.get("PRECEDING_RUN_ID", "")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs"
    current_wf_url = f"{base_url}/{gh_run_id}/jobs"
    preceding_wf_url = f"{base_url}/{gh_preceding_run_id}/jobs"

    r = requests.get(current_wf_url, headers=github_headers)
    r.raise_for_status()
    actual_wf_jobs = r.json()

    if gh_preceding_run_id:
        r = requests.get(preceding_wf_url, headers=github_headers)
        r.raise_for_status()
        preceding_wf_jobs = r.json()

        preceding_wf_name = (
            n if (n := os.environ.get("PRECEDING_RUN_NAME", "")) else "CI"
        )
        total_action_dict = {
            preceding_wf_name: preceding_wf_jobs,
            os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs,
        }
    else:
        total_action_dict = {os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs}
    return total_action_dict


def make_empty_span_dict(name, start=0, end=0, sub_spans=None, span=None):
    return {
        "name": name,
        "start": start,
        "end": end,
        "sub_spans": sub_spans if sub_spans is not None else [],
        "span": span,
    }


def stringify_span(span):
    return f"{span.context.trace_id:x}:{span.context.span_id:x}:0:{span.context.trace_flags:x}"


def construct_github_action_trace(tracer):
    if os.environ.get("TOKEN") is None:
        logger.info("No github token found to inspect workflows.. Skipping trace!")
        return None

    total_action_dict = request_github_wf_data()

    wf_start_times = []
    span_dict = make_empty_span_dict("build and deploy")

    for wf_name, wf_jobs in total_action_dict.items():
        wf_start_time, wf_end_time, job_spans = trace_jobs(wf_jobs)
        wf_start_times.append(wf_start_time)
        span_dict["sub_spans"].append(
            make_empty_span_dict(wf_name, wf_start_time, wf_end_time, job_spans)
        )
    span_dict["start"] = min(wf_start_times) - 1

    # Convert dict into actual opentelemetry spans!
    span = tracer.start_span(span_dict["name"], start_time=span_dict["start"])
    span_dict["span"] = span
    for wf_span_dict in span_dict["sub_spans"]:
        recurse_add_spans(tracer, span, wf_span_dict)
        if wf_span_dict["name"] == os.environ["GITHUB_WORKFLOW"]:
            logger.info("Current wf_span:")
            logger.info(stringify_span(wf_span_dict["span"]))
    span.end(span_dict["end"] or None)
    return span


def start_trace(g: gcp.Gcp) -> str:
    tracer = init_tracer(g, service="velo-action")
    span = construct_github_action_trace(tracer)
    if span is None:
        return "None"
    print_trace_link(span)
    return stringify_span(span)
