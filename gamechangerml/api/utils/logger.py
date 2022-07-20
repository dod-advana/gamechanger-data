import logging
from logging import handlers
import sys

# set loggers
logger = logging.getLogger()
glogger = logging.getLogger("gunicorn.error")
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s][PID:%(process)d]: %(message)s"
)
try:
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(log_formatter)
    logger.addHandler(ch)
    glogger.addHandler(ch)
    log_file_path = "gamechangerml/api/logs/gc_ml_logs.txt"
    fh = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=2000000, backupCount=1, mode="a"
    )
    logger.info(f"ML API is logging to {log_file_path}")

    fh.setFormatter(log_formatter)
    logger.addHandler(fh)
    glogger.addHandler(fh)
except Exception as e:
    logger.warn(e)
