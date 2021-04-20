import click
import sys
from typing import Optional
from .models import ExampleCrawler, FakeExampleCrawler
from io import TextIOBase


@click.group()
def cli():
    pass


@cli.command()
@click.option('--output', help='JSON output file', type=click.File("w"))
@click.option('--no-validation', help='Turn off json schema validation', is_flag=True)
@click.option(
    '--fake-run', help='Fake run against locally downloaded source sample', is_flag=True
)
@click.option(
    "--starting-url", help="Parser starting url", default="http://localhost:8000"
)
def run(
    fake_run: bool, no_validation: bool, starting_url: str, output: Optional[TextIOBase]
) -> None:

    crawler = (
        ExampleCrawler(starting_url=starting_url)
        if not fake_run
        else FakeExampleCrawler()
    )

    results = (
        crawler.iter_output_json()
        if no_validation
        else crawler.iter_validated_output_json()
    )

    output_sink = output or sys.stdout

    for json_doc in results:
        output_sink.write(json_doc + "\n")
