from time import perf_counter
import click
import csv
from elasticsearch import helpers
from .conf import Conf
from collections import OrderedDict
import pandas as pd
import numpy as np
import tempfile
import re
import datetime

coauth_re = re.compile('CoAuthor(?P<kind>.*\D)(?P<num>\d+)')


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '-f',
    '--filepath',
    help="The location of the csv file to be indexed",
    required=True,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        allow_dash=False
    ),
)
def run(filepath: str):
    print("Starting Gamechanger CDO Pipeline")
    start = perf_counter()
    # Download PDF and metadata files

    csv_ingest(filepath)

    end = perf_counter()
    print(f'Total time -- It took {end - start} seconds!')
    print("DONE!!!!!!")


def format_gen(reader: csv.DictReader):
    for row in reader:
        item = OrderedDict({})
        coauthors = [{} for _ in range(20)]
        for key, val in row.items():

            matches = coauth_re.search(key)
            if matches:
                num, kind = matches.group('num'), matches.group('kind')
                coauthors[int(num)-1][kind] = val

            else:
                item[key] = val

        item['CoAuthors'] = list(filter(lambda x: x['ID'], coauthors))
        yield item


def csv_ingest(filepath: str):
    es = Conf.ch.es_client
    df = pd.read_csv(filepath, encoding="ISO-8859-1")
    df = df[df.columns[2:]]
    # NaN space only values
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    # NaN "empty" string values
    df.replace("empty", np.nan, regex=True, inplace=True)

    with tempfile.TemporaryFile(mode="r+") as f:
        df.to_csv(f, index=False)
        f.seek(0)

        reader = csv.DictReader(f)
        formatted = format_gen(reader)

        ts = datetime.datetime.now().strftime('%Y%m%d')
        index = f'gc-cdo_{ts}'
        helpers.bulk(es, formatted, index=index)
        body = {
            "actions": [
                {"remove": {"index": 'gc-cdo_*', "alias": 'gc-cdo'}},
                {"add": {"index": index, "alias": 'gc-cdo'}}
            ]
        }
        es.indices.update_aliases(body)
