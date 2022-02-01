import subprocess


def generate_version() -> str:
    """Version used to generate release and tag image.
    Defaults to the shortened git hash (`git rev-parse --short HEAD`).

    The length of the Git hash is dynamic.
    Minimum length is 7 characters.
    It can be longer if it is not unique.
    """
    result = subprocess.run(
        ["git rev-parse --short HEAD"],
        shell=True,
        capture_output=True,
        check=True,
    )
    version = result.stdout.decode(encoding="utf-8").rstrip()
    return version
