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

class ManualMetadata:

    def __init__(self, input_directory, document_group):
        self.input_directory = input_directory
        self.document_group = document_group
        p = Path(self.input_directory).glob("**/*")
        self.files = [x for x in p if x.is_file() and (str(x).endswith("pdf") or str(x).endswith("html")
                                                       or (filetype.guess(str(x)) is not None and (
                                                           filetype.guess(str(x)).mime == "pdf" or filetype.guess(str(x)).mime == "application/pdf")))]
        self.metadata_files = [Path(x).stem for x in p if x.is_file() and filetype.guess(str(x)) is not None and (
            filetype.guess(str(x)).mime == "metadata")]

    def create_document(self, file) -> t.Optional[t.Dict[str, t.Any]]:
        doc = None
        if self.document_group == "Memo":
            pdi = dict(doc_type="pdf", web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type="Memo",
                publication_date="N/A",
                access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                cac_login_required=True,
                crawler_used="Memo",
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi],
                source_fqdn="manual.ingest",
                version_hash= dict_to_sha256_hex_digest(version_hash_fields)
            )
        elif self.document_group == "pdf":
            pdi = dict(doc_type="pdf", web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type="pdf",
                publication_date="N/A",
                access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                cac_login_required=True,
                crawler_used="pdf",
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi],
                source_fqdn="manual.ingest",
                version_hash=dict_to_sha256_hex_digest(version_hash_fields)
            )
        elif self.document_group == "nga":
            before, part, after = Path(file).stem.partition("(")

            doc_title = before.split("_")[5] if not after else before
            doc_type = doc_title.split(" ", 1)[0]
            doc_num = doc_title.split(" ", 1)[1]

            pdi = dict(doc_type=Path(file).suffix[1:],
                       web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name,
                                   "doc_title": doc_title,
                                   "doc_num": doc_num,
                                   "doc_type": doc_type}

            doc = dict(
                doc_name=Path(file).stem,
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

        else:
            pdi = dict(doc_type=Path(file).suffix[1:],
                       web_url="manual.ingest")
            version_hash_fields = {"filename": Path(file).name}
            doc = dict(
                doc_name=Path(file).stem,
                doc_title=Path(file).stem,
                doc_num="",
                doc_type=str.upper(self.document_group),
                publication_date="N/A",
                access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
                cac_login_required=True,
                crawler_used=str.upper(self.document_group),
                source_page_url="manual.ingest",
                version_hash_raw_data=version_hash_fields,
                downloadable_items=[pdi],
                display_doc_type="Document",
                display_org=str.upper(self.document_group),
                display_source=str.upper(self.document_group) + " Publications",
                source_fqdn="manual.ingest",
                version_hash=dict_to_sha256_hex_digest(version_hash_fields)
            )

        return doc

    def create_metadata(self):
        if self.document_group:
            for file in self.files:
                print(self.metadata_files)
                if Path(file).stem not in self.metadata_files:
                    doc = self.create_document(file)

                    outname = str(file) + '.metadata'
                    print(outname)
                    if doc:
                        with open(outname, "w") as f:
                            f.write(json.dumps(doc))
