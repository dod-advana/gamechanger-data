import logging
import threading
import typing as t
from gamechangerml.api.utils import processmanager

logger = logging.getLogger("gamechanger")


class StatusUpdater:
    """
        Updates process manager for key given in constructor
        each step takes a message
        nsteps needs to be known at start
        will not stop updating if steps > nsteps but the output will be nonsense, e.g. 'step 6 of 4'
    """

    def __init__(self, process_key: str, nsteps: int, log_messages=True):
        self.key = process_key
        self.current_step = 1
        self.nsteps = nsteps
        self.last_message = None
        self.log_messages = log_messages

    def next_step(self, message: str = "") -> None:
        try:
            if self.log_messages:
                logger.info(message)

            processmanager.update_status(
                self.key,
                progress=self.current_step,
                total=self.nsteps,
                message=message,
                thread_id=threading.current_thread().ident
            )
            if self.current_step > self.nsteps:
                logger.warn(f"StatusUpdater current step larger than nsteps")

        except Exception as e:
            logger.warn(
                f"StatusUpdater {self.key} failed to update status: {message} \n{e}"
            )
        finally:
            self.current_step += 1
            self.last_message = message

    def current(self) -> dict:
        return {
            "key": self.key,
            "current_step": self.current_step,
            "nsteps": self.nsteps,
            "last_message": self.last_message,
        }
