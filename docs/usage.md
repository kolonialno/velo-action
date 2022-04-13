# Velo-action

This action is part of the Velo deploy tooling.

## Usage

```yaml
- uses: kolonialno/velo-action@v0.4.0
  id: velo
  with:
    # Version used to generate release and tag image. If unspecified, the git short ref is used.
    version: ''

    # Create a release on Octopus Deploy and save artifacts in the Velo Artifacts bucket.
    # If an environment in 'deploy_to_environments' is set, and the release does not exist, one will be created.
    create_release: ''

    # If specified trigger a deployment to the environment.
    # Can be multiple values by separating environment names by a comma. Example 'staging,prod'.
    deploy_to_environments: ''

    # If specified trigger a deploy to the spesified tenants.
    # Can be multiple values by seperating tenant names by a comma. Example 'fc:osl1,fc:rd1'.
    # Will only deploy to environments listed in the 'deploy_to_environments' variable.
    tenants: ''

    # A Google Service account key to use for authentication. This should be the JSON
    # formatted private key which can be exported from the Cloud Console.
    # Use: ${{ secrets.VELO_ACTION_GSA_KEY_PROD }}
    service_account_key: ''
```

### Generate semantic version and use when building images

```yaml
- uses: kolonialno/velo-action@v0.4.0
  id: velo

- run: |
    docker build -t sample-image:${{ steps.velo.outputs.version }} .
```

### Create a release

```yaml
- name: Create release
  uses: kolonialno/velo-action@v0.4.0
  with:
    create_release: 'True'
    service_account_key: ${{ secrets.VELO_ACTION_GSA_KEY_PROD }}

```

### Create a release and deploy to staging

If a release does not exist, one will be created.

```yaml
- name: Deploy release
  uses: kolonialno/velo-action@v0.4.0
  with:
    deploy_to_environments: staging
    service_account_key: ${{ secrets.VELO_ACTION_GSA_KEY_PROD }}
```
