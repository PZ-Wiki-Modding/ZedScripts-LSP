.PHONY: help build cleanup release setup clean build_package upload
.ONESHELL:

SHELL := /bin/bash
PYTHON ?= python3
VENV := .venv

help:
	@echo "ZedScripts Language Server"
	@echo "Available targets:"
	@echo "  build  - Build the ZedScripts language server installer"
	@echo "  cleanup - Clean up build artifacts"
	@echo "  release - Build and upload the ZedScripts language server package to PyPi"
	@echo "  setup - Set up the Python virtual environment and install build dependencies"
	@echo "  clean - Clean up the dist directory"
	@echo "  build_package - Build the ZedScripts language server package"
	@echo "  upload - Upload the ZedScripts language server package to PyPi"

# setup .venv if it doesn't exist
_setup:
	if [ ! -d "$(VENV)" ]; then
		$(PYTHON) -m venv $(VENV);
		$(VENV)/bin/python -m pip install .[build];
		echo "*" > .venv/.gitignore
	fi

build: _setup
	$(VENV)/bin/pyinstaller --noconfirm ZedScripts.spec

# PyPi release chain
release: cleanup setup build_package upload

cleanup:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -Rf src/*.egg-info

setup:
	$(PYTHON) -m venv $(VENV) && echo "*" > $(VENV)/.gitignore
	. $(VENV)/bin/activate && pip install --upgrade pip
	pip install --upgrade build twine

build_package:
	$(VENV)/bin/python3 -m build

upload:
	$(VENV)/bin/python3 -m twine upload --repository pypi dist/*

make_schema:
	uv run python -m ZedScripts.environment.config > schema/zedscripts.json