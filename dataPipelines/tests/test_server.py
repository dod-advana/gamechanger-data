import requests
from pytest import mark


@mark.dev
def test_server(example_server):
    example_interface, example_port = example_server

    url = f"http://{example_interface}:{example_port}/ping.html"
    resp = requests.get(url)

    print(resp.text)

    assert resp.text == "pong"
