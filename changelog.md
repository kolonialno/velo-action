# Changelog

## v0.2.14 (2021-08-10)

- Add argument `wait_for_deployment`. This will cause the action to wait until Octopus Deploy finished the deployment. The action will fail if the deploy failes.

- Add argument `progress`. This will show progress of the deployment in Octopus Deploy. In other words a more verbose logs from Octopus Deploy

- Refactored the argument parser

## v0.2.6 (2021-06-30)

- Initial release. Velo-action allows Github Action Workflows to generate a semantic versioning using [GitVersion](https://gitversion.net/), create an imutable relese using Velo and trigger a deploy of that relese in Octopus Deploy.
