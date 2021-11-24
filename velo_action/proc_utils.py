import logging
import os
import re
import subprocess
import sys
from functools import lru_cache

logger = logging.getLogger(name="proc_utils")


@lru_cache()
def re_compile_ansi_escape():
    return re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def ansi_escape_string(input_str):
    ansi_escape = re_compile_ansi_escape()
    return ansi_escape.sub("", input_str)


def execute_process(
    cmd,
    env_vars=None,
    fail_on_non_zero_exit=True,
    log_cmd=True,
    log_envvars=False,
    log_stdout=True,
    forward_stdout=False,
    log_stderr=True,
    cwd=None,
    ansi_escape_loglines=True,
):
    if not env_vars:
        env_vars = {}
    proc_env_vars = os.environ.copy()
    proc_env_vars = {**proc_env_vars, **env_vars}
    if log_cmd:
        print(f"\tRunning '{cmd}'")
    if log_envvars:
        print("\tenvvars")
        print(f"\t{proc_env_vars}")

    if forward_stdout:
        proc_stdout = sys.stdout
    else:
        proc_stdout = subprocess.PIPE
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=proc_stdout,
        stderr=proc_stdout,
        env=proc_env_vars,
        cwd=cwd,
    )
    line_out = []
    with process.stdout:
        for line in iter(process.stdout.readline, b""):
            line_out.append(line)
    process.wait()
    out = []
    if not forward_stdout:
        for item in line_out:
            item_formatted = item.decode().replace("\n", "")
            out.append(item_formatted)
        for item in out:
            if log_stdout:
                print(f"\t{ansi_escape_string(item)}")

    if process.returncode != 0:
        print(f"\tProcess exited with return code {process.returncode}")
        if not forward_stdout:
            if log_stderr:
                logger.error(process.stderr.read())
        if fail_on_non_zero_exit:
            raise ValueError(
                f"Process exited with code {process.returncode}. "
                "Check logs for details."
            )
    return out
