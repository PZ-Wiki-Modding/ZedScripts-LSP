import logging
from datetime import datetime, timezone
from pathlib import Path




def initialize_logger() -> None:
    import ZedScripts

    # setup the logger
    log_dir = ZedScripts.ZEDSCRIPT_CACHE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # define logger
    logger = logging.getLogger()
    logger.handlers.clear()

    # set early level, this is changed later by the user configuration
    # in the server initialization
    logger.setLevel(logging.DEBUG if ZedScripts.IS_DEBUG else logging.INFO)

    # stream handler for console output
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(stream_handler)

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
    if ZedScripts.IS_DEBUG:
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

    logging.info("ZedScripts logger initialized. Debug mode: %s", ZedScripts.IS_DEBUG)
