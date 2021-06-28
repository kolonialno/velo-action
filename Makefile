VERSION_FILE=appversion.txt
VERSION=`cat $(VERSION_FILE)`

.PHONY: version test

version:
	gitversion > appversion.json && jq -r '.SemVer' appversion.json > appversion.txt && cat appversion.txt

install:
	poetry install

update:
	poetry update

test:
	poetry run pytest test -c pytest.ini -v -m "not docker"

image:
	docker build -t eu.gcr.io/nube-hub/velo-action:dev .
	docker tag eu.gcr.io/nube-hub/velo-action:dev act-github-actions-velo:latest odacom/velo-action:latest
	docker tag eu.gcr.io/nube-hub/velo-action:dev odacom/velo-action:latest

build_no_cache:
	docker build --no-cache -t eu.gcr.io/nube-hub/velo-action:dev .

push: image
	# docker push eu.gcr.io/nube-hub/velo-action:dev
	# docker push eu.gcr.io/nube-hub/velo-action:latest
	# docker push ghcr.io/kolonialno/velo-action:latest
	docker push odacom/velo-action:latest

run: image
	docker-compose run --rm velo-action

bash: image
	docker-compose run --rm --entrypoint bash velo-action

lint: black flake8 pylint yamllint

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
