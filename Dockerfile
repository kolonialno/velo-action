# A Github Action Dockerfile has some requirements that needs to be followed
# https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# TLDR; no WORKDIR, must run as USER root
FROM python:3.9 as python

ARG OCTOPUSCLI_VERSION='7.4.3256'
ARG GITVERSION='5.6.7'
ARG POETRY_VERSION='1.1.6'

RUN apt-get update -y \
    && apt-get install --no-install-recommends -y \
        libgssapi-krb5-2 libicu-dev \
        jq \
        gnupg curl ca-certificates apt-transport-https \
    && sh -c "echo deb https://apt.octopus.com/ stable main > /etc/apt/sources.list.d/octopus.com.list" \
    && curl -sSfL https://apt.octopus.com/public.key | apt-key add - \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    && apt-get update -y && apt-get install -y octopuscli=$OCTOPUSCLI_VERSION google-cloud-sdk \
    && apt-get clean

# Install Gitversion
# minimum requirements for GitVersion https://github.com/GitTools/GitVersion/blob/main/src/Docker/linux%20deps.md
RUN wget --quiet https://github.com/GitTools/GitVersion/releases/download/$GITVERSION/gitversion-linux-x64-$GITVERSION.tar.gz \
    && mkdir -p /tmp \
    && tar -xvf gitversion-linux-x64-$GITVERSION.tar.gz -C tmp \
    && chmod +x /tmp/gitversion \
    && mv /tmp/** /usr/local/bin \
    && rm -rf gitversion-linux-x64-$GITVERSION.tar.gz


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
COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock
COPY poetry.toml /app/poetry.toml

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
COPY velo-action.sh /velo-action.sh

RUN chmod +x /entrypoint.sh /velo-action.sh
ENTRYPOINT ["/entrypoint.sh"]
