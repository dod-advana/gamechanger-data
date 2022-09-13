import pandas as pd
import os
from pathlib import Path
import filetype
import typing as t
import json
from datetime import datetime
from hashlib import sha256
from functools import reduce


def str_to_sha256_hex_digest(_str: str) -> str:
    """Converts string to sha256 hex digest"""
    if not _str and not isinstance(_str, str):
        raise ValueError("Arg should be a non-empty string")

    return sha256(_str.encode("utf-8")).hexdigest()

def dict_to_sha256_hex_digest(_dict: t.Dict[t.Any, t.Any]) -> str:
    """Converts dictionary to sha256 hex digest.
      Sensitive to changes in presence and string value of any k/v pairs.
    """
    if not _dict and not isinstance(_dict, dict):
        raise ValueError("Arg should be a non-empty dictionary")
    # order dict k/v pairs & concat their values as strings
    value_string = reduce(
        lambda t1, t2: "".join(map(str, (t1, t2))),
        sorted(_dict.items(), key=lambda t: str(t[0])),
        "",
    )
    return str_to_sha256_hex_digest(value_string)


class NGAManualMetadata:
    def __init__(self, metadata_filename="metadata.csv"):
        self.metadata_filename = metadata_filename
        self.all_processed_files = []

    def create_metadata_files(self, input_directory):

        try:
            metadata_records = pd.read_csv(os.path.join(input_directory,self.metadata_filename)).to_dict(orient="records")
        except Exception as e:
            raise e

        all_input_filepaths = Path(input_directory).glob("**/*")
        existing_files = [x for x in all_input_filepaths if x.is_file() and (x.suffix.lower() in (".pdf", ".html", ".txt")
                                                       or (filetype.guess(str(x)) is not None and (
                        filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)).mime == "application/pdf")))]
        existing_metadata_files = [Path(x).stem for x in all_input_filepaths if x.is_file() and filetype.guess(str(x)) is not None and (
                filetype.guess(str(x)).mime == "metadata")]




        for metadata_record in metadata_records:
            # print(metadata_record["file_name"])
            filepath = os.path.join(input_directory,metadata_record["file_name"])
            if Path(filepath).stem not in existing_metadata_files and Path(filepath) in existing_files:
                before, part, after = Path(filepath).stem.partition("(")

                doc_title = metadata_record.get('title') if metadata_record.get('title') else (before.split("_")[5] if not after else before)
                doc_type = metadata_record.get('doc_type') if metadata_record.get('doc_type') else (doc_title.split(" ", 1)[0])
                doc_num = metadata_record.get('doc_num') if metadata_record.get('doc_num') else (doc_title.split(" ", 1)[1])

                pdi = dict(doc_type=Path(filepath).suffix[1:],
                           web_url="manual.ingest")
                version_hash_fields = {"filename": Path(filepath).name,
                                       "doc_title": doc_title,
                                       "doc_num": doc_num,
                                       "doc_type": doc_type}

                doc = dict(
                    doc_name=Path(filepath).stem,
                    doc_title=doc_title,
                    doc_num=doc_num,
                    doc_type=doc_type,
                    publication_date="N/A",
                    access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                    cac_login_required=True,
                    crawler_used="NGA",
                    source_page_url="manual.ingest",
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[pdi],
                    display_doc_type="Document",
                    display_org="NGA",
                    display_source="NGA Publications",
                    source_fqdn="manual.ingest",
                    version_hash=dict_to_sha256_hex_digest(version_hash_fields)
                )

                metadata_outfile = str(filepath) + '.metadata'
                # print(metadata_outfile)
                if doc:
                    with open(metadata_outfile, "w") as f:
                        f.write(json.dumps(doc))
                        # fully processed the file, write to all_processed_files
                        self.all_processed_files.append(metadata_outfile)


#
# if __name__=="__main__":
#     input_directory = "/Users/austinmishoe/bah/advana_data/gc_pdfs/"
#     nga_mm = NGAManualMetadata()
#     nga_mm.create_metadata_files(input_directory)
#     print(nga_mm.all_processed_files)

