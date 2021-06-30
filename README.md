# Velo action

This actions generates a semantic version using [GitVersion](https://gitversion.net/docs/) and triggers a deploy to Octopus Deploy.

This repo is public since Github actions does not yet [support actions in private repos](https://github.com/github/roadmap/issues/74).

Documentation on usage can be found in [Velo-infra](https://github.com/kolonialno/velo-infra).

## Release

A release must be performed manually since the CI workflow is dependant on the velo action itself.

1. `make version`
2. Export the version to release. Usually +1 compared to above `export VERSION=<>`
3. `make image`
4. `docker tag odacom/velo-action:latest odacom/velo-action:$VERSION`
5. `make push`
6. Manually create a release in Github.
