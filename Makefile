.PHONY: img_tag tests

image_tag:
	$(eval IMAGE_TAG=$(shell git rev-parse --short HEAD))
	echo ${IMAGE_TAG}

tests:
	poetry run pytest tests -c pytest.ini -v -m "not docker"

image: image_tag
	docker build -t europe-docker.pkg.dev/nube-hub/docker-public/velo-action:${IMAGE_TAG} .

push: image_tag
	docker push europe-docker.pkg.dev/nube-hub/docker-public/velo-action:${IMAGE_TAG}

run:
	. ./env.dev && docker-compose run --rm velo-action

dev-run:
	. ./env.dev && poetry run python velo_action/action.py

docker_bash: image
	docker-compose run --rm --entrypoint bash velo-action

velo_render_staging:
	velo deploy-local-dir --environment staging

velo_deploy_staging:
	velo deploy-local-dir --environment staging --do-deploy

velo_render_prod:
	velo deploy-local-dir --environment prod

velo_deploy_prod:
	velo deploy-local-dir --environment prod --do-deploy

lint: black flake8 pylint yamllint isort markdownlint

black:
	poetry run black --config=pyproject.toml .

flake8:
	poetry run flake8 --config='.flake8' .

mypy:
	poetry run mypy --config-file=.mypy.ini velo_action tests

pylint:
	poetry run pylint --rcfile=.pylintrc --fail-under=8 velo_action tests

isort:
	poetry run isort --check .

yamllint:
	yamllint --config-file=.yamllint .

markdownlint:
	markdownlint --config=.markdownlint.yaml .
