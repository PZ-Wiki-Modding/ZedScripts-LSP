.PHONY: help build
.ONESHELL:

SHELL := /bin/bash

help:
	@echo "ZedScripts Language Server"
	@echo "Available targets:"
	@echo "  build  - Build the ZedScripts language server installer"

build:
	pyinstaller --noconfirm ZedScripts.spec