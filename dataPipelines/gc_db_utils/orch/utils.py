from .models import DeferredOrchReflectedBase
from pathlib import Path
from . import PACKAGE_PATH
from typing import Union
import sqlalchemy


def run_sql_file(sql_subpath: Union[str, Path], engine: sqlalchemy.engine.Engine) -> None:
    sql_path = Path(PACKAGE_PATH, 'sql', sql_subpath).resolve()
    if not sql_path.is_file():
        raise ValueError(f"There is no file at path {sql_path!s}")

    with sql_path.open("r") as fd:
        sql = fd.read()

    engine.execute(sql)


def drop_views(engine: sqlalchemy.engine.Engine) -> None:
    run_sql_file('drop_views.sql', engine=engine)


def drop_tables(engine: sqlalchemy.engine.Engine) -> None:
    run_sql_file('drop_tables.sql', engine=engine)


def create_tables(engine: sqlalchemy.engine.Engine) -> None:
    run_sql_file('create_tables.sql', engine=engine)


def create_views(engine: sqlalchemy.engine.Engine) -> None:
    run_sql_file('create_views.sql', engine=engine)


def init_db_bindings(engine: sqlalchemy.engine.Engine) -> None:
    DeferredOrchReflectedBase.prepare(engine=engine)


def create_tables_and_views(engine: sqlalchemy.engine.Engine) -> None:
    create_tables(engine=engine)
    create_views(engine=engine)


def drop_tables_and_views(engine: sqlalchemy.engine.Engine) -> None:
    drop_tables(engine=engine)
    drop_views(engine=engine)


def recreate_tables_and_views(engine: sqlalchemy.engine.Engine) -> None:
    drop_tables_and_views(engine=engine)
    create_tables_and_views(engine=engine)
