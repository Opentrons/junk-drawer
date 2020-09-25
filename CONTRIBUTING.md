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
poetry run pylama

# run type checks
poetry run mypy
```

## Build and Publish Tasks

```shell
# build wheel file
poetry build
```
