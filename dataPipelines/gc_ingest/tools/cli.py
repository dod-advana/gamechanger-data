import click
from .load.cli import load_cli
from .checkpoint.cli import checkpoint_cli
from .snapshot.cli import snapshot_cli
from .db.cli import db_cli
from .metadata.cli import metadata_cli


@click.group(name="tools")
def tools_cli():
    """Run individual steps"""
    pass


tools_cli.add_command(load_cli)
tools_cli.add_command(snapshot_cli)
tools_cli.add_command(checkpoint_cli)
tools_cli.add_command(db_cli)
tools_cli.add_command(metadata_cli)
