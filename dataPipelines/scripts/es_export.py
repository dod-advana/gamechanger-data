import subprocess as sub
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path
import typing as t
import multiprocessing as mp
import sys
import argparse
import os
import shutil
import json
from collections import defaultdict
from datetime import datetime as dt
import hashlib
import tempfile

PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
REPO_PATH: str = os.path.abspath(os.path.join(PACKAGE_PATH, '../../'))



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-prefix", help="s3 location of the pdf and metadata snapshot e.g. s3://....")

    return parser.parse_args()

#- function to copy pdf & json snapshots (gamechanger/{pdf,json}) to new directory on disk
#     - inputs:
#         - pdf snapshot s3 prefix url, e.g. s3://....
#         - json snapshot s3 prefix url
#     - how, use python & aws CLI
#     - so the end result is...
#         - `<some_local_base_dir>/json/<parsed json files here...>`
#         - `<some_local_base_dir>/pdf/<pdf/metadata files here...>`

def copy_snapshots_from_s3(pdf_snapshot_prefix:str, json_snapshot_prefix:str, export_base_dir:str) -> t.Dict[str,str]:
    export_base_dir = Path(export_base_dir)
    export_base_dir.mkdir(exist_ok=True)
    # functions to copy pdf & json snapshots (gamechanger/{pdf,json}) to new directory on disk
    print("*** COPYING PDF AND JSON SNAPSHOTS FROM S3 ***")
    pdf_dir = Path(export_base_dir, "pdf")
    json_dir = Path(export_base_dir, "json")

    pdf_dir.mkdir(exist_ok=True)
    json_dir.mkdir(exist_ok=True)

    sub.run(["aws", "s3", "cp", "--recursive", pdf_snapshot_prefix, str(pdf_dir)], check=True)
    sub.run(["aws", "s3", "cp", "--recursive", json_snapshot_prefix, str(json_dir)], check=True)
    return {
        "pdf_dir": str(pdf_dir),
        "json_dir": str(json_dir)
    }

# - function to stage settings/mappings we intend to use
#     - inputs:
#         - nothing, just resolve relevant paths to these indices from the repo itself
#     - so end result is...
#         - `<some_local_base_dir>/mappings/gamechanger.json`
#         - `<some_local_base_dir>/mappings/entities.json`
#         - `<some_local_base_dir>/mappings/search_history.json`

def export_es_mappings(export_base_dir: str) -> None:

    export_base_dir = Path(export_base_dir)
    export_base_dir.mkdir(exist_ok=True)

    # function to stage settings/mappings we intend to use
    print("*** EXPORTING ES MAPPINGS ***")

    gamechanger_mapping = Path(REPO_PATH, "configuration/elasticsearch-config/prod.json")
    entities_mapping = Path(REPO_PATH, "configuration/elasticsearch-config/prod-entities.json")
    search_history_mapping = Path(REPO_PATH, "configuration/elasticsearch-config/prod-search_history.json")

    local_mapping_dir = Path(export_base_dir, "mappings")
    local_mapping_dir.mkdir(exist_ok=True)

    local_gamechanger_mapping = Path(local_mapping_dir, "gamechanger.json")
    local_entities_mapping = Path(local_mapping_dir, "entities.json")
    local_search_history_mapping = Path(local_mapping_dir, "search_history.json")

    shutil.copy(str(gamechanger_mapping), str(local_gamechanger_mapping))
    shutil.copy(str(entities_mapping), str(local_entities_mapping))
    shutil.copy(str(search_history_mapping), str(local_search_history_mapping))


# - function to pull down and save a json array of doc_name + revocation status
#     - inputs:
#       - some_local_base_dir - common dir for the export outputs
#       - nothing else, just use the default connection helper to reach out to db and hardcoded table name to get the data
#     - so end result is...
#         - `<some_local_base_dir>/misc/revocation_map.json`
#         - with a dictonary structured as `[ { "doc_name": "...", "is_revoked": False }, { "doc_name": "...", "is_revoked": True }, ... ]`
def pull_revocations() -> t.Dict[str,bool]:
    print("*** PULLING REVOCATION FROM DB ***")
    from configuration.utils import get_connection_helper_from_env

    connection_helper = get_connection_helper_from_env()
    db = connection_helper.orch_db_engine
    revocation_map = defaultdict(lambda:False)
    with db.connect() as connection:
        result = connection.execute("SELECT name, is_revoked FROM publications")
        for row in result:
            revocation_map[row["name"]] = row["is_revoked"]
    return revocation_map

