# Release

A release of Velo-action consist of to components:
- velo-action docker image
- a github release, based on a tagged commit

In `action.yml` at `runs.image` you have to specify the correct image version.

The problem is that for the next commit after a release we want  `runs.image: Dockerfile` to ensure the action uses builds the latest image, and verifies it.

If for instance `runs.image: odacom/velo-action:latest` then the current commit of the velo-action would actually test the previous commit, which is tagged as latest.

A release therfore includes the following steps:


1. These steps can be run from any branch. But take notics that the version generated from the main branch in in the format `x.x.x`, without any branch name. 
   Its easies to run these steps from the main branch. 

1. Update the `runs.image` field in `action.yml` to use a pinned docker image in a public registry. Currently we are using DockerHub where we have a organization named `odacom`. 
   The `image tag` must be set to
   
   ```bash
   gitversion /showvariable SemVer
   ```

   The `action.yml` should look something like this

    ```yaml
    ...
    runs:
        using: docker
        image: docker://odacom/velo-action:x.x.x  # example 0.2.14
    ...
    ```

1. Build the image

    ```bash
    docker build -t odacom/velo-action:$(gitversion /showvariable SemVer) .
    docker push odacom/velo-action:$(gitversion /showvariable SemVer)
    ```

    ***NOTE***: Credentials for the DockerHub repo odacom can be found in [1Password](https://tienda.1password.com/signin), `DevOps` vault, with the name `velo-action (dockerhub)`. 
    Authenticate as the `velo-action` user by running `docker login`.

1. Update the `changelog.md` with the changes for this release.

1. Commit the `action.yml` anb `changelog.md` files and push the commit to the `main` branch.

7. Manually create a release in Github, on the commit you just pushed.
   The relese will add a tag to the commit.
   Tag with a `v` prefix. Example `v0.2.14`. This shall be the same version as the docker image pushed to odacom.
   Add the entry you made in `changelog.md` to the release description.

8. Revert the changes to enable debugging on the next apps.
   Change the `runs.image` field in `action.yml` back to `Dockerfile``.
   This makes the future commits build the image before running the action, ensuring the latest version is tested.

    ```yaml
    ...
    runs:
        using: docker
        image: Dockerfile
    ...
    ```
