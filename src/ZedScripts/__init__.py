import os
import logging
from pathlib import Path

IS_DEBUG = os.getenv("ZEDSCRIPTS_DEBUG_MODE") == "1"

# setup the logger
log_file = Path.home() / "server.log"

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