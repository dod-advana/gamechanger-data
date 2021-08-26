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
@click.option(
    '-s',
    '--shrink-factor',
    help="Factor to reduce image sizes. Reduces by a factor of 2^s",
    required=False,
    type=int,
    default=1
)
@click.option(
    '-m',
    '--max-workers',
    help="Number of workers for multiprocessing",
    required=False,
    type=int,
    default=1
)
def process(
        input_directory: str,
        output_directory: str,
        shrink_factor: int,
        max_workers: int) -> None:
    """Run Thumbnail Retrieval"""
    input_directory = Path(input_directory).resolve()
    output_directory = Path(output_directory).resolve()
    png_generator = ThumbnailsCreator(
        input_directory=input_directory,
        output_directory=output_directory,
        shrink_factor=shrink_factor,
        max_workers=max_workers
    )
    result = png_generator.process_directory()

