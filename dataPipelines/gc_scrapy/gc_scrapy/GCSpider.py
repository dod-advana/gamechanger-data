# -*- coding: utf-8 -*-
import scrapy
from urllib.parse import urljoin, urlparse
from os.path import splitext

from dataPipelines.gc_scrapy.gc_scrapy.runspider_settings import general_settings


class GCSpider(scrapy.Spider):
    """
        Base Spider with settings automatically applied and some utility methods
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    custom_settings = general_settings

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
    def url_encode_spaces(href_raw):
        return href_raw.replace(' ', '%20')
