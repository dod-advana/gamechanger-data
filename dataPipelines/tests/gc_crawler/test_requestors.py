import pytest
from dataPipelines.gc_crawler.requestors import (
    DefaultRequestor,
    MapBasedPseudoRequestor,
    FileBasedPseudoRequestor,
)
import dataPipelines.gc_crawler.example


def test_map_based_pseudo_requestor():
    default_response = "Hello"
    foo_response = "Hello Foo"
    specific_foo_response = "Hello Specific Foo"

    lambda_text_map = lambda k: foo_response if k.startswith("foo") else None
    dict_text_map = {"foo": foo_response, "foo.specific": specific_foo_response}

    lambda_requestor_with_default = MapBasedPseudoRequestor(
        default_text=default_response, url_text_map=lambda_text_map
    )
    assert lambda_requestor_with_default.get_text("foo") == foo_response
    assert lambda_requestor_with_default.get_text("foo.specific") == foo_response
    assert lambda_requestor_with_default.get_text("something") == default_response

    dict_requestor_with_default = MapBasedPseudoRequestor(
        default_text=default_response, url_text_map=dict_text_map
    )
    assert dict_requestor_with_default.get_text("foo") == foo_response
    assert dict_requestor_with_default.get_text("foo.specific") == specific_foo_response
    assert dict_requestor_with_default.get_text("something") == default_response

    dict_requestor_without_default = MapBasedPseudoRequestor(url_text_map=dict_text_map)
    assert dict_requestor_without_default.get_text("foo") == foo_response
    assert (
        dict_requestor_without_default.get_text("foo.specific") == specific_foo_response
    )
    with pytest.raises(KeyError):
        dict_requestor_without_default.get_text("something")

    noop_requestor = MapBasedPseudoRequestor()
    with pytest.raises(KeyError):
        noop_requestor.get_text("something")


def test_file_based_pseudo_requestor():
    base_url = "https://example.local"
    requestor = FileBasedPseudoRequestor(
        fake_web_base_url=base_url,
        source_sample_dir_path=dataPipelines.gc_crawler.example.SOURCE_SAMPLE_DIR,
    )

    assert requestor.get_text(base_url + "/ping.html").strip() == "pong"
