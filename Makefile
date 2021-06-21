
VERSION_FILE=appversion.txt
VERSION=`cat $(VERSION_FILE)`

version:
	gitversion > appversion.json && jq -r '.SemVer' appversion.json > appversion.txt && cat appversion.txt

install:
	poetry install

update:
	poetry update

tests:
	poetry run pytest test -c pytest.ini -v

test_image:
	docker build -t eu.gcr.io/nube-hub/velo-action:dev .
	docker run -it --rm --name velo-action eu.gcr.io/nube-hub/velo-action:dev -- poetry run pytest test -c pytest.ini -v

image_no_cache:
	docker build -t eu.gcr.io/nube-hub/velo-action:dev . --no-cache
	docker tag eu.gcr.io/nube-hub/velo-action:dev act-github-actions-velo:latest

image:
	docker build -t eu.gcr.io/nube-hub/velo-action:dev .
	docker tag eu.gcr.io/nube-hub/velo-action:dev act-github-actions-velo:latest
	docker image inspect eu.gcr.io/nube-hub/velo-action:dev --format='{{.Size}}'

run: image
	docker run -it --rm --name velo-action act-github-actions-velo:latest

bash: image
	docker run -it --rm --name velo-action --entrypoint bash eu.gcr.io/nube-hub/velo-action:dev

staging: version
	velo deploy-local-dir --version $(VERSION) --project-name velo-action --environment staging --tempdir-behavior existing_folder --tempdir-existing-folder deploy --local_dir .deploy

prod: staging
	velo deploy-local-dir --version $(VERSION) --project-name velo-action --environment prod --tempdir-behavior existing_folder --tempdir-existing-folder deploy --local_dir .deploy

tfi:
	cd deploy/rendered/terraform; \
	terraform init -var-file=values.json

tfa: tfi
	cd deploy/rendered/terraform; \
	terraform apply -var-file=values.json

lint: black flake8 mypy pylint yamllint markdownlint

black:
	poetry run black --config=pyproject.toml .

flake8:
	poetry run flake8 --config='.flake8' .

mypy:
	poetry run mypy --config-file=.mypy.ini velo_action

pylint:
	poetry run pylint --rcfile=.pylintrc --fail-under=8 velo_action

yamllint:
	yamllint --config-file=.yamllint .

markdownlint:
	markdownlint --config=.markdownlint.yaml .
