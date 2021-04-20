import click
import sys
from typing import Optional
from io import TextIOBase
from scrapy import spiderloader
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
#import quote.quote.settings as settings


@click.group()
def cli():
    pass


@cli.command()
@click.option('--crawler', help='JSON output file', type=str)
def run(crawler:Optional[str]) -> None:

    setting = get_project_settings()
    process = CrawlerProcess(setting)

    spider_loader = spiderloader.SpiderLoader.from_settings(setting)
    if crawler:
        if crawler in spider_loader.list():
            # run only the crawler name provided
            print("Running spider %s" % (crawler))
            process.crawl(crawler)
        else:
            print(" %s crawler not implemented." %(crawler))
            return

    else:
        print(spider_loader.list())
        for spider_name in spider_loader.list():
            print("Running spider %s" % (spider_name))
            process.crawl(spider_name)

    process.start()


