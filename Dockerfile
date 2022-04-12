# A Github Action Dockerfile has some requirements that needs to be followed
# https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# TLDR; no WORKDIR, must run as USER root
ARG PYTHON_VERSION=3.10.2
FROM docker.io/library/python:${PYTHON_VERSION}-slim AS builder

WORKDIR /build

SHELL [ "/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        libgssapi-krb5-2 \
        libicu-dev \
        git \
        jq \
        gnupg \
        curl \
        wget \
        ca-certificates \
        apt-transport-https \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update -y && apt-get install -y google-cloud-sdk \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY .tool-versions .

# Separate dependencies from the rest of the app to
# take advantage of cached builds
COPY pyproject.toml .
COPY poetry.toml .
COPY poetry.lock .

# Install Poetry, as well as the Python wheels, and ignore cache error due to using builder,
# as well as the shellcheck ignore as we do not care about the activation script's contents
# hadolint ignore=DL3042,SC1091
RUN POETRY_VERSION="$(grep poetry .tool-versions | cut -d ' ' -f 2)" \
    && pip install "poetry==${POETRY_VERSION}" \
    && test "$(poetry --version | cut -d ' ' -f 3)" = "$POETRY_VERSION" \
    && python -m venv /app/venv \
    && . /app/venv/bin/activate \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction

# Copy the source code into the project in order for us to build a wheel containing the source code
COPY velo_action/ ./velo_action

# Install Velo-action itself
RUN . /app/venv/bin/activate \
    && poetry build -f wheel \
    && pip install "dist/velo_action-$(poetry version -s)-py3-none-any.whl"

FROM docker.io/library/python:${PYTHON_VERSION}-slim

WORKDIR /app

ENV GITHUB_WORKSPACE '/github/workspace/'
RUN mkdir -p $GITHUB_WORKSPACE /app


COPY --from=builder /app /app
COPY --from=builder /usr/local/bin /usr/local/bin
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV VIRTUAL_ENV /app/venv
ENV PATH "${VIRTUAL_ENV}/bin:${PATH}"
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
ENV GIT_PYTHON_GIT_EXECUTABLE /usr/bin/git

ENTRYPOINT ["/entrypoint.sh"]
