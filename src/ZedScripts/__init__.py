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

# setup the logger

log_dir = Path.home() / ".zedscripts" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# define logger
logger = logging.getLogger()

# set early level, this is changed later by the user configuration
# in the server initialization
logger.setLevel(logging.DEBUG if IS_DEBUG else logging.INFO)

formater = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

# setup the time-based log handler
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f")
time_log_file = log_dir / f"server-{timestamp}.log"
time_handler = logging.FileHandler(time_log_file, encoding="utf-8")
time_handler.setFormatter(
    formater
)
logger.addHandler(time_handler)

# setup the debug log handler which stays in the same file to make it easier to view logs
# when restarting the server for example
if IS_DEBUG:
    global_log_file = log_dir / f"server-debug.log"
    global_handler = logging.FileHandler(
        global_log_file, encoding="utf-8", mode="w"
    )
    global_handler.setFormatter(
        formater
    )
    logger.addHandler(global_handler)

# filenames sort chronologically because the timestamp comes first
keep_logs = 5
log_files = sorted(log_dir.glob("server-*.log"), reverse=True)

# delete the oldest log file
for old_file in log_files[keep_logs:]:
    try:
        old_file.unlink()
    except OSError:
        logger.exception("Failed to delete old log file: %s", old_file)

logging.info("ZedScripts logger initialized. Debug mode: %s", IS_DEBUG)

# datasets
SCRIPTS_DATA_MANIFEST = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/heads/main/manifest.json"
SCRIPTS_BLOCKS_DATA_LINK = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/scriptsBlocks.json"
ROOTS_DATA_LINK = "https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-scripts-data/refs/tags/{best_tag}/out/roots.json"

SCRIPTSDOCS_LINK = "https://pz-wiki-modding.github.io/PZ-API-Docs/scripts/"