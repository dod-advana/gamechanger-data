import click
import sys
from typing import Optional
from .models import NavyReservesCrawler, FakeNavyReservesCrawler
from io import TextIOBase

from dataPipelines.gc_crawler.utils import close_driver_windows_and_quit
from . import driver



@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '--output',
    help='JSON output file',
    type=click.File("w")
)
@click.option(
    '--no-validation',
    help='Turn off json schema validation',
    is_flag=True
)
@click.option(
    '--fake-run',
    help='Fake run against locally downloaded source sample',
    is_flag=True
)
def run(fake_run: bool, no_validation: bool, output: Optional[TextIOBase]) -> None:

    crawler = (
        NavyReservesCrawler()
        if not fake_run
        else FakeNavyReservesCrawler()
    )

    results = (
        crawler.iter_output_json()
        if no_validation
        else crawler.iter_validated_output_json()
    )

    output_sink = output or sys.stdout

    for json_doc in results:
        output_sink.write(json_doc + "\n")

    close_driver_windows_and_quit(driver)
