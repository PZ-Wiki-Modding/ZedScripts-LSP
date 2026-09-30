# ZedScripts LSP

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

The LSP will generate a log file inside the user folder, typically located at:

<details>
<summary>Linux</summary>

```bash
|~/.zedscripts/server.log
```
</details>

<details>
<summary>Windows</summary>
```bash
%USERPROFILE%\.zedscripts\server.log
```
</details>

## License
See [LICENSE](LICENSE) for details.