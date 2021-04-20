import subprocess as sub
import pandas as pd
from textwrap import dedent
from typing import Iterable, Dict, Any, Generator, Union, Optional
from datetime import datetime
from pathlib import Path
import json
import click
from enum import Enum
import re
import copy

TABLE_NAME = "gc_document_corpus_snapshot"
CREATE_TABLE_CMD = dedent(f"""\
    CREATE TABLE {TABLE_NAME} (
        doc_id INTEGER PRIMARY KEY,
        pub_id INTEGER UNIQUE,
        pub_name VARCHAR(512) UNIQUE,
        pub_title VARCHAR(512) NOT NULL,
        pub_type VARCHAR(512) NOT NULL,
        pub_number VARCHAR(512) NOT NULL,
        doc_filename VARCHAR(512),
        doc_s3_location VARCHAR(512),
        upload_date TIMESTAMP,
        publication_date TIMESTAMP
    );
""")
DROP_TABLE_CMD = f"DROP TABLE IF EXISTS {TABLE_NAME} CASCADE;"


class SnapshotEntry:
    MAX_TITLE_LENGTH=100

    def __init__(self,
                 doc_id: int,
                 pub_id: int,
                 pub_name: str,
                 pub_title: str,
                 pub_type: str,
                 pub_number: str,
                 doc_filename: str,
                 doc_s3_location: str,
                 upload_date: datetime,
                 publication_date: datetime):

        str_filter = lambda _s: re.sub(r"""[^0-9a-zA-Z_ ,&.-]""", "", _s)

        self.doc_id = doc_id
        self.pub_id = pub_id
        self.pub_name = str_filter(pub_name)
        self.pub_title = str_filter(pub_title)
        if len(self.pub_title) > SnapshotEntry.MAX_TITLE_LENGTH:
            self.pub_title = self.pub_title[:SnapshotEntry.MAX_TITLE_LENGTH] + "..."

        self.pub_type = str_filter(pub_type)
        self.pub_number = str_filter(pub_number)
        self.doc_filename = str_filter(doc_filename)
        self.doc_s3_location = str_filter(doc_s3_location)
        self.upload_date = upload_date
        self.publication_date = publication_date

    def to_insert_dml(self, table: str) -> str:
        return (dedent("""\
            INSERT INTO {table} (
                doc_id, pub_id, pub_name, pub_title,
                pub_type, pub_number, doc_filename,
                doc_s3_location, upload_date, publication_date
            )
            VALUES
            (
                {doc_id}, {pub_id}, '{pub_name}', '{pub_title}',
                '{pub_type}', '{pub_number}', '{doc_filename}',
                '{doc_s3_location}', {upload_date}, {publication_date}
            )
            ON CONFLICT (pub_name) DO NOTHING
            ;
            """.format(
                table=table,
                doc_id=self.doc_id,
                pub_id=self.pub_id,
                pub_name=self.pub_name,
                pub_title=self.pub_title,
                pub_type=self.pub_type,
                pub_number=self.pub_number,
                doc_filename=self.doc_filename,
                doc_s3_location=self.doc_s3_location,
                upload_date=(
                    ( "'" + self.upload_date.strftime("%Y-%m-%d %H:%M:%S") + "'" + "::TIMESTAMP")
                    if self.upload_date else "NULL"
                ),
                publication_date=(
                    ("'" + self.publication_date.strftime("%Y-%m-%d %H:%M:%S") + "'" + "::TIMESTAMP")
                    if self.publication_date else "NULL"
                )
            )
        ))

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        try:
            return pd.to_datetime(date_str).to_pydatetime()
        except:
            return None

    @classmethod
    def from_metadata_dict(
            cls,
            d: Dict[str, Any],
            pub_id: Union[Generator[int, None, None], int],
            doc_id: Union[Generator[int, None, None], int]
    ) -> 'SnapshotEntry':
        return SnapshotEntry(
            doc_id=doc_id if isinstance(doc_id, int) else next(doc_id),
            pub_id=pub_id if isinstance(pub_id, int) else next(pub_id),
            pub_name=d['doc_name'],
            pub_title=d['doc_title'],
            pub_type=d['doc_type'],
            pub_number=d['doc_num'],
            doc_filename='',
            doc_s3_location='',
            upload_date=datetime(2020,9,18,12,0,0),
            publication_date=cls.parse_date(d['publication_date'])
        )


    @classmethod
    def from_es_dict(
            cls,
            d: Dict[str, Any],
            pub_id: Union[Generator[int, None, None], int],
            doc_id: Union[Generator[int, None, None], int]
    ) -> 'SnapshotEntry':
        return SnapshotEntry(
            doc_id=doc_id if isinstance(doc_id, int) else next(doc_id),
            pub_id=pub_id if isinstance(pub_id, int) else next(pub_id),
            pub_name=d['doc_type'] + " " + d['doc_num'],
            pub_title=(
                d['title']
                if d['title'].upper() != 'NA'
                else  (d['doc_type'] + " " + d['doc_num'])
            ),
            pub_type=d['doc_type'],
            pub_number=d['doc_num'],
            doc_filename='',
            doc_s3_location='',
            upload_date=datetime(2020, 7, 1, 12, 0, 0),
            publication_date=(
                    cls.parse_date(d['change_date'])
                    or cls.parse_date(d['init_date'])
            ),
        )


