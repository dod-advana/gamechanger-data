import sys

from common.document_parser.lib.responsibility_parse import ResponsibilityParser
import argparse

"""
usage: responsibility_parser_cli.py [-h] --json-files-input-directory JSON_FILES_INPUT_DIRECTORY [--excel-save-filepath EXCEL_SAVE_FILEPATH] [--save-to-rds SAVE_TO_RDS] --postgres-user POSTGRES_USER
                                    --postgres-password POSTGRES_PASSWORD --postgres-db-name POSTGRES_DB_NAME --postgres-table-name POSTGRES_TABLE_NAME --postgres-hostname POSTGRES_HOSTNAME --postgres-port
                                    POSTGRES_PORT

"""

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="CLI tool for the Responsibility Section Parser")

    parser.add_argument(
        "--json-files-input-directory", "-i",
        dest="json_files_input_directory",
        required=True,
        help="Directory to the input directory for Gamechanger JSONs"
    )

    parser.add_argument(
        "--excel-save-filepath", "-e",
        dest="excel_save_filepath",
        required=False,
        default=None,
        help="Filepath (including diectory and filename) of the excel file that the responsibility explorer results should"
             "be saved to"
    )
    parser.add_argument(
        "--save-to-rds", "-s",
        dest="save_to_rds",
        required=False,
        action="store_true",
        help="Flag for saving to RDS"
    )

    postgres_info_required = False
    if any(flag in sys.argv for flag in ["--save-to-rds","-s"]):
        postgres_info_required=True
        print("** Save to RDS was selected, additional parameters are required for connecting to Postgres. **")

    parser.add_argument(
        "--postgres-user", "-u",
        dest="postgres_user",
        required=postgres_info_required,
        help="Username for Postgres Instance"
    )
    parser.add_argument(
        "--postgres-password", "-p",
        dest="postgres_password",
        required=postgres_info_required,
        help="Password for Postgres Instance"
    )
    parser.add_argument(
        "--postgres-db-name", "-d",
        dest="postgres_db_name",
        required=postgres_info_required,
        help="Database Name for RE results table to be stored"
    )
    parser.add_argument(
        "--postgres-table-name", "-t",
        dest="postgres_table_name",
        required=postgres_info_required,
        help="Table Name for RE results table to be stored"
    )
    parser.add_argument(
        "--postgres-hostname", "-n",
        dest="postgres_hostname",
        required=postgres_info_required,
        help="Hostname/IP for Postgres Instance"
    )
    parser.add_argument(
        "--postgres-port", "-o",
        dest="postgres_port",
        required=postgres_info_required,
        help="Port for Postgres Instance"
    )


    args = parser.parse_args()

    responsibility_parser = ResponsibilityParser()
    responsibility_parser.main(files_input_directory=args.json_files_input_directory,
                               excel_save_filepath=args.excel_save_filepath)


    if args.save_to_rds:
        from sqlalchemy import create_engine
        try:
            pg_conn_string = f'postgresql://{args.postgres_user}:{args.postgres_password}@{args.postgres_hostname}:' \
                             f'{args.postgres_port}/{args.postgres_db_name}'

            engine = create_engine(pg_conn_string)
            responsibility_parser.results_df.to_sql(args.postgres_table_name, engine, if_exists="replace", index=False)
            print(f"Successfully saved results to {args.postgres_table_name} table")
        except Exception as e:
            print(f"The connection string being used for connecting to postgres is {pg_conn_string} \n"
                  f"If this looks"
                  "Unable to save results table off to RDS, check that the following is True:\n"
                  "* Have necessary VPN connection\n"
                  "* Username/Password are valid for RDS instance\n"
                  "* Database supplied exists")
            raise e