.PHONY: img_tag tests

img_tag:
	$(eval IMG_TAG=$(shell git rev-parse --short HEAD))

tests:
	poetry run pytest tests -c pytest.ini -v -m "not docker"

image: img_tag
	docker build -t europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:$(IMG_TAG) .

push: img_tag
	docker push europe-docker.pkg.dev/nube-artifacts-prod/nube-container-images-public/velo-action:$(IMG_TAG)

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
