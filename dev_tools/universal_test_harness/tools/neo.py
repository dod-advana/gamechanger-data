import click
from dev_tools.universal_test_harness.config import Config

@click.group('neo')
def neo4j_cli():
    """Neo4j Tools"""
    pass


@neo4j_cli.command('purge')
def purge():
    """Purge neo4j entities/relationships/constraints"""
    with Config.ch.neo4j_session_scope() as session:
        print("Deleting all entities, relationships, and constraints :: ", end="")
        session.run("match (n) detach delete n;")
        session.run("DROP CONSTRAINT unique_pubs IF EXISTS")
        session.run("DROP CONSTRAINT unique_docs IF EXISTS")
        session.run("DROP CONSTRAINT unique_ents IF EXISTS")
        session.run("DROP CONSTRAINT unique_resps IF EXISTS")
        print("[OK]")


@neo4j_cli.command('peek')
@click.option(
    '--limit',
    type=int,
    default=10
)
def peek(limit: int):
    """Peek at neo4j entities"""
    fetch_limit = limit
    with Config.ch.neo4j_session_scope() as session:
        for rec in session.run(f'MATCH (n) RETURN n LIMIT {fetch_limit}'):
            print(rec)
