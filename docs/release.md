# Release


A release of Velo-action consist of to components:
- velo-action docker image
- a github release, based on a tagged commit

In `action.yml` at `runs.image` you have to specify the correct image version.

The problem is that for the next commit after a release we want  `runs.image: Dockerfile` to ensure the action uses builds the latest image, and verifies it.

If for instance `runs.image: odacom/velo-action:latest` then the current commit of the velo-action would actually test the previous commit, which is tagged as latest.

A release therfore includes the following steps:

1. `make version`
2. Export the version as env var, adding +1 to the version. To accomodate for the next commit with the tagged version.

    ```bash
    export VERSION=""
    ```

3. `make image`
4. `docker tag odacom/velo-action:latest odacom/velo-action:$VERSION`
5. `docker push odacom/velo-action:$VERSION`
6. Commit `action.yml` file and push to repo.
7. Manually create a release in Github, on the commit you just pushed.