# - function to correctly update revocation field in all of parsed json files
#     - inputs:
#         - parsed_json_dir
#         - revocation_map
#     - so end result is...
#         - JSON's in parsed_json_dir are updated (on disk) so their revocation status reflects the one in the map file.
def update_revocations(parsed_json_dir, revocation_map, pdf_dir) -> None:
    print("*** UPDATING JSONS TO INCLUDE REVOCATIONS ***")
    def get_matching_doc_name(parsed_json_path: Path) ->str:
        metadata_path = Path(pdf_dir, parsed_json_path.stem + ".pdf.metadata")
        if not metadata_path.exists():
            return parsed_json_path.stem
        return json.load(metadata_path.open()).get("doc_name",parsed_json_path.stem)

    for p in Path(parsed_json_dir).glob("*.json"):
        jdict = json.load(p.open(mode='r'))
        jdict["is_revoked_b"] = revocation_map[get_matching_doc_name(p)]
        json.dump(jdict, p.open('rw'))


def zip_base_dir(export_base_dir:str, output_dir: str) -> str:
    output_dir = Path(output_dir)
    export_base_dir = Path(export_base_dir)

    output_dir.mkdir(exist_ok=True)

    compressed_filename = "gc_data_export." + dt.now().strftime("%Y%m%d")
    output_path = Path(output_dir, compressed_filename)

    sub.run([
        "tar",
        "-cz",
        "-f", str(output_path),
        "-C", str(export_base_dir),
        "."
    ], check=True)
    return str(output_path.absolute())

def split_archive(output_dir:str, archive_path:str, chunk_size: str = "1G") -> t.List[str] :
    print("***SPLITING ARCHIVE INTO CHUNKS***")
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    archive_path = Path(archive_path)
    part_name = archive_path.name + ".part_"
    sub.run([
        "split",
        "-b", chunk_size,
        "-d",
        str(archive_path),
        os.path.join(str(output_dir), part_name)
    ], check=True)

    return [str(x.absolute()) for x in output_dir.glob(f"{part_name}*")]

def calculate_md5(filepath:str)->str:
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

        return file_hash.hexdigest()

def create_manifest(file_list:t.List[str], manifest_path:str) -> str:
    print("***CREATING MANIFEST OF CHECKSUMS***")
    manifest_path = Path(manifest_path)
    manifest_dict = {}
    for file in file_list:
        manifest_dict[Path(file).name] = calculate_md5(file)

    json.dump(manifest_dict, manifest_path.open('rw'))
    return str(manifest_path.absolute())

def upload_to_s3(file_list:t.List[str], s3_upload_prefix:str) -> None:
    print("***UPLOADING TO S3***")
    s3_upload_prefix = s3_upload_prefix if s3_upload_prefix.endswith("/") else s3_upload_prefix + '/'
    sub.run(["aws", "s3", "cp", *file_list, s3_upload_prefix], check=True)

if __name__=="__main__":

    args = parse_args()

    pdf_snapshot_prefix = args.pdf_s3_prefix
    json_snapshot_prefix = args.json_s3_prefix
    job_tmp_dir = args.job_tmp_dir
    manifest_filename = args.manifest_filename
    s3_upload_prefix = args.s3_upload_prefix

    export_base_dir_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="export_base_dir_")
    export_base_dir = export_base_dir_tmp_dir.name

    final_output_dir_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="final_output_dir_")
    final_output_dir = final_output_dir_tmp_dir.name

    manifest_path = os.path.join(final_output_dir, manifest_filename)

    try:

        snapshot_dict = copy_snapshots_from_s3(
            pdf_snapshot_prefix=pdf_snapshot_prefix,
            json_snapshot_prefix=pdf_snapshot_prefix,
            export_base_dir= export_base_dir
        )
        parsed_json_dir = snapshot_dict["json_dir"]
        pdf_dir = snapshot_dict["pdf_dir"]

        export_es_mappings(
            export_base_dir=export_base_dir
        )

        revocation_map = pull_revocations()
        update_revocations(
            parsed_json_dir=parsed_json_dir,
            revocation_map=revocation_map,
            pdf_dir=pdf_dir
        )

        compressed_path = zip_base_dir(
            output_dir=final_output_dir,
            export_base_dir=export_base_dir
        )

        part_list = split_archive(
            output_dir=final_output_dir,
            archive_path=compressed_path,
            chunk_size="1G"
        )

        manifest_path = create_manifest(
            file_list=part_list,
            manifest_path=manifest_path
        )

        upload_to_s3(
            file_list=part_list + [manifest_path],
            s3_upload_prefix=s3_upload_prefix
        )
    finally:
        export_base_dir_tmp_dir.cleanup()
        final_output_dir_tmp_dir.cleanup()

