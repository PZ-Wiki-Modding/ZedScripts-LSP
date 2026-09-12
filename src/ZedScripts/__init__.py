import os
import logging
from pathlib import Path

IS_DEBUG = os.getenv("ZEDSCRIPTS_DEBUG_MODE") == "1"

ZEDSCRIPT_CACHE_DIR = Path.home() / ".zedscripts"
"""
Cache directory to hold various information related to ZedScripts.
"""

# setup the logger
log_file = ZEDSCRIPT_CACHE_DIR / "server.log"

level = logging.DEBUG if IS_DEBUG else logging.INFO
logging.basicConfig(
    filename=log_file,
    level=level,
    format="%(asctime)s %(levelname)s %(message)s",
    filemode="w",
    # force=True,
)

logging.info("ZedScripts logger initialized. Debug mode: %s", IS_DEBUG)

IDENTIFIER = "ZedScripts"
SOURCE = IDENTIFIER

SCRIPTS_DATA_MANIFEST = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/heads/main/manifest.json"
SCRIPTS_BLOCKS_DATA_LINK = "https://raw.githubusercontent.com/pz-wiki-modding/pz-scripts-data/refs/heads/main/out/scriptsBlocks.json"
ROOTS_DATA_LINK = "https://raw.githubusercontent.com/pz-wiki-modding/pz-scripts-data/refs/heads/main/out/roots.json"
