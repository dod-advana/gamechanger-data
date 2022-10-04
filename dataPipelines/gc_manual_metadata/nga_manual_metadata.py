import pandas as pd
import os
from pathlib import Path
import filetype
import typing as t
import json
from datetime import datetime
from hashlib import sha256
from functools import reduce
import shutil


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
    def __init__(self, metadata_filename="metadata.xlsx", xlsx_data_sheet = "Metadata Template"):
        self.metadata_filename = metadata_filename
        self.xlsx_data_sheet = xlsx_data_sheet
        if ".xls" in self.metadata_filename:
            print(f"An excel file has been passed in for the 'metadata_filename', please verify that the sheet containing"
                  f"the metadata to be parsed is {self.xlsx_data_sheet}. If it is not, set this value when instantiating"
                  f"from the class or by manually overwriting the 'xlsx_data_sheet' attribute")
        self.all_processed_files = []

    def create_metadata_files(self, input_directory, output_directory = None):
        # if output_directory was passed in, create the directory if doesn't currently exist
        if output_directory:
            if not os.path.exists(output_directory):
                print(f"Output directory {output_directory} doesn't exist, creating directory")
                os.makedirs(output_directory,exist_ok=True)
            # copy over the metadata file to the output directory
            shutil.copy(os.path.join(input_directory,self.metadata_filename), os.path.join(output_directory,self.metadata_filename))
        else:
            # if no output directory specified, make new files in the input directory
            output_directory=input_directory


        try:
            if self.metadata_filename.endswith(".csv"):
                metadata_records = pd.read_csv(os.path.join(input_directory,self.metadata_filename), dtype=str,
                                               keep_default_na=False).to_dict(orient="records")
            elif ".xls" in self.metadata_filename:
                metadata_records = pd.read_excel(os.path.join(input_directory,self.metadata_filename),
                                                 sheet_name=self.xlsx_data_sheet,dtype=str,keep_default_na=False,
                                                 engine='openpyxl').to_dict(orient="records")
            else:
                raise f"Unknown file extension on 'metadata_filename': {self.metadata_filename.split('.')[-1]}"
        except Exception as e:
            raise e

        all_input_filepaths = Path(input_directory).glob("**/*")
        all_output_filepaths = Path(output_directory).glob("**/*")
        existing_files = [x for x in all_input_filepaths if x.is_file() and (x.suffix.lower() in (".pdf", ".html", ".txt")
                                                       or (filetype.guess(str(x)) is not None and (
                        filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)).mime == "application/pdf")))]
        existing_metadata_files = [Path(x).stem for x in all_output_filepaths if x.is_file() and filetype.guess(str(x)) is not None and (
                filetype.guess(str(x)).mime == "metadata")]

        for metadata_record in metadata_records:
            # print(metadata_record["file_name"])
            filepath = os.path.join(input_directory,metadata_record["file_name"])
            if Path(filepath).stem not in existing_metadata_files \
                    and metadata_record['mod_type']=="Addition":# \
                    # and Path(filepath) in existing_files:
                # before, part, after = Path(filepath).stem.partition("(")

                doc_title = metadata_record.get('title', "")# if metadata_record.get('title') else (before.split("_")[5] if not after else before)
                display_doc_type = metadata_record.get('doc_type', "")# if metadata_record.get('doc_type') else (doc_title.split(" ", 1)[0])
                doc_num = metadata_record.get('doc_num', "")# if metadata_record.get('doc_num') else (doc_title.split(" ", 1)[1])
                doc_type = metadata_record.get('display_doc_type', "")

                pdi = dict(doc_type=Path(filepath).suffix[1:],
                           web_url="Not Applicable")
                version_hash_fields = {"filename": Path(filepath).name,
                                       "doc_title": doc_title,
                                       "doc_num": doc_num,
                                       "doc_type": doc_type}

                doc = dict(
                    doc_name=Path(filepath).stem,
                    doc_title=doc_title,
                    doc_num=doc_num,
                    doc_type=doc_type,
                    publication_date=metadata_record.get("publication_date","N/A"),
                    access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                    cac_login_required=True,
                    crawler_used="NGA",
                    source_page_url="Not Applicable",
                    version_hash_raw_data=version_hash_fields,
                    downloadable_items=[pdi],
                    display_doc_type=display_doc_type,

                    display_org="NGA",
                    display_source="NGA Publications",
                    source_fqdn="Not Applicable",
                    version_hash=dict_to_sha256_hex_digest(version_hash_fields)
                )

                # copy over the .pdf file to the output directory if the output directory was specified
                if output_directory!=input_directory:
                    orig_copy_filepath = os.path.join(str(output_directory),metadata_record["file_name"])
                    shutil.copy(filepath, orig_copy_filepath)
                    metadata_outfile = orig_copy_filepath + '.metadata'
                else:
                    metadata_outfile = str(filepath) + '.metadata'
                if doc:
                    with open(metadata_outfile, "w") as f:
                        f.write(json.dumps(doc))
                        # fully processed the file, write to all_processed_files
                        self.all_processed_files.append(metadata_outfile)



if __name__=="__main__":
    input_directory = "/Users/austinmishoe/Downloads/nga_files"
    nga_mm = NGAManualMetadata()
    nga_mm.create_metadata_files(input_directory,output_directory="/Users/austinmishoe/Downloads/nga_files2")
    print(nga_mm.all_processed_files)

