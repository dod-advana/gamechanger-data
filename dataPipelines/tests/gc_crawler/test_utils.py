from dataPipelines.gc_crawler.utils import (
    dict_to_sha256_hex_digest,
    str_to_sha256_hex_digest,
    get_fqdn_from_web_url,
    is_valid_web_url,
    abs_url,
)


def test_dict_to_sha256_hex_digest():
    """Smoke test for dict to hash impl."""
    reference_hash = r"e622b88dfff3dc558cb9d049448b994b70ddebf1adc3f7ae18fb619b44fa3255"

    hash_fields_dict = dict(foo="what", bar=2, baz=None)

    reordered_hash_fields_dict = dict(baz=None, bar=2, foo="what")

    assert reference_hash == dict_to_sha256_hex_digest(
        hash_fields_dict
    ) and reference_hash == dict_to_sha256_hex_digest(reordered_hash_fields_dict)


def test_str_to_sha256_hex_digest():
    """Smoke test for str to hash impl."""
    reference_hash = r"2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"

    assert str_to_sha256_hex_digest("foo") == reference_hash


def test_abs_url():
    page_url = "https://example.local/main?page=1"
    relative_url = "pubs/pub1.pdf"

    assert abs_url(page_url, relative_url) == "https://example.local/pubs/pub1.pdf"


def test_get_fqdn_from_web_url():
    page_url = "https://example.local/main?page=1"

    assert get_fqdn_from_web_url(page_url) == "example.local"


def test_is_valid_web_url():
    bad_urls = [
        "http:/example.local",
        "htrp://example.local",
        "https://example.local/ main?page=1",
    ]
    good_urls = [
        "http://example.local/main?page=1",
        "https://example.local/top/mid/bot/page.html",
    ]
    assert not any(map(is_valid_web_url, bad_urls))
    assert all(map(is_valid_web_url, good_urls))
