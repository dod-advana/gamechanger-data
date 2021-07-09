import os
import json
import click
from dataPipelines.gc_eda_pipeline.metadata.metadata_json import metadata_extraction
from datetime import datetime


@click.command()
@click.option(
    '--file-input',
    required=False,
    type=str,
    default=""
)

def run(file_input: str):
    today_date = datetime.today().strftime('%Y/%m/%d')
    test_date = '2021/07/08'
    if today_date == test_date:
        print("Date Match")
    else:
        print("Dates Don't Match")
    # Load Extensions configuration files.
    # data_conf_filter = read_extension_conf()
    #
    # file_input = "/test/EDAPDF-00AF985C0EC44D12E05400215A9BA3BA-H9222210D0016-0015-empty-01-PDS-2014-08-15.pdf"
    #
    # staging_folder = "/Users/vikramhakkal/Development/tmp/gamechanger/eda"
    # aws_s3_output_pdf_prefix = "gamechanger/projects/eda/pdf"
    # is_supplementary_data_successful, is_supplementary_file_missing, metadata_type, data = metadata_extraction(staging_folder, file_input, data_conf_filter, aws_s3_output_pdf_prefix, False)
    #
    # json_object = json.dumps(data, indent=4)
    # print(json_object)



    # audit_rec = {"filename_s": "", "eda_path_s": "", "gc_path_s": "", "json_path_s": "",
    #              "metadata_type_s": "none", "is_metadata_suc_b": False, "is_ocr_b": False, "is_docparser_b": False,
    #              "is_index_b": False,  "metadata_time_f": False, "ocr_time_f": 0.0, "docparser_time_f": 0.0,
    #              "index_time_f": 0.0, "modified_date_dt": 0}
    #
    # test_audit(audit_rec)
    # print(audit_rec)



# def test_audit(audit_rec:dict):
#     audit_rec.update({"filename_s": "hello World", "eda_path_s": "/t4es",
#                       "metadata_type_s": "none", "is_metadata_suc_b": False,
#                       "is_supplementary_file_missing": True,
#                       "metadata_time_f": round(1022.32, 4), "modified_date_dt": int(12323)})
#
# def read_extension_conf() -> dict:
#     ext_app_config_name = os.environ.get("GC_APP_CONFIG_EXT_NAME")
#     with open(ext_app_config_name) as json_file:
#         data = json.load(json_file)
#     return data

if __name__ == '__main__':
    run()


