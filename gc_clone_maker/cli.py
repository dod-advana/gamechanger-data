import click
from gc_clone_maker.gc_clone_maker import CloneMaker


@click.group()
def cli():
    pass


@cli.command()
def run():
    print("GENERATING CLONE")
    CloneMaker().generate_clone()
