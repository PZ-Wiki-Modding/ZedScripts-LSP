# Contributing

You are welcome to contribute to this project by submitting issues, feature requests, or pull requests.

## Build
There are two build options available:
- `pyinstaller` for the standalone executable build
- `uv` for the package file build

A [Makefile](Makefile) is provided to automatically handle the various steps necessary to build and release the project.

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
