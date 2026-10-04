.PHONY: help build cleanup release setup clean build_package upload make_schema
.ONESHELL:

SHELL := /bin/bash
PYTHON ?= python3
VENV := .venv

help:
	@echo "ZedScripts Language Server"
	@echo "Available targets:"
	@echo "  build_app  - Build the ZedScripts language server installer"
	@echo "  cleanup - Clean up build artifacts"
	@echo "  release - Build and upload the ZedScripts language server package to PyPi"

build_app:
	uv run pyinstaller --noconfirm ZedScripts.spec

# PyPi release chain
cleanup:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	rm -Rf src/*.egg-info

release: cleanup
	uv build
	uv publish

# schema generation
build_schema:
	uv run python -m ZedScripts.environment.config > schema/zedscripts.json