from os import makedirs
from os.path import split
from logging import getLogger, StreamHandler, Formatter, FileHandler


def configure_logger(
    name="gamechanger",
    min_level="DEBUG",
    file_path=None,
    msg_fmt="%(levelname)s - %(asctime)s - %(filename)s - line %(lineno)s - %(message)s",
    date_fmt="%Y-%m-%d %H:%M:%S",
):
    """Configure a logger object.

    Args:
        name (str or None, optional): If str, name of the logger to get/ create. 
        If None, will get the root logger. Default is "gamechanger".
        min_level (str or int, optional): Denotes the minimum level to log. See 
            https://docs.python.org/3/library/logging.html#levels for options. 
            Defaults to "DEBUG".
        file_path (str or None, optional): If str, path to a ".log" file to 
            record log messages. If None, will not log to a file. Default is 
            None.
        msg_fmt (str, optional): Log message formatting. Default is 
            "%(asctime)s - %(levelname)s - %(filename)s - line %(lineno)s - %(message)s"
        date_fmt (str, optional): Date format for log messages. Default is
            "%Y-%m-%d %H:%M:%S".
    
    Returns:
        logging.Logger
    """
    logger = getLogger(name)
    logger.propagate = False
    logger.setLevel(min_level)

    has_stream = False
    has_file = False
    for handler in logger.handlers:
        handler_type = type(handler)
        if handler_type == StreamHandler:
            has_stream = True
        elif handler_type == FileHandler:
            has_file = True

    formatter = Formatter(msg_fmt, datefmt=date_fmt)

    if not has_stream:
        stream_handler = StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(min_level)
        logger.addHandler(stream_handler)

    if not has_file and file_path is not None and file_path.endswith(".log"):
        dirpath = split(file_path)[0]
        makedirs(dirpath, exist_ok=True)
        file_handler = FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(min_level)
        logger.addHandler(file_handler)
    
    return logger
