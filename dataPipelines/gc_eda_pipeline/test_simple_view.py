import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import click
from dataPipelines.gc_eda_pipeline.metadata_simple_view import metadata_extraction


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

    #file_input = "/sfasdf/gfsafds/EDAPDF-ad290457-4e43-4276-9e6e-1587d41196f5-N0018918DZ067-N0018919FZ062-empty-P00004-PDS-2019-11-20.pdf" # ONLY PDS
    # file_input = "/sfasdf/gfsafds/EDAPDF-00964DCE18980E0EE05400215A9BA3BA-N0060412A3000-empty-empty-P00005-PDS-2014-08-14.pdf" # ONLY SYN
    #file_input = "/sfasdf/gfsafds/EDAPDF-001D97D62A432FE6E05400215A9BA3BA-N6523609D3808-empty-empty-P00025-PDS-2014-08-08.pdf" # IN Both SYBN and PDS

    # file_input = "/sfasdf/gfsafds/EDAPDF-0C00C8166F006949E05400215A9BA3BA-SP070003D1380-0523-empty-16-PDS-2015-01-06.pdf" # ONLY SYN (modified data)

    file_input = "/sfasdf/gfsafds/EDAPDF-1BF94F7DBB842A4DE05400215A9BA3B8-FA150010D0004-0008-empty-17-PDS-2015-07-28.pdf"

    aws_s3_output_pdf_prefix = "gamechanger/projects/eda/pdf"
    staging_folder = "don't really need"
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