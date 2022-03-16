# -*- coding: utf-8 -*-
"""
gc_crawler.requestors
-----------------
Primary classes/objects that power requests sent by gc_crawler
"""
from typing import Dict, Optional, Callable, Union
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

DEFAULT_TIMEOUT = 5  # seconds
DEFAULT_RETRIES = 3  # times
USER_AGENTS = {
    "default": "GameChangerBot/0.1",
    "macos_chrome": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
}


class TimeoutHTTPAdapter(HTTPAdapter):
    """HTTPAdapter with support for timeout setting"""

    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


class HttpResponseHooks:
    """Util class with various response callback functions"""

    @staticmethod
    def assert_status_hook(response: requests.Response, *args, **kwargs) -> None:
        response.raise_for_status()


class DefaultHttpSession(requests.Session):
    """Requests session with some sane defaults."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        retry_strategy = Retry(
            # number of retries
            total=DEFAULT_RETRIES,
            # backoff_factor determines delays according to ...
            #   :: {backoff factor} * (2 ** ({number of total retries} - 1))
            #   :: with factor = 1, retry backoff is ...
            #   :: 0.5, 1, 2, 4, 8, 16, 32, 64, 128, 256
            backoff_factor=1,
            # response codes on which to trigger retries
            # 429 - req rate limit exceeded
            status_forcelist=[429, 500, 502, 503, 504],
            # request methods on which to trigger retries
            method_whitelist=["HEAD", "GET", "OPTIONS"],
        )

        # adapter for handling http/https requests in this session
        adapter = TimeoutHTTPAdapter(
            timeout=DEFAULT_TIMEOUT, max_retries=retry_strategy
        )

        # set user agent header for every request
        self.headers.update({"User-Agent": USER_AGENTS["default"]})

        # register adapter as default for handling http/https
        self.mount("https://", adapter)
        self.mount("http://", adapter)

        # raise exception for "bad" response codes after retries run out
        self.hooks["response"] = [HttpResponseHooks.assert_status_hook]


class Requestor(ABC):
    """Adapter for making requests"""

    @abstractmethod
    def get_text(self, url: str) -> str:
        """Get text from page at URL"""
        pass


class DefaultRequestor(Requestor):
    def __init__(self):
        self.http = DefaultHttpSession()

    def get_text(self, url: str) -> str:
        resp = self.http.get(url,verify=False)
        return resp.text


class FileBasedPseudoRequestor(Requestor):
    """Pseudo adapter for making requests based on filenames
    :param fake_web_base_url: Fake url for directory root
    :param source_sample_dir_path: Path to directory with file samples
    """

    def __init__(self, fake_web_base_url: str, source_sample_dir_path: str):

        self.fake_web_base_url = fake_web_base_url.strip()

        if not Path(source_sample_dir_path).is_dir():
            raise ValueError("source_sample_dir_path should be an existing directory")
        self.source_sample_dir_path: Path = Path(source_sample_dir_path)

    def get_sample_file_at_fake_url(self, fake_url: str) -> Path:
        """Fetch path to a real file that corresponds to given fake url
        For example:
            fake_url = "https://example.local/articles/article_1.html" =>
                file_url = "/source_sample_dir/articles/article_1.html
        """
        real_file_path: Path = self.source_sample_dir_path.absolute().joinpath(
            "." + urlparse(fake_url).path
        )

        if real_file_path.is_file():
            return real_file_path
        else:
            raise ValueError(
                "Provided fake_url is not valid -> no file exists at real path: "
                + str(real_file_path)
            )

    def get_text(self, url: str) -> str:
        file_path = self.get_sample_file_at_fake_url(url)
        with open(file_path, "r") as f:
            return f.read()


class MapBasedPseudoRequestor(Requestor):
    """MapBasedPseudoRequestor always returns default text unless url matches a map
    :param default_text: text to return in response to any unmapped url
    :param url_text_map: function or dict that maps urls to specific text
    """

    def __init__(
        self,
        default_text: Optional[str] = None,
        url_text_map: Optional[Union[Callable[[str], str], Dict[str, str]]] = None,
    ):
        self.default_text = default_text
        self.url_text_map = url_text_map

    def get_text(self, url: str) -> str:
        mapped_text: Optional[str] = None

        if hasattr(self.url_text_map, '__call__'):
            mapped_text = self.url_text_map(url)  # type: ignore
        elif isinstance(self.url_text_map, dict):
            mapped_text = self.url_text_map.get(url, None)  # type: ignore

        response_text = mapped_text or self.default_text
        if not response_text:
            raise KeyError("No text defined for this URL: {}".format(url))
        else:
            return response_text
