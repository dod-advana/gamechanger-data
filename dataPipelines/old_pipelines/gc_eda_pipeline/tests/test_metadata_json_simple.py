import os
import json
import click
from dataPipelines.gc_eda_pipeline.metadata.metadata_json_simple import metadata_extraction


@click.command()
@click.option(
    '--file-input',
    required=False,
    type=str,
    default=""
)

def run(file_input: str):

    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    file_input = "/test/EDAPDF-00AF985C0EC44D12E05400215A9BA3BA-H9222210D0016-0015-empty-01-PDS-2014-08-15.pdf"

    staging_folder = "/Users/vikramhakkal/Development/tmp/gamechanger/eda"
    aws_s3_output_pdf_prefix = "bronze/gamechanger/projects/eda/pdf"
    is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, data = metadata_extraction(staging_folder, file_input, data_conf_filter, aws_s3_output_pdf_prefix, False)

    json_object = json.dumps(data, indent=4)
    print(json_object)


def read_extension_conf() -> dict:
    ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
    with open(ext_app_config_name) as json_file:
        data = json.load(json_file)
    return data

if __name__ == '__main__':
    run()


