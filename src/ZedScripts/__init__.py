import logging
from pathlib import Path


# setup the logger
log_file = Path.home() / "server.log"

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    filemode="w" # clear logger
)