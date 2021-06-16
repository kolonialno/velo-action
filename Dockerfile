# A Github Action Dockerfile has some requirements that needs to be followed
# https://docs.github.com/en/actions/creating-actions/dockerfile-support-for-github-actions
# TLDR; no WORKDIR, must run as USER root

FROM python:3.9 as python

# The enviroment variable ensures that the python output is set straight
# to the terminal with out buffering it first
ENV PYTHONUNBUFFERED 1

ARG GITVERSION=5.6.7

# Install Gitversion
# inimum requirements for GitVersion https://github.com/GitTools/GitVersion/blob/main/src/Docker/linux%20deps.md
RUN apt-get update -y \
    && apt-get install -y libgssapi-krb5-2 libicu-dev \
    && apt-get clean

RUN wget https://github.com/GitTools/GitVersion/releases/download/$GITVERSION/gitversion-linux-x64-$GITVERSION.tar.gz \
    && mkdir -p /tmp \
    && tar -xvf gitversion-linux-x64-$GITVERSION.tar.gz -C tmp \
    && chmod +x /tmp/gitversion \
    && mv /tmp/** /usr/local/bin \
    && rm -rf gitversion-linux-x64-$GITVERSION .tar.gz

# Required system packages
COPY .tool-versions .
RUN set -e \
    && pip install --no-cache poetry=="$(grep poetry .tool-versions | cut -d' ' -f2)"

# Separate dependencies from the rest of the app to
# take advantage of cached builds
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
COPY poetry.toml poetry.toml

RUN set -e \
    && poetry config virtualenvs.in-project \
    && poetry install --no-interaction --no-ansi --no-dev

COPY velo-action/** /
COPY entrypoint.sh entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
