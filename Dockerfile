# A Github Action Dockerfile has some requirements that needs to be followed
# https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# TLDR; no WORKDIR, must run as USER root
ARG OCTOPUSCLI_VERSION='7.4.2' a

FROM octopusdeploy/octo:7.4.2 as octopuscli


FROM python:3.9-alpine as python

ARG GITVERSION='5.6.7'
ARG POETRY_VERSION='1.1.6'
ARG GOOGLE_CLOUD_SDK_VERSION='355.0.0'

RUN apk add --no-cache \
        wget \
        curl \
        jq \
        gnupg \
        ca-certificates

RUN apk add  

COPY --from=octopuscli /usr/bin/octo /usr/bin/octo
RUN chmod +x /usr/bin/octo

ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT false
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8


wget --quiet https://github.com/OctopusDeploy/OctopusCLI/archive/refs/tags/7.4.2.tar.gz
tar -xvf 7.4.2.tar.gz -C tmp

RUN wget --quiet https://github.com/OctopusDeploy/OctopusCLI/archive/refs/tags/$OCTOPUSCLI_VERSION.tar.gz \
    && mkdir -p /tmp \
    && tar -xvf $OCTOPUSCLI_VERSION.tar.gz -C tmp \
    && chmod +x /tmp/OctopusCLI-$OCTOPUSCLI_VERSION \
    && mv /tmp/** /usr/local/bin \
    && rm -rf gitversion-linux-x64-$GITVERSION.tar.gz

# Install Google Cloud SDK
RUN apk add --no-cache bash
RUN wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-$GOOGLE_CLOUD_SDK_VERSION-linux-x86_64.tar.gz \
    -O /tmp/google-cloud-sdk.tar.gz | bash

RUN mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -xvzf /tmp/google-cloud-sdk.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh -q

# Install Gitversion
# minimum requirements for GitVersion https://github.com/GitTools/GitVersion/blob/main/src/Docker/linux%20deps.md
RUN wget --quiet https://github.com/GitTools/GitVersion/releases/download/$GITVERSION/gitversion-linux-x64-$GITVERSION.tar.gz \
    && mkdir -p /tmp \
    && tar -xvf gitversion-linux-x64-$GITVERSION.tar.gz -C tmp \
    && chmod +x /tmp/gitversion \
    && mv /tmp/** /usr/local/bin \
    && rm -rf gitversion-linux-x64-$GITVERSION.tar.gz

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

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

RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
