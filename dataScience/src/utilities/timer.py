import time
import logging

logger = logging.getLogger(__name__)


class Timer:
    def __enter__(self, level="debug"):
        """
        A simple timer class. Usage is

            `with Timer():
                < code to be timed >'

        It will generate a log message with  the elapsed time according
        specified `level` - either logger.DEBUG or logger.INFO. If `level`
        is anything other than "debug", the level is logger.INFO

        Args:
            level (str): Anything other than the default "debug" will log
                as logging.INFO; default is "debug".

        """
        self._level = level
        self.t0 = time.time()

    def __exit__(self, *args):
        if self._level == "debug":
            logger.debug(
                "elapsed time: {:0.3f}s".format(time.time() - self.t0)
            )
        else:
            logger.info("elapsed time: {:0.3f}s".format(time.time() - self.t0))
