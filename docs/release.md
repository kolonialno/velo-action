# Release

A release of Velo-action consist of to components:
- velo-action docker image
- a github release, based on a tagged commit

In `action.yml` at `runs.image` you have to specify the correct image version.

The problem is that for the next commit after a release we want  `runs.image: Dockerfile` to ensure the action uses builds the latest image, and verifies it.

If for instance `runs.image: odacom/velo-action:latest` then the current commit of the velo-action would actually test the previous commit, which is tagged as latest.

A release therfore includes the following steps:


1. Get the current version
    ```bash
    gitversion /showvariable SemVer
    ```

1. Update the `runs.image` field in `action.yml` to the current version +1. Since the commit with the update increments the version by 1.
    Should look something like this

    ```yaml
    ...
    runs:
        using: docker
        image: odacom/velo-action:0.2.14
    ...
    ```

2.  Commit `action.yml` file, but do not push.

4. Build the image locally and push to registry

    ```bash
    docker build -t odacom/velo-action:$(gitversion /showvariable SemVer) .
    docker push odacom/velo-action:$(gitversion /showvariable SemVer)
    ```

5. Push the commit. Now the image set in `action.yml` in the commit above exists, such that the github action CI will run.

6. Update the `changelog.md`

7. Manually create a release in Github, on the commit you just pushed.
   The relese will add a tag to the commit.
   Tag with a `v` prefix. Example `vx.x.x`.
   Add a description of changes. Same as from the changelog.

8. Change the `runs.image` field in `action.yml` back to Dockerfile. This makes the future commits build the image before running the action, ensuring the latest version is tested.

    ```yaml
    ...
    runs:
        using: docker
        image: Dockerfile
    ...
    ```
