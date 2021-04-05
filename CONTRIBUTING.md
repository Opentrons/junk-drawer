# Contributing Guide

## Development Setup

You will need the following tools installed:

- [Python 3.7][]
- [Poetry][]

Once they're installed, you can clone the repository, setup a virtual environment, and install dependencies:

```shell
git clone https://github.com/Opentrons/junk-drawer.git
cd junk-drawer
poetry install
```

[python 3.7]: https://www.python.org/downloads/
[poetry]: https://python-poetry.org/

## Development Tasks

All tasks should be run in the virtualenv by using `poetry run` or by activating the virtualenv using `poetry shell`

```shell
# run tests
poetry run pytest

# run tests in watch mode
poetry run ptw

# run formatting
poetry run black .

# run lints
poetry run flake8

# run type checks
poetry run mypy

# run everything
poetry run black . && poetry run flake8 && poetry run mypy && poetry run pytest
```

## Build and Publish Tasks

```shell
# build wheel and sdist files
poetry build
```

## Releasing

You can create a release by running the [Create a new release][] GitHub Actions workflow. To run the workflow, use the "Run workflow" button on the workflow page, specifying the exact semver version or bump rule. Allowed bump rules are from the [poetry version][] command:

- patch
- minor
- major
- prepatch
- preminor
- premajor
- prerelease

When run, the workflow will:

1. Bump the version in `pyproject.toml`
2. Commit the bump
3. Tag the bump commit
4. Push the tag and commit

The pushed tag will trigger a run of the [Continuous integration][] workflow, which will build the project and deploy it to [PyPI][].

[create a new release]: https://github.com/Opentrons/junk-drawer/actions?query=workflow%3A%22Create+release%22
[continuous integration]: https://github.com/Opentrons/junk-drawer/actions?query=workflow%3A%22Continuous+integration%22
[poetry version]: https://python-poetry.org/docs/cli/#version
[pypi]: https://pypi.org/project/junk-drawer/
