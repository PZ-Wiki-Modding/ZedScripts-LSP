# ZedScripts LSP

[![License](https://img.shields.io/github/license/PZ-Wiki-Modding/ZedScripts?label=License)](LICENSE)
![Code Size](https://img.shields.io/github/languages/code-size/PZ-Wiki-Modding/ZedScripts?label=Code%20Size)
[![PyPi Version](https://img.shields.io/pypi/v/ZedScripts)](https://pypi.org/project/ZedScripts/)
[![PyPi Downloads](https://img.shields.io/pypi/dm/ZedScripts)](https://pypi.org/project/ZedScripts/)
![PyPI Python Version](https://img.shields.io/pypi/pyversions/ZedScripts)

> [!IMPORTANT]
> Work In Progress, this is a BETA release

ZedScripts LSP is a language server protocol implementation in Python for the [scripting format]() of Project Zomboid. Previously a VSCode extension, it is now reimplemented as a standalone LSP.

## Installation
### Releases

### Python package

<!-- <details open>
<summary>PyPi</summary>

```bash
pip install ZedScripts-LSP
```
</details> -->

<details>
<summary>Git</summary>

```bash
pip install git+https://github.com/PZ-Wiki-Modding/ZedScripts-LSP.git
```
</details>

<details>
<summary>Local</summary>

```bash
pip install .
```
</details>

## Usage

You can either launch the LSP from Python or you can launch the software as is.

### LSP cache directory

The LSP uses a cache directory on your system to store temporary files and logs as well as configuration files. You can find it here: 

<details>
<summary>Linux</summary>

```bash
~/.zedscripts
```
</details>

<details>
<summary>Windows</summary>

```bash
%USERPROFILE%\.zedscripts
```
</details>

### Configuration

The LSP uses configurations files which provide information to the LSP about various settings. You have access to a global configuration file

Example configuration:
```json
{
    "dataset": {
        "latest": true
    },
    "libraries": [
        "/home/simon/.steam/debian-installation/steamapps/common/ProjectZomboid/projectzomboid/media",
    ]
}
```

WIP: proper documentation will come soon

## License
See [LICENSE](LICENSE) for details.