import click
from pathlib import Path
from .utils import ThumbnailsCreator
import typing as t
import os

####
# CLI
####

@click.group()
def cli():
    pass


@cli.command(name='process')
@click.option(
    '-i',
    '--input-directory',
    help="Input directory containing the PDFs you want to extract the thumbnails from",
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        exists=True,
        resolve_path=True
    ),
    required=True,
)
@click.option(
    '-o',
    '--output-directory',
    help="Path for the output directory",
    required=False,
    type=click.Path(dir_okay=True, resolve_path=True),
    default=os.path.abspath('.')
)
def process(
        input_directory: str,
        output_directory: str) -> None:
    """Run Thumbnail Retrieval"""
    input_directory = Path(input_directory).resolve()
    output_directory = Path(output_directory).resolve()
    png_generator = ThumbnailsCreator(
        input_directory=input_directory,
        output_directory=output_directory
    )
    result = png_generator.generate_thumbnails()

