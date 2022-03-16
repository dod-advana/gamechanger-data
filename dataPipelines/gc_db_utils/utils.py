from pathlib import Path
import typing as t
import sqlalchemy
import psycopg2.extensions as pg2ext


def truncate_table(db_engine: sqlalchemy.engine.Engine, table: str, schema: str = 'public', cascade: bool = False) -> None:
    """Truncate given table"""
    db_engine.execute(f"TRUNCATE TABLE {schema + '.' + table} {'CASCADE' if cascade else ''}")


def export_to_csv(db_engine: sqlalchemy.engine.Engine, table_or_view: str, output_file: t.Union[Path, str], schema: str = 'public') -> None:
    """Export table/view to a csv file"""
    output_file = Path(output_file).resolve()
    con: pg2ext.connection = db_engine.raw_connection()
    cur: pg2ext.cursor = con.cursor()
    query = f"COPY {schema + '.' + table_or_view} TO STDOUT WITH (FORMAT CSV, HEADER, DELIMITER ',')"

    with output_file.open(mode="wb") as fd:
        cur.copy_expert(sql=query, file=fd)


def import_from_csv(db_engine: sqlalchemy.engine.Engine, input_file: t.Union[Path, str], table: str, schema: str = 'public') -> None:
    """Import csv file into given table"""
    input_file = Path(input_file).resolve()
    con: pg2ext.connection = db_engine.raw_connection()
    cur: pg2ext.cursor = con.cursor()
    query = f"COPY {schema + '.' + table} FROM STDIN WITH (FORMAT CSV, HEADER, DELIMITER ',')"

    with input_file.open(mode="rb") as fd:
        cur.copy_expert(sql=query, file=fd)
        con.commit()


def check_if_table_or_view_exists(db_engine: sqlalchemy.engine.Engine, table_or_view: str, schema: str = 'public') -> bool:
    """Check if table or view exists in the db
    :param db_engine: PostgreSQL db engine
    :param table_or_view: table_or_view to read from
    :param schema: table_or_view schema
    """
    query = f"""
            SELECT 1 FROM INFORMATION_SCHEMA.tables WHERE table_schema = '{schema}' AND table_name = '{table_or_view}'
            UNION ALL
            SELECT 1 FROM INFORMATION_SCHEMA.views WHERE table_schema = '{schema}' AND table_name = '{table_or_view}';
        """

    r = db_engine.execute(query)
    if r.fetchall():
        return True
    else:
        return False