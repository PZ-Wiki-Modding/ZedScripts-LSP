# Change Log
<!-- http://keepachangelog.com/ -->

## [Unreleased]

## [1.0.0] - 2026/10/04
- Show a `(deprecated)` note in hover information of a deprecated parameter
- Package name changed from ZedScripts-LSP to ZedScripts
- Only load libraries if script files are found in any of the workspaces
- Add new notifications to improve support for status bars in VSCode
- New diagnostic configuration in global and local config files
- Schema file for `.zedscripts.json` files validation

## [0.0.2] - 2026/10/01
- Provide parameter type information in hovering ([#4](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/4))
- Centralized download links for datasets
- `cant_self_validate` method for `Dataset`
- Warning diagnostic unparsed tokens ([#8](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/8))
- Implement notifications for workspace loading progress communication
- Fix `ScriptBlockParameter` typing for defaults
- Fix configuration file parsing allowing for `dataset.release.version` to be optional (defaults to maximum available build release `version`) and to have a value equal to 0 ([#7](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/7))

## [0.0.1] - Initial release
Initial base by [@demiurgeQuantified], created by [@SimKDT]. Provided by [@PZ-Wiki-Modding] and based on the initial [ZedScripts] VSCode extension.



[unreleased]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.0.0
[0.0.2]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v0.0.2
[0.0.1]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v0.0.1
[ZedScripts]: https://github.com/PZ-Wiki-Modding/ZedScripts
[@PZ-Wiki-Modding]: https://github.com/PZ-Wiki-Modding
[@SimKDT]: https://github.com/SimKDT
[@demiurgeQuantified]: https://github.com/demiurgeQuantified