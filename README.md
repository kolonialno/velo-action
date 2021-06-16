# Velo action

This actions generates a semantic version using [GitVersion](https://gitversion.net/docs/) and triggers a deploy to [Octopus Deploy](https://octopusdeploy.prod.nube.tech/app#/Spaces-1).

This action does the following:

- Generate gitversion > appversion.json
  generate releasenotes.md
  generate appversion.txt
- build and push image (support multiarch builds)
- upload files to velo bucket
- trigger octo deploy-release

## Inputs

## `who-to-greet`

**Required** The name of the person to greet. Default `"World"`.

## Outputs

## `time`

The time we greeted you.

## Example usage

uses: kolonialno/velo-action@v1
with:
  who-to-greet: 'Mona the Octocat'

