# -*- coding: utf-8 -*-
import scrapy
from dataPipelines.gc_scrapy.gc_scrapy.runspider_settings import general_settings


class GCSpider(scrapy.Spider):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    custom_settings = general_settings
