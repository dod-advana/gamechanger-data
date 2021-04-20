from contextlib import contextmanager
from typing import ContextManager
from typing import Callable, Any, Union
import signal


class ContextTimeout(Exception):
    """Raised when execution context exceeds its' specified timeout"""
    pass


@contextmanager
def set_signal(
        signum: signal.Signals,
        handler: Callable[[signal.Signals, Any], Any]) -> ContextManager[None]:
    """Set handler for given signal"""
    old_handler = signal.getsignal(signum)
    signal.signal(signum, handler)
    try:
        yield
    finally:
        signal.signal(signum, old_handler)


@contextmanager
def set_alarm(secs: float) -> ContextManager[None]:
    """Delivers SIGALRM upon after approximately <arg:secs> seconds"""
    signal.setitimer(signal.ITIMER_REAL, secs)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0) # Disable alarm


def err_callback(signum: signal.Signals, frame: Any) -> None:
    """Callback that raises Timeout.ContextTimeout"""
    raise ContextTimeout()


@contextmanager
def raise_on_timeout(secs: Union[float, int]) -> ContextManager[None]:
    """Raises ContextTimeout unless context exits in time"""
    secs = float(secs)
    with set_signal(signal.SIGALRM, err_callback):
        with set_alarm(secs):
            yield