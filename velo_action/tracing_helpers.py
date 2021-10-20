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


def replace_job_span_duration(job, job_span, mint, maxt):
    span_start = convert_time(job["started_at"])
    job_span.start_time = span_start
    mint = mint if span_start > mint else span_start

    span_end = convert_time(job["completed_at"])
    job_span.end_time = span_end
    maxt = maxt if span_end < maxt else span_end
    return mint, maxt


def construct_github_action_trace(tracer):
    headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ["GITHUB_API_URL"]
    gh_repo = os.environ["GITHUB_REPOSITORY"]
    gh_run_id = os.environ["GITHUB_RUN_ID"]
    gh_preceding_run_id = os.environ.get("PRECEDING_RUN_ID")

    base_url = f"{gh_api_url}/repos/{gh_repo}/actions/runs/"
    current_wf_url = f"{base_url}/{gh_run_id}/jobs"
    preceding_wf_url = f"{base_url}/{gh_preceding_run_id}/jobs"

    r = requests.get(current_wf_url, headers=headers)
    r.raise_for_status()
    actual_wf_jobs = r.json()

    if gh_preceding_run_id:
        r = requests.get(preceding_wf_url, headers=headers)
        r.raise_for_status()
        preceding_wf_jobs = r.json()

        total_action_dict = {"CI": preceding_wf_jobs, "Deploy": actual_wf_jobs}
    else:
        total_action_dict = {"Deploy": actual_wf_jobs}

    mint = 0
    maxt = time.time()

    with tracer.start_span("Full Build and Deploy") as span:
        for wf_name, wf_jobs in total_action_dict.items():
            with tracer.start_span(wf_name, child_of=span) as wf_span:
                for job in wf_jobs["jobs"]:
                    with tracer.start_span(job["name"], child_of=wf_span) as job_span:
                        for step in job["steps"]:
                            with tracer.start_span(
                                step["name"], child_of=job_span
                            ) as step_span:
                                step_span.start_time = convert_time(step["started_at"])
                            step_span.end_time = convert_time(step["completed_at"])
                    mint, maxt = replace_job_span_duration(job, job_span, mint, maxt)
            wf_span.start_time = mint
            wf_span.end_time = maxt
        span.start_time = mint
    return span


def start_trace() -> str:
    tracer = init_tracer(service="velo-action")
    span = construct_github_action_trace(tracer)

    time.sleep(2)
    tracer.close()
    print_trace_link(span)
    return str(span).split()[0]
