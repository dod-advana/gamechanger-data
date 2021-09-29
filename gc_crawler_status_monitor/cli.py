import click
from gc_crawler_status_monitor.crawler_monitor import CrawlerMonitor


@click.group()
def cli():
    pass


@cli.command()
def run():
    print("CHECKING FOR STALE CRAWLERS")
    CrawlerMonitor().check_for_stale_statuses()
