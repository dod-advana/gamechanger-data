import click
from dataPipelines.gc_manual_metadata.gc_manual_metadata import ManualMetadata


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '-i',
    '--input-directory',
    help='where files reside',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--document-group',
    type=str,
    default=False,
    show_default=True,
    help="default metadata entries to use from config"
)

def run (input_directory: str, document_group:str) -> None:

    meta = ManualMetadata(
        input_directory=input_directory,
        document_group=document_group
    )

    meta.create_metadata()

