<h1 align="center">
  🚲 <br>
  Velo-action
</h1>

<p align="center">
  A GitHub Action to create releases and trigger deployments
</p>

This GitHub actions is part of the Velo deploy system at Oda.

This repo is public since GitHub actions does not yet
[support actions in private repos](https://github.com/github/roadmap/issues/74).

## Local execution

[The Makefile](../Makefile) covers the most common commands you need. For testing,
you should check out the [example-deploy-project](https://github.com/kolonialno/example-deploy-project/) to have a working deployable application.

 1. Setup dependencies and virtual env: `make install`
 2. All configuration os done via [development variables](../env.dev-vars). It
    should be easy to integrate this env-file into your IDE as well

Now you can execute velo-action using `make run`.

In order to use the containerized build, use `make run_docker`.

## Test a pre-release

1. Create a PR.
2. Update the `velo-action` Github action release version to the commit you want to test.

    ```yaml
   - name: Use Velo-action
    uses: kolonialno/velo-action@<commit>
    with:
      service_account_key: ${{ secrets.VELO_ACTION_GSA_KEY_PROD_PUBLIC }}
      ...
    ```

## Create a release

A new draft [Github release of Velo-action](https://github.com/kolonialno/velo-action/releases) is created on every merge to main.

Manually convert the release from a draft to a release to [release it](https://github.com/kolonialno/velo-action/releases).

1. Determine the version of the current release by running `make verison`.
   Bump version if nececary according [SevVer](https://semver.org/) by adding this to the commit message (the PR commits are squashed)

   - `+semver: major`
   - `+semver: minor`

2. Update the `changelog.md` with the changes for this release and the uppcomming verison.

A release will create a Dependabot PR in all repost using it.
