import click
from gamechangerml.train.pipeline import Pipeline


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--corpus-location",
    "-c",
    help="Directory location",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    required=False,
)
@click.option(
    "--upload",
    "-u",
    help="Upload to S3 flag",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "--sample-rate",
    "-s",
    help="Sample rate for training (0.0, 1.0]",
    type=click.FloatRange(min=0.0, max=1.0, min_open=True),
    required=False,
)
def create_topics(corpus_location, upload, sample_rate):
    print("Running create topics CLI with params")
    print(f"\tcorpus_location:", corpus_location)
    print(f"\tupload:", upload)
    print(f"\tsample_rate:", sample_rate)

    pipeline = Pipeline()
    pipeline.create_topics(
        corpus_dir=corpus_location, sample_rate=sample_rate, upload=upload
    )

