# Changelog

## v0.5.0

Breaking changes:

- Input: `project` removed.

  Velo-action will now read the Octopus Project from the AppSpec `app.yml` file as described in the [Velo docs](https://centro.prod.nube.tech/docs/default/component/velo/app-spec/#project).

  Example:

  ```yml
  # .deploy/app.yml
  ...
  project: <project_name>
  vars:
    ...
  ```

- Velo version field in the AppSpec is now required

  Previously each release created would use the latest released Velo verison. This resulted in little transparency to the end-users a lot of errors when new Velo verison where deployed.

  You could suddenly have an error from a new Velo release, without you knowing about it.

  To solve this **you must now explicitly** set the Velo version in the AppSpec.

  The `velo_version` uses the [python-semanticversion SimpleSpec](https://python-semanticversion.readthedocs.io/en/latest/reference.html#semantic_version.SimpleSpec) format to resolve the version.

  From [python-semanticversion spesifications](https://python-semanticversion.readthedocs.io/en/latest/reference.html#version-specifications-the-spec-class)

  > The [SemVer](https://semver.org/) specification doesn’t provide a standard description of version ranges. And simply using a naive implementation leads to unexpected situations: >=1.2.0,<1.3.0 isn’t expected to match version 1.3.0-rc.1, yet a strict application of [SemVer](https://semver.org/) precedence rules would include it.
  > In order to solve this problem, each SemVer-based package management platform has designed its own rules.

  Example:

  ```yml
  # .deploy/app.yml
  ...
  velo_verison: '>0.4,<0.5'
  vars:
    ...
  ```

  ```yml
  # .deploy/app.yml
  ...
  velo_verison: '0.4.38
  vars:
    ...
  ```

## v0.4.0 (2022-02-01)

Breaking changes:

- action input `octopus_cli_api_key_secret` is renamed to `octopus_api_key_secret`
- action input `octopus_cli_server_secret` is renamed to `octopus_server_secret`

Please update your GitHub workflows where needed.

Features:

- New input `wait_for_success_seconds` to specify that the action waits until Octopus Deploy is finished.
  Deprecates the input `wait_for_deployment`

Other:

- Interact with Octopus Deploy using the API. The Octo CLI is no longer part of the container.

## v0.3.0 (2021-12-22)

- Remove generation of semantic version numbers (SemVer). Default is now the shortened git
  hash (`git rev-parse --short HEAD`). Removes although the gitversion dependency. Please see
  [this example](https://github.com/kolonialno/velo/blob/c3d5ddff650fd97357b72ef178d93e5519eb5efa/.github/workflows/ci.yml#L71-L114)
  if you still want to auto-generate the SemVer.

  NOTE: The length of the version string is dynamic. It can be longer if it is not unique.

## v0.2.79 (2021-12-17)

- Use `subprocess.run()` when calling the octo CLI

## v0.2.21 (2021-09-23)

- Moved image to the new [public Artifact Registry](https://console.cloud.google.com/artifacts/docker/nube-artifacts-prod/europe/nube-container-images-public?project=nube-artifacts-prod) in Google Cloud Platform. Will deprecate the Dockerhub image when there have been no pull for a month. This change require no changes by the user.

- Use python slim image, reduce image size from 1.8GB to 1.14GB.

## v0.2.14 (2021-08-10)

- Add argument `wait_for_deployment`. This will cause the action to wait until Octopus Deploy finished the deployment. The action will fail if the deploy failes.

- Add argument `progress`. This will show progress of the deployment in Octopus Deploy. In other words a more verbose logs from Octopus Deploy

- Refactored the argument parser

## v0.2.6 (2021-06-30)

- Initial release. Velo-action allows Github Action Workflows to generate a semantic versioning using [GitVersion](https://gitversion.net/), create an imutable relese using Velo and trigger a deploy of that relese in Octopus Deploy.
