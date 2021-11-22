import click
from pathlib import Path
from configuration.enums import ConfigurationEnvVar
from common.utils.file_utils import walk_files, ensure_dir
import shutil
from . import TEMPLATE_DIR, RENDERED_DIR
from .defaults import TEMPLATE_FILENAME_SUFFIX
from .utils import get_config_renderer_from_env, get_connection_helper_from_env
import typing as t
import sys
import os
from common.utils.timeout_utils import raise_on_timeout, ContextTimeout

@click.group()
def cli():
    """Config management CLI"""
    pass


@cli.command(name="clean")
def clean_cmd() -> None:
    """Clean up old rendered configs"""

    if Path(RENDERED_DIR).exists():
        for root, dirs, files in os.walk(RENDERED_DIR):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    print(f"[OK] Old rendered directory tree removed: {RENDERED_DIR}")


@cli.command(name="init")
@click.pass_context
@click.option(
    "--app-config",
    help="Application configuration env",
    type=click.STRING,
    required=False,
    envvar=ConfigurationEnvVar.APP_CONFIG_NAME.value
)
@click.option(
    "--ext-app-config-path",
    help="Path to arbitrary app config file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    envvar=ConfigurationEnvVar.APP_EXT_CONFIG_NAME.value,
    required=False
)
@click.option(
    "--elasticsearch-config",
    help="Elasticsearch configuraiton env",
    type=click.STRING,
    required=False,
    envvar=ConfigurationEnvVar.ES_CONFIG_NAME.value
)
@click.argument(
    'overall_env',
    type=click.STRING,
    required=True
)
def init_cmd(
        ctx: click.Context,
        app_config: t.Optional[str],
        ext_app_config_path: t.Optional[t.Union[str, Path]],
        elasticsearch_config: t.Optional[str],
        overall_env: str) -> None:
    """Initialize configuration files"""

    app_config = app_config or overall_env
    elasticsearch_config = elasticsearch_config or overall_env
    print(f"CONFIG ::>\n\tapp_config is {app_config}\n\tes_config is {elasticsearch_config}\n\text_app_config_path is {ext_app_config_path}")

    # if ext config path is specified, use that and don't pass app config name
    r = get_config_renderer_from_env(
        es_config_name=elasticsearch_config,
        **(dict(app_ext_config_path=ext_app_config_path) if ext_app_config_path else dict(app_config_name=app_config))  # type: ignore
    )

    # first, we clean up
    ctx.invoke(clean_cmd)

    for src_file in walk_files(TEMPLATE_DIR):
        # get output path relative rendered dir
        dst_file = Path(RENDERED_DIR, str(src_file.relative_to(TEMPLATE_DIR)))
        ensure_dir(dst_file.parent)

        # process templated files
        if dst_file.suffix == TEMPLATE_FILENAME_SUFFIX:
            # lose the suffix
            dst_file = Path(dst_file.parent, dst_file.stem)
            with dst_file.open("w") as f:
                f.write(r.render_configured(src_file))
        else:
            shutil.copy(src_file, dst_file)

    print(f"[OK] Configuration files rendered/copied from {TEMPLATE_DIR} to {RENDERED_DIR}")


@cli.command(name="configure-backend")
@click.option(
    '--drop-existing-db-schema',
    type=bool,
    default=False,
    help="Drop relevant tables/views from all configured databases",
    show_default=True
)
def setup_db(drop_existing_db_schema: bool):
    """Setup backend for the env"""
    print("Setting up the backend (db, etc.)")
    ch = get_connection_helper_from_env()
    ch.init_dbs(create_schema=True, drop_existing_schema=drop_existing_db_schema)


@cli.command(name="check-connections")
def check_connections():
    """Validate that configured connections are possible"""
    ch = get_connection_helper_from_env()
    check_timeout_secs=10

    print("\n\nSTARTING CONNECTION CHECKS\n")
    status_tracker: t.Dict[str, bool] = {}

    # check s3
    print('... checking S3 connection and bucket')
    status_tracker['s3_ok'] = False
    try:
        with raise_on_timeout(check_timeout_secs):
            try:
                s3_res = ch.s3_client.list_objects(Bucket=ch.conf['aws']['bucket_name'], Prefix='', Delimiter='/')
                if str(s3_res['ResponseMetadata']['HTTPStatusCode']).startswith('2'):
                    status_tracker['s3_ok'] = True
            except Exception as e:
                print(e)
    except ContextTimeout:
        print("Check timed out.")

    # check es
    print('... checking ElasticSearch')
    status_tracker['es_ok'] = False
    try:
        status_tracker['es_ok'] = True if ch.es_client.ping() else False
    except Exception as e:
        print(e)

    # check orch_db
    print('... checking Orch DB')
    status_tracker['orch_db_ok'] = False
    try:
        if ch.orch_db_engine.execute('select 666;').fetchall():
            status_tracker['orch_db_ok'] = True
    except Exception as e:
        print(e)

    # check web_db
    print('... checking Web DB')
    status_tracker['web_db_ok'] = False
    try:
        if ch.web_db_engine.execute('select 666;').fetchall():
            status_tracker['web_db_ok'] = True
    except Exception as e:
        print(e)

    # check neo4j
    print('... checking Neo4j')
    status_tracker['neo4j_ok'] = False
    try:
        with ch.neo4j_session_scope() as session:
            session.run("Match () Return 1 Limit 1")
            status_tracker['neo4j_ok'] = True
    except Exception as e:
        print(e)

    print("\n\nCONNECTION CHECKS FINISHED\n")

    print("\n".join((f'{k} - {v}' for k,v in status_tracker.items())))
    if not all(status_tracker.values()):
        print("\n[FAIL] Some checks failed, see earlier cmd output for more info", file=sys.stderr)
        exit(1)
    else:
        print("\n[OK] All checks passed")