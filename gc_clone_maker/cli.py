import click
from gc_clone_maker.gc_clone_maker import CloneMaker
from gc_clone_maker.clone_zip_mover import unzip_and_move


@click.group()
def cli():
    pass


@cli.command()
def run():
    print("GENERATING CLONE")
    CloneMaker().generate_clone()


@cli.command()
def edl_move():
    print("Moving EDL upload files")
    unzip_and_move()
