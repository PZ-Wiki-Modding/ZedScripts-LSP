import logging
from pathlib import Path


# setup the logger
log_file = Path.home().parent / "server.log"
log_file.write_text("") # clear logger

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)