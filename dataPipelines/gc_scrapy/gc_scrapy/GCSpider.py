# -*- coding: utf-8 -*-
import scrapy
import re
import typing
from urllib.parse import urljoin, urlparse
from os.path import splitext

from dataPipelines.gc_scrapy.gc_scrapy.runspider_settings import general_settings

url_re = re.compile("((http|https)://)(www.)?" +
                    "[a-zA-Z0-9@:%._\\+~#?&//=]" +
                    "{2,256}\\.[a-z]" +
                    "{2,6}\\b([-a-zA-Z0-9@:%" +
                    "._\\+~#?&//=]*)"
                    )


class GCSpider(scrapy.Spider):
    """
        Base Spider with settings automatically applied and some utility methods
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    custom_settings: dict = general_settings
    rotate_user_agent: bool = False
    randomly_delay_request: typing.Union[bool, range, typing.List[int]] = False

    @staticmethod
    def get_href_file_extension(url: str) -> str:
        """
            returns file extension if exists in passed url path, else UNKNOWN
            UNKNOWN is used so that if the website fixes their link it will trigger an update from the doc type changing
        """
        path = urlparse(url).path
        ext: str = splitext(path)[1].replace('.', '').lower()

        if not ext:
            return 'UNKNOWN'

        return ext

    @staticmethod
    def ascii_clean(text: str) -> str:
        """
            encodes to ascii, retaining non-breaking spaces and strips spaces from ends
            applys text.replace('\u00a0', ' ').encode('ascii', 'ignore').decode('ascii').strip()
        """

        return text.replace('\u00a0', ' ').replace('\u2019', "'").encode('ascii', 'ignore').decode('ascii').strip()

    @staticmethod
    def ensure_full_href_url(href_raw: str, url_base: str) -> str:
        """
            checks if href is relative and adds to base if needed
        """
        if href_raw.startswith('/'):
            web_url = urljoin(url_base, href_raw)
        else:
            web_url = href_raw

        return web_url

    @staticmethod
    def url_encode_spaces(href_raw: str) -> str:
        """
            encodes spaces as %20
        """
        return href_raw.replace(' ', '%20')

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
            checks if url is valid
        """
        return url_re.match(url)
