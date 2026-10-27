from ZedScripts.server import zedserver
from ZedScripts.logger import initialize_logger

def main() -> None:
    initialize_logger()
    zedserver.startup()

if __name__ == "__main__":
    main()
