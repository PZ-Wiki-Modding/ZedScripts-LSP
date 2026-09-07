.PHONY: help build cleanup build_wheel
.ONESHELL:

SHELL := /bin/bash
PYTHON ?= python3
VENV := .venv

help:
	@echo "ZedScripts Language Server"
	@echo "Available targets:"
	@echo "  build  - Build the ZedScripts language server installer"
	@echo "  cleanup - Clean up build artifacts"
	@echo "  build_wheel - Build the ZedScripts language server wheel"

# setup .venv if it doesn't exist
_setup:
	if [ ! -d "$(VENV)" ]; then
		$(PYTHON) -m venv $(VENV);
		$(VENV)/bin/python -m pip install .[build];
		echo "*" > .venv/.gitignore
	fi

build: _setup
	$(VENV)/bin/pyinstaller --noconfirm ZedScripts.spec

cleanup:
# 	rm -rf $(VENV)
	rm -rf dist
	rm -rf build
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -Rf src/*.egg-info

build_wheel:
	$(VENV)/bin/python -m build --wheel