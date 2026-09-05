import os
import logging
from pathlib import Path

DEBUG_MODE = os.getenv("ZEDSCRIPTS_DEBUG_MODE") == "1"

# setup the logger
log_file = Path.home() / "server.log"

level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(
    filename=log_file,
    level=level,
    format="%(asctime)s %(levelname)s %(message)s",
    filemode="w",
    # force=True,
)

logging.info("ZedScripts logger initialized. Debug mode: %s", DEBUG_MODE)

IDENTIFIER = "ZedScripts"
SOURCE = IDENTIFIER