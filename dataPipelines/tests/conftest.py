import os
import socket
from pytest import fixture
from . import MODULE_PATH
from http.server import SimpleHTTPRequestHandler
import socketserver
from pathlib import Path
import threading


@fixture(scope='session')
def example_server():

    webserver_root = os.path.join(MODULE_PATH, 'example_webserver_root')
    server_interface = "localhost"
    server_port = 0  # first available port

    if not Path(webserver_root).is_dir():
        raise ValueError(f"Given web server path is invalid: {webserver_root}")

    os.chdir(webserver_root)  # necessary for python <3.7

    if not Path(".").absolute().name == 'example_webserver_root':
        raise RuntimeError(
            f"Could not change dir to example webserver root: {example_root}"
        )

    with socketserver.TCPServer(
        (server_interface, server_port), SimpleHTTPRequestHandler
    ) as httpd:

        daemon = threading.Thread(name="example web server", target=httpd.serve_forever)

        daemon.setDaemon(True)  # kill after main thread dies
        daemon.start()

        yield httpd.server_address
