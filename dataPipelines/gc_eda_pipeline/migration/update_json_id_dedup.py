########################################################################################################################
#                                                                                                                      #
#                                   Deprecated Code                                                                    #
#                                                                                                                      #
########################################################################################################################
# import time
# import click
# import json
# import os
# import concurrent.futures
# import traceback
# import subprocess
# from tqdm import tqdm
#
# from typing import Union
# from pathlib import Path
# from urllib3.exceptions import ProtocolError
#
# from dataPipelines.gc_eda_pipeline.conf import Conf
# from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
#
#
# @click.command()
# @click.option(
#     '-s',
#     '--staging-folder',
#     help="A temp folder for which the eda data will be staged for processing.",
#     required=True,
#     type=str,
# )
# @click.option(
#     '--aws-s3-input-json-prefix',
#     help="The S3 prefix for updating the id in the extracted json file",
#     required=True,
#     type=str,
# )
# def run(staging_folder: str, aws_s3_input_json_prefix: str):
#
#     update_id(staging_folder=staging_folder, aws_s3_input_json_prefix=aws_s3_input_json_prefix)
#
#
# def update_id(staging_folder: str, aws_s3_input_json_prefix: str):
#     print("Starting Gamechanger EDA update json ID Pipeline")
#     os.environ["AWS_METADATA_SERVICE_TIMEOUT"] = "20"
#     os.environ["AWS_METADATA_SERVICE_NUM_ATTEMPTS"] = "40"
#
#     start_app = time.time()
#
#     for input_loc in aws_s3_input_json_prefix.split(","):
#         # Get list of files from S3
#
#         file_list = list_of_to_process(staging_folder, input_loc)
#         for json_file in file_list:
#             if Conf.s3_utils.prefix_exists(prefix_path=json_file):
#                 raw_json = json.loads(Conf.s3_utils.object_content(object_path=json_file))
#                 print(raw_json)
#                 exit(1)
#
#
#
# def list_of_to_process(staging_folder: Union[str, Path], aws_s3_input_pdf_prefix: str) -> list:
#     files = []
#     for obj_path in tqdm(Conf.s3_utils.iter_object_paths_at_prefix(prefix=aws_s3_input_pdf_prefix)):
#         path, filename = os.path.split(obj_path)
#         if filename != "":
#             files.append(obj_path)
#             if not os.path.exists(staging_folder + "/json/" + path + "/"):
#                 os.makedirs(staging_folder + "/json/" + path + "/")
#     return files
#
# if __name__ == '__main__':
#     run()
