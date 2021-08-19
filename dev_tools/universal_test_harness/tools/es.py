import click
from dev_tools.universal_test_harness.config import Config
from functools import reduce
from enum import Enum


@click.group('es')
def es_cli():
    """ES Tools"""
    pass


class PurgeChoice(Enum):
    ALIAS = 'alias'
    INDEX = 'index'
    ALL = 'all'


@es_cli.command('purge')
@click.argument(
    'purge_choice',
    type=click.Choice([e.value for e in PurgeChoice]),
    default=PurgeChoice.ALL.value
)
def purge(purge_choice: str):
    """Purge all indexes/aliases"""

    es = Config.ch.es_client

    aliases = list(reduce(
        lambda x,y: x+y,
        [list(v['aliases'].keys()) for k, v in es.indices.get_alias().items() if v.get('aliases')],
        []
    ))
    indices = es.indices.get('*').keys()
    exclude_patterns = ['kibana', 'apm']

    def purge_aliases():
        print("Purging aliases ::")
        for alias in [a for a in aliases if not any([pattern in a for pattern in exclude_patterns])]:
            print(f'Deleting alias :: {alias}')
            es.indices.delete_alias(index='_all', name=alias)

    def purge_indices():
        print("Puring indices")
        for index in [i for i in indices if not any([pattern in i for pattern in exclude_patterns])]:
            print(f'Deleting index :: {index}')
            es.indices.delete(index=index)

    if PurgeChoice(purge_choice) == PurgeChoice.ALIAS:
        purge_aliases()
    elif PurgeChoice(purge_choice) == PurgeChoice.INDEX:
        purge_indices()
    elif PurgeChoice(purge_choice) == PurgeChoice.ALL:
        purge_aliases()
        purge_indices()


@es_cli.command('peek')
@click.argument(
    'index_or_alias',
    type=str,
    required=False
)
@click.option(
    "--limit",
    type=int,
    default=10
)
def peek(index_or_alias: str, limit: int):
    """Peek at index/alias contents"""
    es = Config.ch.es_client
    max_fetch_size = limit

    print("ES Indices ::")
    for index in es.indices.get('*'):
        print(index)

    print("ES Aliases --> Indices ::")
    for line in (line for line in es.cat.aliases().split('\n') if line.strip()):
        print(line)

    if index_or_alias:
        res = es.search(
            body={
                    "query": {
                        "match_all": {}
                    },
                    "_source": ["filename", "doc_type", "doc_num", "paragraphs.par_raw_text_t"],
                    "from": 0,
                    "size": max_fetch_size
                },
            index=index_or_alias
        )
        print(f"Index/Alias Search - {index_or_alias} :: ")
        for l in [r['_source'] for r in res['hits']['hits']]:
            print(l)


@es_cli.command('alias')
@click.argument(
    "index_name",
    type=str
)
@click.argument(
    "alias_name",
    type=str
)
def alias(index_name: str, alias_name: str):
    """Alias index """
    es = Config.ch.es_client
    print(f"Setting index('{index_name}') to alias('{alias_name}') :: ")
    try:
        es.indices.put_alias(index=index_name, name=alias_name)
    except Exception as e:
        print(e)


@es_cli.command('unalias')
@click.argument(
    "alias_name",
    type=str
)
def unalias(alias_name: str):
    """Delete alias"""
    try:
        Config.ch.es_client.indices.delete_alias(index='_all', name=alias_name)
    except Exception as e:
        print(e)