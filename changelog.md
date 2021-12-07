# Changelog

## DRAFT v0.3.x (2021-12-08)

- Remove generation of semantic version numbers (SemVer). Default is now the shortened git
  hash (`git rev-parse --short HEAD`). Removes although the gitversion dependency.

## v0.2.21 (2021-09-23)

- Moved image to the new [public Artifact Registry](https://console.cloud.google.com/artifacts/docker/nube-artifacts-prod/europe/nube-container-images-public?project=nube-artifacts-prod) in Google Cloud Platform. Will deprecate the Dockerhub image when there have been no pull for a month. This change require no changes by the user.

- Use python slim image, reduce image size from 1.8GB to 1.14GB.

## v0.2.14 (2021-08-10)

- Add argument `wait_for_deployment`. This will cause the action to wait until Octopus Deploy finished the deployment. The action will fail if the deploy failes.

- Add argument `progress`. This will show progress of the deployment in Octopus Deploy. In other words a more verbose logs from Octopus Deploy

- Refactored the argument parser

## v0.2.6 (2021-06-30)

- Initial release. Velo-action allows Github Action Workflows to generate a semantic versioning using [GitVersion](https://gitversion.net/), create an imutable relese using Velo and trigger a deploy of that relese in Octopus Deploy.
