# Contributing

You are welcome to contribute to this project by submitting issues, feature requests, or pull requests.

## Build
There are two build options available:
- `pyinstaller` for the standalone executable build
- `uv` for the package file build

A [Makefile](Makefile) is provided to automatically handle the various steps necessary to build and release the project.

## Tests

Run `make test` (or `uv run --frozen python -m unittest discover -s tests -p
'test_*.py' -v`) for offline unit tests. The suite exercises the production lexer,
source ranges and LSP positions, including the existing script fixtures. It uses
the standard-library test runner and isolates the package's import-time cache.
No game installation, downloaded dataset or running editor is required.

## Package release
Best to use `uv` for publishing packages. 

For the test PyPI index
```bash
uv publish --index testpypi
```

For the PyPI index
```bash
uv publish
```

## Commits

Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages.
