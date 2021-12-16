VERSION_FILE=appversion.txt
VERSION=`cat $(VERSION_FILE)`

.PHONY: version tests

version:
	gitversion /showvariable SemVer > appversion.txt
	echo $(VERSION)

tests:
	poetry run pytest tests -c pytest.ini -v -m "not docker"

image:
	docker build -t europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:${VERSION} .

push:
	docker push europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:${VERSION}

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
