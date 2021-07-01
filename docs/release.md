# Release

A release must be performed manually since the CI workflow is dependant on the velo action itself.

1. `make version`
2. Export the version to release. Usually +1 compared to above `export VERSION=<>`
3. `make image`
4. `docker tag odacom/velo-action:latest odacom/velo-action:$VERSION`
5. `make push`
6. Manually create a release in Github.
