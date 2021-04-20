import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import click
from dataPipelines.gc_eda_pipeline.metadata import metadata_extraction


@click.command()
@click.option(
    '--file-input',
    required=False,
    type=str,
    default=""
)

def run(file_input: str):
    print("Hello World")

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    staging_folder = "/Users/vikramhakkal/Development/tmp/gamechanger/eda"
    aws_s3_output_pdf_prefix = "gamechanger/projects/eda/pdf"
    is_md_successful, md_type, data = metadata_extraction(staging_folder, file_input, data_conf_filter, aws_s3_output_pdf_prefix, False)

    json_object = json.dumps(data, indent=4)
    print(json_object)



def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data

if __name__ == '__main__':
    run()