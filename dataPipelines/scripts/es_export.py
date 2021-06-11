import subprocess as sub
from pathlib import Path
import typing as t
import argparse
import os
import shutil
import json
from collections import defaultdict
import datetime as dt
import hashlib
import tempfile
import logging

PACKAGE_PATH: str = os.path.dirname(os.path.abspath(__file__))
REPO_PATH: str = os.path.abspath(os.path.join(PACKAGE_PATH, '../../'))


def get_logger() -> logging.Logger:
    logging.basicConfig(format='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%dT%H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


l = get_logger()


def copy_snapshots_from_s3(pdf_snapshot_prefix: str, json_snapshot_prefix: str, export_base_dir: t.Union[str, Path]) -> t.Dict[
    str, str]:
    export_base_dir = Path(export_base_dir)
    export_base_dir.mkdir(exist_ok=True)
    # functions to copy pdf & json snapshots (gamechanger/{pdf,json}) to new directory on disk
    l.info("*** COPYING PDF AND JSON SNAPSHOTS FROM S3 ***")
    pdf_dir = Path(export_base_dir, "pdf").absolute()
    json_dir = Path(export_base_dir, "json").absolute()

    pdf_dir.mkdir(exist_ok=True)
    json_dir.mkdir(exist_ok=True)

    sub.run(["aws", "s3", "cp", "--recursive", pdf_snapshot_prefix, str(pdf_dir)], check=True)
    sub.run(["aws", "s3", "cp", "--recursive", json_snapshot_prefix, str(json_dir)], check=True)
    return {
        "pdf_dir": str(pdf_dir),
        "json_dir": str(json_dir)
    }


def export_es_mappings(export_base_dir: t.Union[str, Path]) -> None:
    """
     function to stage settings/mappings we intend to use
      inputs:
        - nothing, just resolve relevant paths to these indices from the repo itself
      so end result is...
        - `<some_local_base_dir>/mappings/gamechanger.json`
        - `<some_local_base_dir>/mappings/entities.json`
        - `<some_local_base_dir>/mappings/search_history.json`
    """
    export_base_dir = Path(export_base_dir)
    export_base_dir.mkdir(exist_ok=True)

    # function to stage settings/mappings we intend to use
    l.info("*** EXPORTING ES MAPPINGS ***")

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


def pull_revocations() -> t.Dict[str, bool]:
    l.info("*** PULLING REVOCATION FROM DB ***")
    from configuration.utils import get_connection_helper_from_env

    connection_helper = get_connection_helper_from_env()
    db = connection_helper.orch_db_engine
    revocation_map = defaultdict(lambda: False)
    with db.connect() as connection:
        result = connection.execute("SELECT name, is_revoked FROM publications")
        for row in result:
            revocation_map[row["name"]] = row["is_revoked"]
    return revocation_map


def update_revocations(parsed_json_dir: t.Union[str, Path], revocation_map: t.Dict[str, bool], pdf_dir: t.Union[str, Path]) -> None:
    l.info("*** UPDATING JSONS TO INCLUDE REVOCATIONS ***")
    parsed_json_dir = Path(parsed_json_dir).absolute()
    pdf_dir = Path(pdf_dir).absolute()


    def get_matching_doc_name(parsed_json_path: Path) -> str:
        metadata_path = Path(pdf_dir, parsed_json_path.stem + ".pdf.metadata")
        if not metadata_path.exists():
            return parsed_json_path.stem
        return json.load(metadata_path.open()).get("doc_name", parsed_json_path.stem)

    for p in parsed_json_dir.glob("*.json"):
        jdict = json.load(p.open(mode='r'))
        jdict["is_revoked_b"] = revocation_map[get_matching_doc_name(p)]
        json.dump(jdict, p.open("w"))


def zip_base_dir(export_base_dir: t.Union[str, Path], output_dir: t.Union[str, Path]) -> str:
    output_dir = Path(output_dir).absolute()
    export_base_dir = Path(export_base_dir).absolute()

    output_dir.mkdir(exist_ok=True)

    compressed_filename = "gc_data_export.tgz"
    output_path = Path(output_dir, compressed_filename)

    sub.run([
        "tar",
        "-cz",
        "-f", str(output_path),
        "-C", str(export_base_dir),
        "."
    ], check=True)
    return str(output_path)


def split_archive(output_dir: t.Union[str, Path], archive_path: t.Union[str, Path], chunk_size: str = "1G") -> t.List[str]:
    l.info("***SPLITING ARCHIVE INTO CHUNKS***")
    output_dir = Path(output_dir).absolute()
    archive_path = Path(archive_path).absolute()

    output_dir.mkdir(exist_ok=True)

    part_name = archive_path.name + ".part_"
    sub.run([
        "split",
        "-b", chunk_size,
        "-d",
        str(archive_path),
        str(Path(output_dir, part_name))
    ], check=True)

    return [str(x) for x in output_dir.glob(f"{part_name}*")]


def calculate_md5(filepath: t.Union[str, Path]) -> str:
    filepath = Path(filepath).absolute()
    with filepath.open("rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

        return file_hash.hexdigest()


def create_manifest(file_list: t.List[str], manifest_path: t.Union[str, Path]) -> str:
    l.info("***CREATING MANIFEST OF CHECKSUMS***")
    manifest_path = Path(manifest_path).absolute()
    manifest_dict = {}
    for file in file_list:
        manifest_dict[Path(file).name] = calculate_md5(file)

    json.dump(manifest_dict, manifest_path.open('w'))
    return str(manifest_path)


def upload_to_s3(input_dir: t.Union[str, Path], s3_upload_prefix: str) -> None:
    l.info("***UPLOADING TO S3***")
    input_dir = Path(input_dir).absolute()
    s3_upload_prefix = s3_upload_prefix if s3_upload_prefix.endswith("/") else s3_upload_prefix + '/'
    sub.run(["aws", "s3", "cp", "--recursive", str(input_dir), s3_upload_prefix], check=True)


def arg_s3_prefix_url(s: str) -> str:
    if not s.startswith('s3://'):
        raise argparse.ArgumentTypeError("Not a valid S3_URL. Must start with s3://")

    s = s if s.endswith("/") else s + "/"
    return s


def arg_job_tmp_dir(s: str) -> str:
    sp = Path(s).absolute()
    sp.mkdir(exist_ok=True)
    return str(sp)


def arg_chunk_size(s: str) -> str:
    return s.upper()


def parse_args():
    parser = argparse.ArgumentParser(
        description="CLI for exporting PDF/JSON GC data",
        allow_abbrev=False,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--pdf-s3-prefix",
        help="s3 location of the pdf and metadata snapshot e.g. s3://....",
        required=True,
        type=arg_s3_prefix_url
    )
    parser.add_argument(
        "--json-s3-prefix",
        help="s3 location of the json snapshot e.g. s3://....",
        required=True,
        type=arg_s3_prefix_url
    )
    parser.add_argument(
        "--s3-upload-prefix",
        help="s3 location of the desired upload e.g. s3://....",
        required=True,
        type=arg_s3_prefix_url
    )
    parser.add_argument(
        "--job-tmp-dir",
        help="temp job directory",
        required=False,
        default="/tmp",
        type=arg_job_tmp_dir
    )
    parser.add_argument(
        "--manifest-filename",
        help="desired filename of checksum manifest",
        required=False,
        default="checksum_manifest.json"
    )
    parser.add_argument(
        "--chunk-size",
        help="number of parts the zip files will be split into",
        required=False,
        default="1G",
        type=arg_chunk_size
    )

    return parser.parse_args()


if __name__ == "__main__":
    start_ts = dt.datetime.now()

    args = parse_args()

    pdf_snapshot_prefix = args.pdf_s3_prefix
    json_snapshot_prefix = args.json_s3_prefix
    s3_upload_prefix = args.s3_upload_prefix
    job_tmp_dir = args.job_tmp_dir
    manifest_filename = args.manifest_filename
    chunk_size = args.chunk_size

    export_base_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="export_base_dir_")
    export_base_dir = export_base_tmp_dir.name

    partial_output_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="partial_output_dir_")
    partial_output_dir = partial_output_tmp_dir.name

    final_output_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="final_output_dir_")
    final_output_dir = final_output_tmp_dir.name

    manifest_path = os.path.join(final_output_dir, manifest_filename)

    try:
        snapshot_dict = copy_snapshots_from_s3(
            pdf_snapshot_prefix=pdf_snapshot_prefix,
            json_snapshot_prefix=json_snapshot_prefix,
            export_base_dir=export_base_dir
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
            output_dir=partial_output_dir,
            export_base_dir=export_base_dir
        )

        part_list = split_archive(
            output_dir=final_output_dir,
            archive_path=compressed_path,
            chunk_size=chunk_size
        )

        manifest_path = create_manifest(
            file_list=part_list,
            manifest_path=manifest_path
        )

        upload_to_s3(
            input_dir=final_output_dir,
            s3_upload_prefix=s3_upload_prefix
        )

        l.info("EXPORT COMPLETED\n\tElapsed Time: %s", str(dt.datetime.now() - start_ts))
    finally:
        export_base_tmp_dir.cleanup()
        final_output_tmp_dir.cleanup()
        partial_output_tmp_dir.cleanup()
