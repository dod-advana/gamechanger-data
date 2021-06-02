import click

from .utils import ThumbnailsCreator
import typing as t

####
# CLI
####

@click.group()
def cli():
    pass


@cli.command(name='process')
@click.option(
    '-f',
    '--file-name',
    help="Name of the file you're extracting the thumbnail from",
    type=str,
    required=True,
)
@click.option(
    '-o',
    '--output-directory',
    help="Path for the output directory",
    required=False,
    type=str,
    default="./"
)
def process(
        file_name: str,
        output_directory: t.Optional[str]) -> None:
    """Run Thumbnail Retrieval"""
    png_generator = ThumbnailsCreator(
        file_name=file_name,
        output_directory=output_directory
    )
    result = png_generator.generate_png()

