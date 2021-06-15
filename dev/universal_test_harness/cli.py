import click
from .tools.es import es_cli, purge as purge_es
from .tools.s3 import s3_cli, reset as reset_s3
from .tools.pg import pg_cli, reset as reset_pg
from .tools.neo import neo4j_cli, purge as purge_neo4j
from .config import Config
from pathlib import Path
import shutil


@click.group()
def cli():
    """Pipeline testing tools"""
    pass


cli.add_command(es_cli)
cli.add_command(s3_cli)
cli.add_command(pg_cli)
cli.add_command(neo4j_cli)


@cli.command(name='setup')
@click.option(
    '-t',
    '--test-dir',
    type=click.Path(
        dir_okay=True,
        file_okay=False,
        resolve_path=True
    ),
    help="Base directory for hierarchy of job test subdirectories",
    default=Config.DEFAULT_LOCAL_TEST_PATH
)
@click.option(
    '-f',
    '--force',
    is_flag=True,
    help="Recreate test directory if already exists"
)
@click.pass_context
def setup(ctx: click.Context, test_dir: str, force: bool):
    """Configure backends and local directories for testing"""
    ctx.invoke(purge_es)
    ctx.invoke(purge_neo4j)
    ctx.invoke(reset_pg)
    ctx.invoke(reset_s3)

    test_dir_p = Path(test_dir)
    if test_dir_p.is_dir() and force:
        shutil.rmtree(str(test_dir_p))

    print(f"[INFO] Populating local test dirs under: {test_dir_p!s}")

    raw_dir_p = Path(test_dir_p, 'raw')
    parsed_dir_p = Path(test_dir_p, 'parsed')
    thumbnail_dir_p = Path(test_dir_p, 'thumbnails')
    job_dir_p = Path(test_dir_p, 'job')

    test_dir_p.mkdir(exist_ok=True)
    raw_dir_p.mkdir(exist_ok=True)
    parsed_dir_p.mkdir(exist_ok=True)
    thumbnail_dir_p.mkdir(exist_ok=True)
    job_dir_p.mkdir(exist_ok=True)

    for d in [p for p in Path(Config.CRAWLER_OUTPUT_PATH).iterdir() if p.is_dir()]:
        shutil.copytree(str(d), str(Path(raw_dir_p, d.name)))
        Path(parsed_dir_p, d.name).mkdir(exist_ok=True)
        Path(thumbnail_dir_p, d.name).mkdir(exist_ok=True)
