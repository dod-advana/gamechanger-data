import click
from .core.cli import core_cli
from .clone.cli import clone_cli


@click.group(name='pipelines')
def pipelines_cli():
    """Pipeline CLI"""
    pass

pipelines_cli.add_command(core_cli)
pipelines_cli.add_command(clone_cli)