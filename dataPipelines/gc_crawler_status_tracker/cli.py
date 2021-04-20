import click
from dataPipelines.gc_crawler_status_tracker.gc_crawler_status_tracker import CrawlerStatusTracker
from datetime import datetime as dt


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '-i',
    '--index-name',
    help='The Elasticsearch Schema that will be used and updated',
    default="elasticsearch",
    required=True
)
@click.option(
    '--input-json',
    help='Crawler output json to determine revocations',
    type=click.Path(exists=False, file_okay=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--update-es',
    type=bool,
    default=False,
    show_default=True,
    help="Update Elasticsearch with revocation flags"
)
@click.option(
    '--update-db',
    type=bool,
    default=False,
    show_default=True,
    help="Update gc_orchestration database with revocation flags"
)
def revoke(index_name: str, input_json, update_es, update_db) -> None:

    revoker = CrawlerStatusTracker(
        input_json=input_json
    )

    revoker.handle_revocations(index_name = index_name, update_es = update_es, update_db = update_db)


@cli.command()
@click.option(
    '--input-json',
    help='Crawler output json to determine revocations',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    required=True
)
@click.option(
    '--update-db',
    type=bool,
    default=False,
    show_default=True,
    help="Update gc_orchestration database with revocation flags"
)
@click.option(
    '-s',
    '--status',
    help='status of crawlers',
    default="In Progress",
    required=True
)

def update_status(input_json, update_db, status) -> None:

    crawler_status_tracker = CrawlerStatusTracker(
        input_json=input_json
    )

    crawler_status_tracker.update_crawler_status(status=status, timestamp=dt.now(), update_db=update_db)

