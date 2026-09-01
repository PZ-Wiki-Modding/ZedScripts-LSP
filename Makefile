.PHONY: help build _setup
.ONESHELL:

SHELL := /bin/bash
PYTHON ?= python3
VENV := .venv

help:
	@echo "ZedScripts Language Server"
	@echo "Available targets:"
	@echo "  build  - Build the ZedScripts language server installer"

# setup .venv if it doesn't exist
_setup:
	if [ ! -d "$(VENV)" ]; then
		$(PYTHON) -m venv $(VENV);
		$(VENV)/bin/python -m pip install .[build];
		echo "*" > .venv/.gitignore
	fi

build: _setup
	$(VENV)/bin/pyinstaller --noconfirm ZedScripts.spec