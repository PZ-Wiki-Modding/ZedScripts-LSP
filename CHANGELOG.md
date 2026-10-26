# Change Log
<!-- http://keepachangelog.com/ -->

## [Unreleased]

## [1.4.0] - 2026/10/26
- Fixed allowed values not comparing as string types which led to an instant validation failure
- Libraries loading is done if at least one mod is found (instead of expecting at least one script file found) (contributes to [#30](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/30) but does not fix it)
- Fix missing notification to indicate workspace and library loading started
- Added new files loaded notification
- Added definition access for file types (CTRL+left click in VSCode)
- Fixed loading datasets not taking into account global configuration
- Improved semantic tokens highlighting for values of array type
- Fixed type validation not working properly
- Added array type diagnostics (not included block references validation for now)
- DEBUG: list files refs in hover

## [1.3.1] - 2026/10/24
- Fixed solitary files not working ([#19](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/19))
- Fixed library loading counter being incorrect and also bump workspaces and libraries loaded after they have been loaded
- Diagnostic added for block's missing parameter ([#24](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/24))

## [1.3.0] - 2026/10/24
- Added description and classifiers to package
- Added mypy typed support
- Added missing author [@demiurgeQuantified] to pyproject.toml
- Fixed missing README section
- Changes to diagnostics:
  - VALUE_WRONGLY_FORMATTED_KEY_VALUE_PAIR from Warning to Information
- Improved debug block references hovering
- Revamped dataset handling and validation to use new Pydantic models from [pz-scripts-data]
- Fixed script file discovery being case-sensitive
- Fixed block referencing not ignored versions that can't be accessed from within another versioning script file
- New configuration key for dataset: local
- Now stripping descriptions of parameter hovering
- Implemented new parameter type: file
  - Added diagnostics for no files found and multiple files found
  - Added hovering of the file reference value to display texture previews. Will display multiple textures being found for easy comparison.

## [1.2.0] - 2026/10/19
- Added [pygments](https://pygments.org/) support for syntax highlighting in code blocks.
  - Use it in sphinx docs (see README for details)
  - Use the command `highlight-zedscripts <file>` to print the file's content with the lexer highlight applied.
- Added debug diagnostic for missing parameter descriptions (`DEBUG_MISSING_PARAMETER_DESCRIPTION`), only appears when the environment variable `ZEDSCRIPTS_DEBUG_MODE` is set.
- Added extra information on how to install debugpy when launching in debug mode without it.
- Some cleanup to existing tests.

## [1.1.0] - 2026/10/12
- Code cleanup
- Implemented automated tests to verify some features before release of new versions:
  - Test for schema and default config generation
  - Test for parser functionality
- Improved logging:
  - Provided an option for logging level available only in the global configuration (`server.logging_level`)
  - Logging is now per server instance, that is each server has its own log file named with the date timestamp
  - Only 5 log files are stored, older files are automatically deleted
- The global configuration file is now automatically created with the default values if it does not exist
- Config module subcommands:
  - `schema` to generate the schema file for `.zedscripts.json` validation
  - `default` to generate the default configuration file for the LSP
  - Each can have a `--output` argument to specify an output file path

## [1.0.1] - 2026/10/06
- Fixed an issue with block ID validation in certain scenarios ([#14](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/14))

## [1.0.0] - 2026/10/04
- Show a `(deprecated)` note in hover information of a deprecated parameter
- Package name changed from ZedScripts-LSP to ZedScripts
- Only load libraries if script files are found in any of the workspaces
- Add new notifications to improve support for status bars in VSCode
- New diagnostic configuration in global and local config files
- Schema file for `.zedscripts.json` files validation

## [0.0.2] - Beta release
- Provide parameter type information in hovering ([#4](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/4))
- Centralized download links for datasets
- `cant_self_validate` method for `Dataset`
- Warning diagnostic unparsed tokens ([#8](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/8))
- Implement notifications for workspace loading progress communication
- Fix `ScriptBlockParameter` typing for defaults
- Fix configuration file parsing allowing for `dataset.release.version` to be optional (defaults to maximum available build release `version`) and to have a value equal to 0 ([#7](https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/issues/7))

## [0.0.1] - Beta release
Initial base by [@demiurgeQuantified], created by [@SimKDT]. Provided by [@PZ-Wiki-Modding] and based on the initial [ZedScripts] VSCode extension.



[unreleased]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.4.0
[1.3.1]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.3.1
[1.3.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.3.0
[1.2.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.2.0
[1.1.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.1.0
[1.0.1]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.0.1
[1.0.0]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v1.0.0
[0.0.2]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v0.0.2
[0.0.1]: https://github.com/PZ-Wiki-Modding/ZedScripts-LSP/releases/tag/v0.0.1
[pz-scripts-data]: https://github.com/PZ-Wiki-Modding/pz-scripts-data
[ZedScripts]: https://github.com/PZ-Wiki-Modding/ZedScripts
[@PZ-Wiki-Modding]: https://github.com/PZ-Wiki-Modding
[@SimKDT]: https://github.com/SimKDT
[@demiurgeQuantified]: https://github.com/demiurgeQuantified