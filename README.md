# Velo action

This actions generates a semantic version using [GitVersion](https://gitversion.net/docs/) and triggers a deploy to [Octopus Deploy](https://octopusdeploy.prod.nube.tech/app#/Spaces-1).

This action does the following:

- Generate gitversion > appversion.json
  generate releasenotes.md
  generate appversion.txt
- build and push image (support multiarch builds)
- upload files to velo bucket
- trigger octo deploy-release

## Usage

```yaml
- uses: kolonialno/velo-action
  with:
    # Use VERSION or DEPLOY.
    # VERSION will generate a gitversion string and output this for the docker build step.
    # Deploy will save artifacts in the nube-velo-prod-deploy-artifacts bucket and trigger a depoy in Octopus deploy.
    mode: ''

    # Octopus Deploy project to target when creating a release and deploying it.
    # The project must exist at https://octopusdeploy.prod.nube.tech/app#/Spaces-1
    project: ''

    # A Google Service account key to use for authentication. This should be the JSON
    # formatted private key which can be exported from the Cloud Console.
    service_account_key: '${{ secrets.VELO_CI_KEY }}'

    # URL to the Octopus Deploy Server
    # Default: "https://octopusdeploy.prod.nube.tech"
    octopus_cli_server: '${{ secrets.VELO_CI_OCTOPUS_URL }}'

    # Octpous deploy server API key. The API key is a Github Secret, can be used as
    # octopus_cli_api_key: ${{ secrets.VELO_CI_OCTOPUS_API_KEY }}
    octopus_cli_api_key: '${{ secrets.VELO_CI_OCTOPUS_API_KEY }}'
```
<!-- end usage -->

## Scenarios

- [Generate version, build image and deploy a release](#Fetch-all-history-for-all-tags-and-branches)

### Generate version, build image and deploy a release

```yaml
...
steps:
  - uses: actions/checkout@v2

  - name: Velo Version
    id: velo_version
    uses: kolonialno/velo-action
    with:
      mode: VERSION

  - uses: google-github-actions/setup-gcloud@v0.2.0
    with:
      service_account_key: ${{ secrets.VELO_CI_KEY }}
      project_id: nube-velo-prod
      export_default_credentials: true

  - run: gcloud auth configure-docker -q
  - run: |
      docker build -t eu.gcr.io/nube-hub/velo-action:${{ steps.velo_version.outputs.version }} -t eu.gcr.io/nube-hub/velo-action:latest .

      docker push eu.gcr.io/nube-hub/velo-action:${{ steps.velo_version.outputs.version }} eu.gcr.io/nube-hub/velo-action:latest

  - name: Velo Deploy
    id: velo_deploy
    uses: kolonialno/velo-action@main
    with:
      mode: DEPLOY
      octopus_cli_server: ${{ secrets.VELO_CI_OCTOPUS_URL }}
      octopus_cli_api_key: ${{ secrets.VELO_CI_OCTOPUS_API_KEY }}
      service_account_key: ${{ secrets.VELO_CI_KEY }}
...
```

## Debugging

Test the action locally using act

```bash
act -j deploy_local
```

***NOTE:*** The velo `action.yml` is located in the `.github/actions/velo` folder to make local debugging with act possible. When not in this folder structure act can auto generate the image name `act-github-actions-velo:latest` and fails.
