# Release

## Create a new release

A release of Velo-action consists of to components

- velo-action docker image
- a GitHub release

The version of the action is determined by the release tag. It is used when
referencing the action in a workflow yaml. The container image is tagged
using a shortened commit hash.

To create a new release of velo-action follow the steps below

1. These steps must be run from the default branch, which is `main`. Make sure
   you committed and pushed your changes before proceeding.

2. Build and push the image by running

   ```shell
   make image
   make push
   ```

3. Update the field `runs.image` in the `action.yml` file. Replace the tag
   with the shortened hash of the commit (`make image_tag`).

   We are using [GCP artifacts](https://console.cloud.google.com/artifacts/docker/nube-artifacts-prod/europe/nube-container-images-public?project=nube-artifacts-prod).

   The `action.yml` should look something like this

   ```yaml
   ...
   runs:
     using: docker
     image: docker://europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:1234567
   ...
   ```

4. Determine the version of the next Release.

   **NOTE:** This is done manually for the moment. A version should be generated automatically
   in the future.

5. Update the `changelog.md` with the changes for this release.

6. Commit the `action.yml` and the `changelog.md` files and push the commit to the `main` branch.

7. Manually [create a release in Github](https://github.com/kolonialno/velo-action/releases), on
   the commit you just pushed.

   Tag the release commit with the new version using a `v` prefix.

   Example `v0.2.14`.

   Add the entry you made in `changelog.md` to the release description.
