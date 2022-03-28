.PHONY: img_tag tests

IMAGE_NAME:=europe-docker.pkg.dev/nube-hub/docker-public/velo-action
IMAGE_SIZE_LIMIT="1300 MB"

image_tag:
	$(eval IMAGE_TAG=$(shell git rev-parse --short HEAD))
	echo ${IMAGE_TAG}

tests:
	poetry run pytest velo_action -c pytest.ini -v -m "not docker"

image: image_tag
	docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

push: image
	docker push ${IMAGE_NAME}:${IMAGE_TAG}

image_size:
	docker run -v /var/run/docker.sock:/var/run/docker.sock --rm -e INPUT_IMAGE=${IMAGE_NAME} -e INPUT_SIZE=${IMAGE_SIZE_LIMIT} wemakeservices/docker-image-size-limit

run:
	. ./env.dev && poetry run python velo_action/main.py

run_docker:
	. ./env.dev && docker-compose build && docker-compose run --rm velo-action

run_docker_shell:
	. ./env.dev && docker-compose build && docker-compose run --rm --entrypoint bash velo-action

velo_render_staging:
	velo deploy-local-dir --environment staging

velo_deploy_staging:
	velo deploy-local-dir --environment staging --do-deploy

velo_render_prod:
	velo deploy-local-dir --environment prod

velo_deploy_prod:
	velo deploy-local-dir --environment prod --do-deploy

lint: black flake8 mypy pylint yamllint isort markdownlint

black:
	poetry run black --config=pyproject.toml .

flake8:
	poetry run flake8 --config='.flake8' .

mypy:
	poetry run mypy --config-file=.mypy.ini velo_action

pylint:
	poetry run pylint --rcfile=.pylintrc --fail-under=8 velo_action

isort:
	poetry run isort .

yamllint:
	yamllint --config-file=.yamllint .

markdownlint:
	markdownlint --config=.markdownlint.yaml .

install:
	poetry install

docs_generate:
	techdocs-cli generate --verbose --no-docker

# The 'mkdocs-click' is not installed in the techdocs docker image
docs: docs_generate
	techdocs-cli serve --verbose --no-docker

# require access to nube-centro-prod
docs_publish_prod: docs_generate
	techdocs-cli publish \
	--publisher-type googleGcs \
	--storage-name centro-docs-prod \
	--entity "default/Component/velo"

# require access to nube-centro-staging
docs_publish_staging: docs_generate
	techdocs-cli publish \
	--publisher-type googleGcs \
	--storage-name centro-docs-staging \
	--entity "default/Component/velo"

mkdocs:
	mkdocs serve --verbose
