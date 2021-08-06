import string
import random
import time
import os
import hashlib

from dataPipelines.gc_eda_pipeline.utils.eda_utils import read_extension_conf
from dataPipelines.gc_eda_pipeline.indexer.indexer import index_data_file, create_index, get_es_publisher
from dataPipelines.gc_eda_pipeline.audit.audit import audit_record_new

import click

@click.command()
@click.option(
    '-s',
    '--staging-folder',
    help="A temp folder for which the eda data will be staged for processing.",
    required=False,
    type=str,
)
def run(staging_folder: str):
    start_app = time.time()

    data_conf_filter = read_extension_conf()
    publish_audit = create_index(index_name=data_conf_filter['eda']['audit_index'],
                                       alias=data_conf_filter['eda']['audit_index_alias'])
    i = 0
    while i < 1000000:
        project_path = "gamechanger/projects/eda"
        base_path = "eda/piee/unarchive_pdf/pdf_bah_" + str(random.randint(1, 10))
        filename = "EDAPDF" + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)) + "-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) + ".pdf"
        filename_without_ext, file_extension = os.path.splitext(filename)
        audit_rec = {"filename_s": filename,
                     "eda_path_s": base_path + "/" + filename,
                     "gc_path_s": project_path + "/pdf/" + filename,
                     "json_path_s": project_path + "/pdf/" + filename_without_ext + ".json",
                     "metadata_type_s": "none",
                     "is_metadata_suc_b": boolean_random(),
                     "is_ocr_b": boolean_random(),
                     "is_docparser_b": boolean_random(),
                     "is_index_b": boolean_random(),
                     "metadata_time_f": random.uniform(2, 0.001),
                     "ocr_time_f": random.uniform(470, 0.001),
                     "docparser_time_f": random.uniform(4, 0.001),
                     "index_time_f": random.uniform(222, 0.001),
                     "modified_date_dt": int(time.time())
                    }
        audit_id = hashlib.sha256((project_path + "/pdf/" + filename).encode()).hexdigest()
        audit_record_new(audit_id=audit_id, publisher=publish_audit, audit_record=audit_rec)
        i = i + 1
    end_app = time.time()
    print(f'Total APP time -- It took {end_app - start_app} seconds!')

def boolean_random(percent=50):
    prob = random.randrange(0,100)
    if prob > percent:
        return True
    else:
        return False





if __name__ == '__main__':
    run()
