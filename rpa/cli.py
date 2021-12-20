import click
from rpa.edl_zip_mover import move_zips
from rpa.rpa_landing_zone_mover import filter_and_move


@click.group()
def cli():
    pass


@cli.command()
def move_from_edl():
    move_zips()


@cli.command()
def filter_move():
    filter_and_move()
