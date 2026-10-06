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
	rm -rf build dist

# make sure the version in the package matches the version in the source files
verify_version:
	PKG_VERSION=$(shell uv version --short)
	FILES_VERSION=$(shell uv run python -m ZedScripts.__about__)
	echo "Package version: $$PKG_VERSION"
	echo "Files version: $$FILES_VERSION"
	if [ "$$PKG_VERSION" != "$$FILES_VERSION" ]; then \
		echo "Version mismatch!"; \
		exit 1; \
	fi

release: verify_version cleanup
	uv build
	uv publish
	VERSION=$(shell uv version --short)
	git tag -a "v$$VERSION" -m "Release version $$VERSION"
	git push --tags

# schema generation
build_schema:
	uv run python -m ZedScripts.environment.config > schema/zedscripts.json