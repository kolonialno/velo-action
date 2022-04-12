import base64
import datetime as dt
import os
from typing import Any, Optional

import gcp
from loguru import logger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore
    OTLPSpanExporter,
)
from opentelemetry.sdk.resources import SERVICE_NAME, Resource  # type: ignore
from opentelemetry.sdk.trace import TracerProvider  # type: ignore
from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
from opentelemetry.trace import set_span_in_context

from velo_action.github import request_github_workflow_data
from velo_action.settings import GRAFANA_URL, TRACING_URL, GithubSettings


def init_tracer(service_acc_key: Optional[str], service: str) -> TracerProvider:
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: service}))
    )
    if service_acc_key:
        gcloud = gcp.GCP(service_acc_key)
        password = gcloud.lookup_data(
            "tempo-basic-auth-password", "nube-observability-prod"
        )
    else:
        password = os.environ.get("OTEL_TEMPO_PASSWORD", "")

    if not password:
        raise ValueError(
            "OTEL_TEMPO_PASSWORD environment variable not set. Traces cannot be send without password."
        )

    basic_header = base64.b64encode(f"tempo:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {basic_header}"}
    otlp_exporter = OTLPSpanExporter(
        endpoint=TRACING_URL,
        headers=headers,
    )

    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    return trace.get_tracer(__name__)


def print_trace_link(span: Any) -> None:
    trace_host = GRAFANA_URL
    # Use this locally together with docker-compose in the velo-tracing directory
    # trace_host = "http://localhost:3000"
    print(
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


def construct_github_action_trace(
    tracer, token: str, preceding_run_ids: str, github_settings: GithubSettings
) -> Any:

    total_action_dict = request_github_workflow_data(
        token=token,
        preceding_run_ids=preceding_run_ids,
        github_settings=github_settings,
    )

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
        if wf_span_dict["name"] == github_settings.workflow:
            logger.debug(f"Current wf_span: {stringify_span(wf_span_dict['span'])}")
    span.end(span_dict["end"] or None)
    return span
