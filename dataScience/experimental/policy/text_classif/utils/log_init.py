import logging
import os
from datetime import datetime
from pathlib import Path


def initialize_logger(to_file=False, data_name="no-name"):
    """
    From

    https://aykutakin.wordpress.com/2013/08/06/logging-to-console-and-file-in-python/

    This logs to the console and to files in the content root directory.

    Args:
        data_name (str): prefixes the name of the log file

    Returns:
        None

    """
    here = os.path.dirname(os.path.realpath(__file__))
    p = Path(here)
    output_dir = p.parents[0]

    fmt = "%Y%m%d%H%M%S"
    now = datetime.now()
    log_time = now.strftime(fmt)

    log_fmt = "[%(asctime)s%(levelname)8s], [%(filename)s:%(lineno)s "
    log_fmt += "- %(funcName)s()], %(message)s"
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(log_fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # create error file handler and set level to error
    if to_file:
        fname = "_".join([data_name, log_time, "warn_error.log"])
        handler = logging.FileHandler(
            os.path.join(output_dir, fname), "w", encoding=None, delay=True
        )
        handler.setLevel(logging.WARNING)
        formatter = logging.Formatter(log_fmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # create debug file handler and set level to debug
        fname = "_".join([data_name, log_time, "all.log"])
        handler = logging.FileHandler(os.path.join(output_dir, fname), "w")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(log_fmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
