## velo-action Development

Velo-action is a small Python project that mainly runs within GitHub workflows from
a container. For development and testing it can be executed locally.

Prerequisites
* Python 3.9+
* [poetry](https://python-poetry.org/docs/)

## Local execution

[The Makefile](../Makefile) covers the most common commands you need. For testing
you should checkout the
[example-deploy-project](https://github.com/kolonialno/example-deploy-project/)
to have a working deployable application.

 1. Setup dependencies and virtual env: `make install`
 2. All configuration os done via [development variables](../env.dev-vars). It
    should be easy to integrate this env-file into your IDE as well

To get the same results as the productive action, you need access to the secrets
in the `nube-velo-prod` GCP project. This can be easily achieved by elevating your
existing permissions using [klipy](https://github.com/kolonialno/klipy).

```
klipy power elevate --group nube.project.editor.nube-velo-prod
```

Now you can execute velo-action using `make run`.

In order to use the containerized build, use `make run_docker`.

## Push and release

You can perform test with `make tests` and linters with `make lint` before you
push changes. Please follow the [release process](./release.md)
