import click
from enum import Enum
from dev_tools.universal_test_harness.config import Config
import sqlalchemy
from pathlib import Path
import typing as t


@click.group('pg')
def pg_cli():
    """PG Tools"""
    pass


@pg_cli.command('reset')
def reset():
    """Init PG Schema/Tables"""

    def run_sql(sql_path: t.Union[Path, str], engine: sqlalchemy.engine.Engine):
        sql_path = Path(sql_path)
        if not sql_path.is_file():
            raise ValueError(f"There is no file at path {sql_path!s}")

        with sql_path.open("r") as fd:
            sql = fd.read()

        engine.execute(sql)

    print("Recreating Web & Orch Schemas/Tables")
    Config.ch.init_dbs(create_schema=True, drop_existing_schema=True)
    print("Recreating gc_assists table")
    run_sql(sql_path=Path(Config.DATA_PATH, 'sql/gc_assists.sql'), engine=Config.ch.web_db_engine)


class PeekChoice(Enum):
    WEB='web'
    ORCH='orch'
    ALL='all'


@pg_cli.command('peek')
@click.argument(
    'where',
    type=click.Choice([e.value for e in PeekChoice]),
    default=PeekChoice.ALL.value
)
@click.option(
    '--limit',
    type=int,
    default=5
)
def peek(where: str, limit: int):
    """Peek at pg table contents"""
    peek_limit = limit

    def peek_table(table_name: str, session):
        res = session.execute('select count(*) from ' + table_name)
        print(F"\n\n[count] {table_name} ::")
        for r in res.fetchall():
            print(r)

        res = session.execute('select * from ' + table_name + f' limit {peek_limit}')
        print(f"\n\n[top {peek_limit} hits] {table_name} ::")
        for r in res.fetchall():
            print(r)

    def peek_orch():
        with Config.ch.orch_db_session_scope('ro') as session:
            peek_table('publications', session)
            peek_table('versioned_docs', session)
            peek_table('gc_document_corpus_snapshot_vw', session)

    def peek_web():
        with Config.ch.web_db_session_scope('ro') as session:
            peek_table('gc_document_corpus_snapshot', session)
            peek_table('dafa_charter_map', session)
            peek_table('dafa_charter_map_flattened_vw', session)
            peek_table('gc_assists', session)

    if PeekChoice(where) == PeekChoice.ORCH:
        peek_orch()
    if PeekChoice(where) == PeekChoice.WEB:
        peek_web()
    if PeekChoice(where) == PeekChoice.ALL:
        peek_orch()
        peek_web()