import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import click
from dataPipelines.gc_eda_pipeline.metadata_json import metadata_extraction


@click.command()
@click.option(
    '--file-input',
    required=False,
    type=str,
    default=""
)

def run(file_input: str):
    print("Hello World")


    #file_input = "/sfasdf/gfsafds/EDAPDF-ad290457-4e43-4276-9e6e-1587d41196f5-N0018918DZ067-N0018919FZ062-empty-P00004-PDS-2019-11-20.pdf" # ONLY PDS
    #file_input = "/sfasdf/gfsafds/EDAPDF-00964DCE18980E0EE05400215A9BA3BA-N0060412A3000-empty-empty-P00005-PDS-2014-08-14.pdf" # ONLY SYN
    file_input = "/sfasdf/gfsafds/EDAPDF-001D97D62A432FE6E05400215A9BA3BA-N6523609D3808-empty-empty-P00025-PDS-2014-08-08.pdf" # IN Both SYN and PDS

    #file_input = "/sfasdf/gfsafds/EDAPDF-0C00C8166F006949E05400215A9BA3BA-SP070003D1380-0523-empty-16-PDS-2015-01-06.pdf" # ONLY SYN (modified data)


    # Load Extensions configuration files.
    data_conf_filter = read_extension_conf()

    #file_input = "/sfasdf/gfsafds/EDAPDF-ad290457-4e43-4276-9e6e-1587d41196f5-N0018918DZ067-N0018919FZ062-empty-P00004-PDS-2019-11-20.pdf" # ONLY PDS
    #file_input = "/sfasdf/gfsafds/EDAPDF-00964DCE18980E0EE05400215A9BA3BA-N0060412A3000-empty-empty-P00005-PDS-2014-08-14.pdf" # ONLY SYN
    file_input = "/sfasdf/gfsafds/EDAPDF-001D97D62A432FE6E05400215A9BA3BA-N6523609D3808-empty-empty-P00025-PDS-2014-08-08.pdf" # IN Both SYN and PDS

    #file_input = "/sfasdf/gfsafds/EDAPDF-0C00C8166F006949E05400215A9BA3BA-SP070003D1380-0523-empty-16-PDS-2015-01-06.pdf" # ONLY SYN (modified data)

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


# def lower_json(json_info):
#     if isinstance(json_info, dict):
#         for key in list(json_info.keys()):
#             if isinstance(json_info[key], list):
#                 append = "_eda_ext_n"
#             elif isinstance(json_info[key], dict):
#                 append = "_eda_ext_n"
#             else:
#                 append = "_eda_ext"
#             key_lower = key.lower() + append
#             json_info[key_lower] = json_info[key]
#             del json_info[key]
#             lower_json(json_info[key_lower])
#
#     elif isinstance(json_info, list):
#         for item in json_info:
#             lower_json(item)

if __name__ == '__main__':
    run()


