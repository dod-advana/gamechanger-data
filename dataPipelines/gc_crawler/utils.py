# -*- coding: utf-8 -*-
"""
gc_crawler.utils
-----------------
Various gc_crawler util functions/classes used in other modules
"""

from hashlib import sha256
from typing import Any, Dict
from functools import reduce
from urllib.parse import urljoin, urlparse
from selenium import webdriver
import re


def str_to_sha256_hex_digest(_str: str) -> str:
    """Converts string to sha256 hex digest"""
    if not _str and not isinstance(_str, str):
        raise ValueError("Arg should be a non-empty string")

    return sha256(_str.encode("utf-8")).hexdigest()


def dict_to_sha256_hex_digest(_dict: Dict[Any, Any]) -> str:
    """Converts dictionary to sha256 hex digest.

      Sensitive to changes in presence and string value of any k/v pairs.
    """
    if not _dict and not isinstance(_dict, dict):
        raise ValueError("Arg should be a non-empty dictionary")

    # order dict k/v pairs & concat their values as strings
    value_string = reduce(
        lambda t1, t2: "".join(map(str, (t1, t2))),
        sorted(_dict.items(), key=lambda t: str(t[0])),
        "",
    )

    return str_to_sha256_hex_digest(value_string)


def is_valid_web_url(url_string: str) -> bool:
    """Checks if given string is a valid URI"""
    try:
        result = urlparse(url_string)
        # true if ...
        return all(
            [
                # only certain schemes
                result.scheme in ['http', 'https'],
                # fqdn without any spaces
                result.netloc and not re.findall(r"\s", result.netloc),
                # path without any spaces
                not re.findall(r"\s", result.path or ""),
            ]
        )
    except AttributeError:
        return False


def abs_url(base_url: str, target_url: str) -> str:
    """returns absolute url given base and relative target"""
    return urljoin(base_url, target_url)


def get_fqdn_from_web_url(url_string: str) -> str:
    """Parses out just the FQDN from the url"""
    return urlparse(url_string).netloc


def close_driver_windows_and_quit(driver: webdriver.Chrome) -> None:
    if driver:
        for w in driver.window_handles:
            driver.switch_to.window(w)
            driver.close()
        driver.quit()
