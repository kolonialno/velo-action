import datetime as dt
import logging
import os
import time

import opentracing
import requests
from jaeger_client import Config


def init_tracer(service="velo-action"):
    root_logger_level = logging.getLogger().getEffectiveLevel()
    jaeger_logger = logging.getLogger("jaeger_tracing")
    # Set the trace logging to DEBUG if root level is lower then INFO
    jaeger_logger.setLevel(logging.DEBUG if root_logger_level <= 5 else logging.WARNING)

    config = Config(
        config={
            "sampler": {
                "type": "const",
                "param": 1,
            },
            "logging": True,
        },
        service_name=service,
    )

    # this call also sets opentracing.tracer
    tracer = config.initialize_tracer()
    if tracer is None:
        return opentracing.global_tracer()
    else:
        return tracer


def print_trace_link(span):
    trace_host = "https://grafana.infra.nube.tech"
    # Use this locally together with docker-compose in the velo-tracing directory
    trace_host = "http://localhost:3000"
    print(
        f"---\nSee trace at:\n{trace_host}/explore?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Tem"
        f"po%22,%7B%22queryType%22:%22traceId%22,%22query%22:%22{span.trace_id:x}%22%7D%5D\n---"
    )


def convert_time(input_time):
    return dt.datetime.fromisoformat(input_time.replace("Z", "+00:00")).timestamp()


def trace_jobs(tracer, wf_span, wf_jobs):
    start_times = []
    end_times = []

    for job in wf_jobs["jobs"]:
        with tracer.start_span(job["name"], child_of=wf_span) as job_span:
            for step in job["steps"]:
                with tracer.start_span(step["name"], child_of=job_span) as step_span:
                    if step["started_at"]:
                        step_span.start_time = convert_time(step["started_at"])
                if step["completed_at"]:
                    step_span.end_time = convert_time(step["completed_at"])

        if job["started_at"]:
            span_start = convert_time(job["started_at"])
            job_span.start_time = span_start
            start_times.append(span_start)

        if job["completed_at"]:
            span_end = convert_time(job["completed_at"])
            job_span.end_time = span_end
            end_times.append(span_end)

    return min(start_times), max(end_times)


def construct_github_action_trace(tracer):
    if os.environ.get('TOKEN') is None:
        return 'None'
    headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_id = os.environ.get("PRECEDING_RUN_ID", "")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs"
    current_wf_url = f"{base_url}/{gh_run_id}/jobs"
    preceding_wf_url = f"{base_url}/{gh_preceding_run_id}/jobs"

    r = requests.get(current_wf_url, headers=headers)
    r.raise_for_status()
    actual_wf_jobs = r.json()

    if gh_preceding_run_id:
        r = requests.get(preceding_wf_url, headers=headers)
        r.raise_for_status()
        preceding_wf_jobs = r.json()

        preceding_wf_name = n if (n := os.environ.get("PRECEDING_RUN_ID", "")) else "CI"
        total_action_dict = {
            preceding_wf_name: preceding_wf_jobs,
            os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs,
        }
    else:
        total_action_dict = {os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs}

    start_times = []
    with tracer.start_span("In velo-action span start") as span:
        for wf_name, wf_jobs in total_action_dict.items():
            with tracer.start_span(wf_name, child_of=span) as wf_span:
                wf_start_time, wf_end_time = trace_jobs(tracer, wf_span, wf_jobs)
            wf_span.start_time = wf_start_time
            start_times.append(wf_start_time)
            wf_span.end_time = wf_end_time
    span.start_time = min(start_times) - 0.1
    return span


def start_trace() -> str:
    tracer = init_tracer(service="velo-action")
    span = construct_github_action_trace(tracer)

    time.sleep(2)
    tracer.close()
    print_trace_link(span)
    return str(span).split()[0]
