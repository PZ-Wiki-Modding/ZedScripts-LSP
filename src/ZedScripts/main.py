import os
import logging

from ZedScripts.server import server


def main() -> None:
    if os.environ.get("ZEDSCRIPTS_DEBUG"):
        import debugpy

        debugpy.listen(("localhost", 5678))
        logging.debug("Waiting for debug client to attach...")
        debugpy.wait_for_client()  # blocks until the "Python: Attach" launch config connects
        logging.debug("Debug client attached.")
    server.start_io()


if __name__ == "__main__":
    main()