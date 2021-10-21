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

def create_metadata_from_manifest(manifest_dict: dict, output_dir: t.Union[Path,str])->None:
    for key in manifest_dict.get("Filename"):
        filename = Path(manifest_dict.get("Filename")[key])
        metadata_path = Path(output_dir, filename.name + ".metadata").resolve()

        pdi = dict(doc_type=filename.suffix[1:], web_url="manifest.ingest")
        version_hash_fields = {"filename": filename.name,
                               "publication_date": manifest_dict.get("Publication Date")[key]}
        doc = dict(
            doc_name=manifest_dict.get("Document Name")[key],
            doc_title=manifest_dict.get("Document Title")[key],
            doc_num=manifest_dict.get("Document Number Denotation", "")[key],
            doc_type=manifest_dict.get("Document Type Denotation", "")[key],
            publication_date= manifest_dict.get("Publication Date")[key],
            access_timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            cac_login_required= not manifest_dict.get("Unclassified Internet okay?")[key],
            crawler_used=manifest_dict.get("Source Name")[key],
            source_page_url="manifest.ingest",
            version_hash_raw_data=version_hash_fields,
            downloadable_items=[pdi],
            source_fqdn="manual.ingest",
            version_hash=dict_to_sha256_hex_digest(version_hash_fields)
        )
        with open(metadata_path, "w") as f:
            f.write(json.dumps(doc))