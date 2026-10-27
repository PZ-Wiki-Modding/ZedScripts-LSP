import os
import logging
from datetime import datetime, timezone
from pathlib import Path

IDENTIFIER = "ZedScripts"
DIAGNOSTICS_SOURCE = IDENTIFIER

IS_DEBUG = os.getenv("ZEDSCRIPTS_DEBUG_MODE") == "1"

# zedscript's cache directory
ZEDSCRIPT_CACHE_DIR = Path.home() / ".zedscripts"
"""
Cache directory to hold various information related to ZedScripts.
"""
ZEDSCRIPT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

SOLITARY_FILES_DIR = ZEDSCRIPT_CACHE_DIR / "solitary"

# config files naming
CONFIGURATION_FILE_NAME = ".zedscripts.json"
GLOBAL_CONFIGURATION_FILE = (ZEDSCRIPT_CACHE_DIR / CONFIGURATION_FILE_NAME).resolve()

# datasets
SCRIPTS_DATA_MANIFEST = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/heads/main/manifest.json"
SCRIPTS_BLOCKS_DATA_LINK = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/scriptsBlocks.json"
ROOTS_DATA_LINK = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/roots.json"

SCRIPTSDOCS_LINK = "https://pz-wiki-modding.github.io/PZ-API-Docs/scripts/"