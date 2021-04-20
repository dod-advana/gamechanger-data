import logging
from . import get_default_logger
from .cli import cli


doc_logger = get_default_logger()
doc_logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
ch.setFormatter(formatter)
doc_logger.addHandler(ch)

doc_logger.info('Document Parser has started')

cli()