def consec_gen(start:int = 0) -> Generator[int, None, None]:
    current = start
    while True:
        yield current
        current += 1


def iter_entries_from_es_jsons(
        base_dir: Union[Path, str],
        pub_id_gen: Generator[int, None, None] = consec_gen(2600),
        doc_id_gen: Generator[int, None, None] = consec_gen(2600)
    ) -> Iterable[SnapshotEntry]:
    pub_names_so_far = []

    base_dir_path = Path(base_dir).resolve()
    for fp in base_dir_path.glob("*.json"):
        with fp.open(mode='r') as fd:
            entry = SnapshotEntry.from_es_dict(
                d=json.load(fd),
                pub_id=pub_id_gen,
                doc_id=doc_id_gen
            )

            if entry.pub_name in pub_names_so_far:
                continue
            else:
                pub_names_so_far.append(entry.pub_name)
                yield entry


def iter_entries_from_metadata(
        base_dir: Union[Path, str],
        pub_id_gen: Generator[int, None, None] = consec_gen(),
        doc_id_gen: Generator[int, None, None] = consec_gen()
    ) -> Iterable[SnapshotEntry]:
    pub_names_so_far = []

    base_dir_path = Path(base_dir).resolve()

    for fp in base_dir_path.glob("*.metadata"):
        with fp.open(mode="r") as fd:
            entry = SnapshotEntry.from_metadata_dict(
                d=json.load(fd),
                pub_id=pub_id_gen,
                doc_id=doc_id_gen
            )
            if entry.pub_name in pub_names_so_far:
                continue
            else:
                pub_names_so_far.append(entry.pub_name)
                yield entry


def get_ddl_cmds():
    yield from [DROP_TABLE_CMD, CREATE_TABLE_CMD]


def get_dml_cmds(entries: Iterable[SnapshotEntry], table: str = TABLE_NAME):
    for entry in entries:
        yield entry.to_insert_dml(table=table)

class InputJSONType(Enum):
    METADATA = 'metadata-json'
    ES = 'es-json'

@click.command()
@click.option(
    '-s',
    '--source-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help='Dir where ES jsons or metadata jsons are located',
    required=True
)
@click.option(
    '-t',
    '--json-type',
    type=click.Choice([t.value for t in InputJSONType]),
    help='Input json type',
    required=True
)
@click.option(
    '--table-name',
    type=str,
    help='Fully qualified name of the table where entries will be inserted',
    default='gc_document_corpus_snapshot',
    show_default=True
)
@click.option(
    '--ddl',
    is_flag=True,
    help="Also output drop/create table statements"
)
def cli(source_dir: str, json_type: str, table_name: str, ddl: bool) -> None:
    """Generates sql statements to populate corpus snapshot table"""
    collapse = lambda s: re.sub(r"(\s+)"," ",s)

    if ddl:
        for c in get_ddl_cmds():
            print(collapse(c))

    if InputJSONType(json_type) == InputJSONType.METADATA:
        for c in get_dml_cmds(
            table=table_name,
            entries=iter_entries_from_metadata(base_dir=source_dir)
        ):
            print(collapse(c))
    elif InputJSONType(json_type) == InputJSONType.ES:
        for c in get_dml_cmds(
                table=table_name,
                entries=iter_entries_from_es_jsons(base_dir=source_dir)
        ):
            print(collapse(c))


if __name__ == '__main__':
    cli()