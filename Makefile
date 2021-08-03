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
	docker build -t odacom/velo-action:dev .
	docker tag odacom/velo-action:dev odacom/velo-action:latest

image_public:
	docker tag odacom/velo-action:dev europe-west4-docker.pkg.dev/nube-artifacts/oda-docker-public/velo-action:dev
	docker push europe-west4-docker.pkg.dev/nube-artifacts/oda-docker-public/velo-action:dev

build_no_cache:
	docker build --no-cache -t odacom/velo-action:dev .

push: image
	docker push -a odacom/velo-action

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
