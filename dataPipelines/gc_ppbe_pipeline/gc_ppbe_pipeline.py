import click
from pathlib import Path
from typing import Union
import os
import json

from dataPipelines.gc_ppbe_pipeline.utils.conf import Conf
from dataPipelines.gc_ppbe_pipeline.utils.ppbe_job_type import PPBEJobType
from dataPipelines.gc_ppbe_pipeline.process_file_type.transform_process import transform
from dataPipelines.gc_ppbe_pipeline.database.database import insert_data_db

@click.command()
@click.option(
    '-t',
    '--staging-folder',
    help='A temp folder for which the JBook data will be staged for processing.',
    type=click.Path(resolve_path=True, exists=True, dir_okay=True, file_okay=False),
    required=True
)
@click.option(
    '-s',
    '--s3-source-prefix',
    required=True,
    type=str
)
@click.option(
    '--ppbe-job-type',
    help="Which data set is going to be process",
    type=click.Choice(e.value for e in PPBEJobType),
    required=True,
)
def run(staging_folder: Union[Path, str], s3_source_prefix: str, ppbe_job_type: str):
    job_type = PPBEJobType(ppbe_job_type)
    staging_folder_path = Path(staging_folder).resolve()
    download_json_files(staging_folder_path, s3_source_prefix, job_type)


def download_json_files(staging_folder: Union[Path, str], s3_source_prefix: str, job_type: PPBEJobType):
    output_dir = str(staging_folder.resolve()) + "/ppbe/" + job_type.value + "/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if Conf.s3_utils.prefix_exists(prefix_path=s3_source_prefix):
        Conf.s3_utils.download_dir(local_dir=output_dir, prefix_path=s3_source_prefix)

        p = Path(output_dir).glob("**/*.json")
        files = [x for x in p if x.is_file()]
        for file_with_path in files:
            if job_type == PPBEJobType.RDTE or job_type == PPBEJobType.PROCUREMENT:
                process_file(file_with_path, )
            else:
                print(f"Job Type {job_type.value} is not supported")

    else:
        print("*** prefix does not exist")


def process_file(file_with_path: Union[Path, str], job_type: PPBEJobType):
    p = Path(file_with_path)
    so_far_processed = 0
    db_data = []
    if p.is_file():
        file_path = p.resolve()
        with open(file_path) as file:
            while True:
                line = file.readline()
                try:
                    data = json.loads(line)
                    transformed_data = transform(data)
                    db_data.append(transformed_data)
                    if len(db_data) > 10000:
                        so_far_processed += len(db_data)
                        print(f"So Far Processed : {so_far_processed}")
                        insert_data_db(db_data, job_type)
                        db_data.clear()
                except ValueError as ve:
                    print(ve)
                if not line:
                    break
            so_far_processed = so_far_processed + len(db_data)
            print(f"Processed : {so_far_processed}")
            insert_data_db(db_data, job_type)


if __name__ == '__main__':
    run()
