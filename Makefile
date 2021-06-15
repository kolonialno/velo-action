
install:
	poetry install

update:
	poetry update

test:
	poetry run pytest . -c pytest.ini -v

lint: black flake8 mypy pylint yamllint markdownlint

black:
	poetry run black --config=pyproject.toml .

flake8:
	poetry run flake8 --config='.flake8' .

mypy:
	poetry run mypy --config-file=.mypy.ini .

pylint:
	poetry run pylint --rcfile=.pylintrc --fail-under=7 velo scripts tests

yamllint:
	yamllint --config-file=.yamllint .

markdownlint:
	markdownlint --config=.markdownlint.yaml .

version:
	gitversion > appversion.json && jq -r '.SemVer' appversion.json > appversion.txt && cat appversion.txt
