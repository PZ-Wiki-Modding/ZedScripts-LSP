# ZedScripts LSP

[![License](https://img.shields.io/github/license/PZ-Wiki-Modding/ZedScripts?label=License)](LICENSE)
![Code Size](https://img.shields.io/github/languages/code-size/PZ-Wiki-Modding/ZedScripts?label=Code%20Size)
[![PyPi Version](https://img.shields.io/pypi/v/ZedScripts)](https://pypi.org/project/ZedScripts/)

ZedScripts LSP is a language server protocol implemented in Python for the [scripting format](https://pzwiki.net/wiki/Scripts) of Project Zomboid. Previously a [VSCode extension](https://github.com/PZ-Wiki-Modding/ZedScripts), it is now reimplemented as a standalone LSP.

It is powered by the [pz-scripts-data](https://github.com/PZ-Wiki-Modding/pz-scripts-data) to provide up-to-date information about the Scripts format. See [configuration](#configuration) to learn how to specify the dataset version.

## Installation
### Releases

### Python package

ZedScripts LSP is available directly as a Python package if you ever need to use its functionality outside of an IDE.

<details open>
<summary>PyPI</summary>

```bash
pip install ZedScripts
```
</details>

<details>
<summary>Git</summary>

```bash
pip install git+https://github.com/PZ-Wiki-Modding/ZedScripts-LSP.git
```
</details>

<details>
<summary>Dev</summary>

```bash
pip install -e .
```
</details>

## Cache directory

A cache directory is used on your system to cache the [pz-scripts-data](https://github.com/PZ-Wiki-Modding/pz-scripts-data) and logs, as well as global configuration. You can find it here:

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

## Configuration

The LSP uses configurations files `.zedscripts.json` which provide information to the LSP about various settings.

Example of configuration file content:
```json
{
    "$schema": "https://raw.githubusercontent.com/PZ-Wiki-Modding/ZedScripts-LSP/refs/heads/main/schema/zedscripts.json",
    "dataset": {
        "latest": true
    },
    "libraries": [
        "~/.steam/debian-installation/steamapps/common/ProjectZomboid/projectzomboid/media",
    ]
}
```

They are optional and should be placed at the root of your workspaces or in the [cache directory](#cache-directory). The local configuration (root of your workspaces) will override the global configuration (cache directory).

```bash
📁 workspace1
    📁 Contents/mods/YourMod/42/media/scripts
        📄 example_script.txt
    📄 .zedscripts.json
📁 workspace2
    📄 .zedscripts.json
```
```bash
📁 ~
    📁 .zedscripts
        📄 .zedscripts.json
```

A schema is available to validate the configuration files and can be found in the [schema directory](schema/zedscripts.json).

See the following sections for detailed explanation of each parameters.

### Dataset
You can configure the version of the [pz-scripts-data](https://github.com/PZ-Wiki-Modding/pz-scripts-data) dataset.

```json
{
    "dataset": {
        ...
    }
}
```

The key-values which can be set in the `dataset` section are the following:
- `latest`: a boolean indicating the LSP to use the latest available version for the dataset (latest game version and dataset version)
- `stable`: a boolean indicating the LSP to use the latest stable version of the dataset
- `release`: used to indicate a specific release version of the dataset with the following arguments:
  - `major`: major build version (e.g. `42`, `43`)
  - `minor`: minor build version (e.g. `0`, `1`)
  - `patch`: patch build version (e.g. `0`, `1`)
  - `version` (optional): the dataset version (e.g. `0`, `1`, `2`)
  - for example, version `42.21.0` of the game would be specified as:
```json
{
    "release": {
        "major": 42,
        "minor": 21,
        "patch": 0
    }
}
```

It's suggested to use the `stable` option.

### Libraries
A list of paths that should include the base game path, as well as other games that your mod depends on for its scripts. This will provide LSP the ability to find other blocks definitions that you may reference inside your mod's scripts.
```json
{
    "libraries": [
        "path/to/base/game",
        "path/to/other/dependent/game"
    ]
}
```

### Ignored
A list of regex patterns tested on file paths that should be ignored by the LSP, by default this includes large script files that can slow down the LSP.
```json
{
    "ignored": [
        "path/to/large/script/file"
    ]
}
```

### Diagnostics
A list of diagnostics with modifiers to change the diagnostic behavior of the LSP. The following parameters:
- `type`: the type of the diagnostic, that is the ID shown in the diagnostics hover tooltip (for example, `BLOCK_UNKNOWN_BLOCK`)
- `enable` (optional): boolean to disable the diagnostic
- `severity` (optional): the severity level of the diagnostic (accepted values: `Error`, `Warning`, `Information`, `Hint`)
- `tags` (optional): an array of tags which an IDE may use to provide additional context or behavior for the diagnostic (accepted values: `Unnecessary`, `Deprecated`)

Each diagnostic by default have a specific set of modifiers that can be overridden in the configuration.

```json
{
    "diagnostics": [
        {
            "type": "BLOCK_UNKNOWN_BLOCK",
            "enable": true,
            "severity": "Warning",
            "tags": ["Unnecessary"]
        }
    ]
}
```

## IDE configuration
Based on the IDE you use, you may need to install the ZedScripts LSP application for your OS in the [releases](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases) (Linux, Windows).

### Visual Studio Code

Install the [ZedScripts extension](https://marketplace.visualstudio.com/items?itemName=SimKDT.ZedScripts) from the Visual Studio Code marketplace. The extension will handle the downloading and setup of the ZedScripts LSP server for you.

### VIM

Using [yegappan/lsp](https://github.com/yegappan/lsp), setup the ZedScripts LSP server as follows:

```vim
let lspServers = [
      \ #{
      \   name: 'zedscripts',
      \   filetype: ['text', 'zedscripts'],
      \   path: 'path/to/ZedScripts',
      \   args: []
      \ }
      \ ]

autocmd User LspSetup call LspAddServer(lspServers)
```

> [!NOTE]
> You can see [this video](https://www.youtube.com/watch?v=-5lb_jLQmKc) which explains how to set up VIM, and notably setup a LSP server.

## License and contribution
This project is licensed under a [MIT license](LICENSE). Before contributing to the project, please see [CONTRIBUTING](CONTRIBUTING.md).