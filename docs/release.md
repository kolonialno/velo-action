# Release

A release of Velo-action consists of to components

- velo-action docker image
- a github release

To create a new release of velo-action follow the steps below

1. These steps must be run from the default branch, which is `main`.
   The version generated from the main branch is in the format `x.x.x`.

2. Update the field `runs.image` in the `action.yml` file.
   The field determines what image the action will use.
   The action must be in a [public repository](https://github.com/github/roadmap/issues/74) and the image in a public image registry.

   Currently we are using [DockerHub](https://hub.docker.com/repository/docker/odacom/velo-action) where we have an organization named `odacom`.

   The `action.yml` should look something like this

    ```yaml
    ...
    runs:
        using: docker
        image: docker://odacom/velo-action:x.x.x  # example 0.2.14
    ...
    ```

    where the version `x.x.x` must be replaced with the result of (on the main branch)

    ```bash
    gitversion /showvariable SemVer
    ```

3. Build and push the image by running

    ```bash
    docker build -t odacom/velo-action:$(gitversion /showvariable SemVer) .
    docker push odacom/velo-action:$(gitversion /showvariable SemVer)
    ```

    ***NOTE***: Credentials for the DockerHub repo odacom can be found in [1Password](https://tienda.1password.com/signin), `DevOps` vault, with the name `velo-action (dockerhub)`.

    Authenticate as the `velo-action` user by running `docker login`, and supplying the username and password.

4. Update the `changelog.md` with the changes for this release.

5. Commit the `action.yml` and the `changelog.md` files and push the commit to the `main` branch.

6. Manually [create a release in Github](https://github.com/kolonialno/velo-action/releases), on the commit you just pushed.

   Tag the release commit with the same version as the image.

   Prefix a `v` in front of the semantic version.

   Example `v0.2.14`.

   Add the entry you made in `changelog.md` to the release description.

7. Revert the changes to enable debugging on the next apps.

   Change the `runs.image` field in `action.yml` back to `Dockerfile`.

   This makes the future commits build the image before running the action, ensuring the latest version is tested.

    ```yaml
    ...
    runs:
        using: docker
        image: Dockerfile
    ...
    ```
