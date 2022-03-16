import click
from .tools.cli import tools_cli
from .pipelines.cli import pipelines_cli


@click.group(name='gci')
def cli():
    """Running stuff and things"""
    pass


cli.add_command(tools_cli)
cli.add_command(pipelines_cli)