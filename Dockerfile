# A Github Action Dockerfile has some requirements that needs to be followed
# https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# TLDR; no WORKDIR, must run as USER root
FROM python:3.9-slim as python

ARG POETRY_VERSION='1.1.6'

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
    && apt-get clean

ENV GITHUB_WORKSPACE '/github/workspace/'

RUN mkdir -p $GITHUB_WORKSPACE /app

ENV PYTHONPATH /app/

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
ENV POETRY_VERSION=$POETRY_VERSION

# Separate dependencies from the rest of the app to
# take advantage of cached builds
COPY pyproject.toml poetry.lock poetry.toml /app/

# When using image as devcontainer have the option to install dev dependencies
ARG POETRY_INSTALL_ARGS='--no-dev'

RUN set -e \
    && cd /app \
    && pip install poetry==$POETRY_VERSION \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi $POETRY_INSTALL_ARGS \
    && cd ..

COPY velo_action/ /app/velo_action/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
