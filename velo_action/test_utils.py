def fill_default_envvars(monkeypatch):
    """
    set all envvars so that local .env files won't affect test runs.
    These envvars should correspond to the defaults in `action.yml`
    in order to give a realistic test environment

    """
    monkeypatch.setenv("INPUT_VERSION", "None")
    monkeypatch.setenv("INPUT_WORKSPACE", "None")
    monkeypatch.setenv("INPUT_PROJECT", "None")
    monkeypatch.setenv("INPUT_CREATE_RELEASE", "False")
    monkeypatch.setenv("INPUT_DEPLOY_TO_ENVIRONMENTS", "None")
    monkeypatch.setenv("INPUT_TENANTS", "None")
    monkeypatch.setenv("INPUT_PROGRESS", "False")
    monkeypatch.setenv("INPUT_WAIT_FOR_DEPLOYMENT", "False")
    monkeypatch.setenv("INPUT_SERVICE_ACCOUNT_KEY", "None")
    monkeypatch.setenv("INPUT_PYTHON_LOGGING_LEVEL", "None")
    monkeypatch.setenv("INPUT_OCTOPUS_CLI_SERVER_SECRET", "None")
    monkeypatch.setenv("INPUT_OCTOPUS_CLI_API_SECRET", "None")
    monkeypatch.setenv("INPUT_VELO_ARTIFACT_BUCKET_SECRET", "None")
