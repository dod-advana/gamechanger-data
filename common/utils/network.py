import socket
import time


def check_connection(
        ipv4_addr: str,
        port: int,
        timeout_secs: float = 3.0,
        retries: int = 1,
        retry_delay: float = 1.0,
        raise_error: bool = False) -> bool:
    """ Check if remote TCP connection is possible
    :param ipv4_addr: remote ipv4 address
    :param port: remote port
    :param timeout_secs: How many seconds to wait until timeout error
    :param retries: How many times to retry
    :param retry_delay: Secs to wait between tries
    :param raise_error: whether to raise error on failure
    :return: True/False connection success status
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_secs)
    status = False

    try:
        for _ in (range(retries) if retries > 0 else [0]):
            try:
                result = sock.connect_ex((ipv4_addr, port))
                if result == 0:
                    status = True
                    break
            except socket.error:
                pass

            if retries:
                time.sleep(retry_delay)
    finally:
        sock.close()

    if raise_error and not status:
        raise RuntimeError(f"Could not open TCP connection to {ipv4_addr}:{port}")
    else:
        return status
