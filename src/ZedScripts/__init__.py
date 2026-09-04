import logging
from pathlib import Path


# setup the logger
log_file = Path.home() / "server.log"

logging.basicConfig(
    filename=log_file,
    level=logging.NOTSET,
    format="%(asctime)s %(levelname)s %(message)s",
    filemode="w",
    # force=True,
)

IDENTIFIER = "ZedScripts"
SOURCE = IDENTIFIER