#!/usr/bin/env python3

import argparse
import hashlib
import json
import logging
import ssl
import typing as t
import urllib.request as urq
from http.client import HTTPResponse
from urllib.error import HTTPError
from pathlib import Path
import tempfile
import subprocess as sub
import datetime as dt
import csv
import time
import base64
import urllib.parse as urp
from multiprocessing.pool import ThreadPool


def get_logger() -> logging.Logger:
    logging.basicConfig(format='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s', datefmt='%Y-%m-%dT%H:%M:%S',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


def get_nonvalidating_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


l = get_logger()
NON_VALIDATING_SSL_CTX = get_nonvalidating_ssl_context()


def flexible_utf8_json_encoder(o: object) -> object:
    """UTF8 JSON Serializer that doesn't break on invalid utf-8 characters"""
    def fix_utf8_string(_s: t.Union[str, bytes]) -> str:
        """Translates utf-8 byte sequence to one without invalid utf-8 characters"""
        _str_bytes = _s if isinstance(_s, bytes) else _s.encode("utf-8")
        return _str_bytes.decode('utf-8', errors='ignore')
    if isinstance(o, (str, bytes)):
        return fix_utf8_string(o)
    else:
        return json.JSONEncoder().default(o)


def calculate_md5(filepath: str) -> str:
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)
        return file_hash.hexdigest()


# validate that md5sums for files in the manifest match, throw exception if there's a problem
def validate_manifest(manifest_path: t.Union[str, Path], file_dir: t.Union[str, Path]) -> None:
    manifest_path = Path(manifest_path).absolute()
    file_dir = Path(file_dir).absolute()

    manifest = json.load(manifest_path.open("r"))

    failures = []
    for p in (Path(file_dir, filename) for filename in manifest.keys()):
        manifest_md5 = manifest[p.name]
        actual_md5 = calculate_md5(str(p))
        if not manifest_md5 == actual_md5:
            failures.append({
                "filename": p.name,
                "manifest_md5": manifest_md5,
                "actual_md5": actual_md5
            })

    if failures:
        for f in failures:
            l.error("Checksum validation failed: %s", f)
        raise Exception("Checksum validation failure.")
    return


# join archive files into one
def join_split_archive(
        manifest_path: t.Union[str, Path],
        file_dir: t.Union[str, Path],
        combined_archive_path: t.Union[str, Path]) -> Path:
    manifest_path = Path(manifest_path).absolute()
    file_dir = Path(file_dir).absolute()
    combined_archive_path = Path(combined_archive_path).absolute()

    manifest = json.load(manifest_path.open("r"))

    with combined_archive_path.open("a") as f:
        for part in sorted([str(Path(file_dir, filename)) for filename in manifest.keys()]):
            sub.run(["cat", part], stdout=f, check=True)


# unzip archive
def unzip_archive(archive_path: t.Union[str, Path], output_dir: t.Union[str, Path]) -> None:
    archive_path = Path(archive_path).absolute()
    output_dir = Path(output_dir).absolute()
    output_dir.mkdir(exist_ok=True)

    sub.run([
        "tar",
        "-xzf", str(archive_path),
        "-C", str(output_dir)
    ], check=True)


class EsConfig:
    def __init__(self,
                 host: str,
                 username: str = None,
                 password: str = None,
                 port: int = None,
                 ssl_on: bool = False):

        if (username and not password) or (not username and password):
            l.error("Username and password must both be set or not at all")
            raise ValueError("Unset username/password")

        self.auth_on = True if (username and password) else False
        self.username = username
        self.password = password
        self.ssl_on = ssl_on
        self.host = host
        self.port = port or (443 if ssl_on else 80)

    @property
    def root_url(self) -> str:
        return (
            f"http{'s' if self.ssl_on else ''}://"
            + self.host
            + f":{self.port}"
        )

    @property
    def auth_header(self) -> t.Dict[str, str]:
        return {
            "Authorization": "Basic " + (
                base64.b64encode(
                        f"{self.username}:{self.password}".encode("utf-8")
                ).decode("utf-8")
            )
        } if self.auth_on else {}


def es_request(
        url: str,
        method: str,
        es_conf: EsConfig,
        data: t.Optional[t.Union[bytes, t.Dict[str, t.Any]]] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        validate_ssl: bool = False) -> HTTPResponse:

    data = (
        data
        if isinstance(data, bytes)
        else json.dumps(data, default=flexible_utf8_json_encoder).encode("utf-8")
    ) if data else None

    headers = headers or {}
    headers["Content-Type"] = "application/json"
    headers.update(es_conf.auth_header)

    method = method.upper()

    request = urq.Request(
        url=urp.urljoin(es_conf.root_url, url),
        method=method,
        data=data,
        headers=headers
    )

    return urq.urlopen(
        url=request,
        context=NON_VALIDATING_SSL_CTX if not validate_ssl else None
    )


def index_exists(index_name: str, es_conf: EsConfig) -> bool:
    try:
        resp = es_request(
            url=f"/{index_name}",
            method='HEAD',
            es_conf=es_conf
        )
        return True
    except HTTPError as e:
        return False


# create index w optional mapping/settings
def create_index(index_name: str, es_conf: EsConfig, mapping_file: t.Optional[t.Union[str, Path]] = None) -> None:
    if mapping_file:
        mapping_file = Path(mapping_file).absolute()
        mapping = json.load(mapping_file.open("r"))
        data = mapping["index"]
    else:
        data = None

    resp = es_request(
        url=f"/{index_name}?pretty",
        method='PUT',
        data=data,
        es_conf=es_conf
    )

    l.info(resp.read().decode())


# remove all indices but the indicated one from alias
def prune_alias(keep_index_name: str, alias_name: str, es_conf: EsConfig) -> None:
    resp = es_request(
        url=f"/{alias_name}/_settings",
        method='GET',
        es_conf=es_conf
    )
    alias_settings = json.loads(resp.read())
    assigned_indices = alias_settings.keys()

    for index_name in filter(lambda i: i != keep_index_name, assigned_indices):
        resp = es_request(
            url=f"/{index_name}/_alias/{alias_name}",
            method='DELETE',
            es_conf=es_conf
        )
        l.info(resp.read().decode())


# sets alias to a given index and no other
def set_alias(index_name: str, alias_name: str, es_conf: EsConfig) -> None:
    resp = es_request(
        url=f"/{index_name}/_alias/{alias_name}",
        method='PUT',
        es_conf=es_conf
    )
    l.info(resp.read().decode())


def generate_doc_id(_s: t.Union[str, bytes]) -> str:
    return hashlib.sha256(_s if isinstance(_s, bytes) else _s.encode("utf-8")).hexdigest()


# insert json doc into given index
def insert_json(
        index_name: str,
        data: t.Dict[str, t.Any],
        es_conf: EsConfig,
        doc_id: t.Optional[str] = None,
        retries: int = 2,
        retry_interval: float = 0.5,
        **kwargs) -> None:
    retries = int(retries)

    url = (
        f"/{index_name}/" +
        f"_doc/{doc_id or ''}"
        # (f"_create/{doc_id}" if doc_id else "_doc")
    )
    method = "POST" if not doc_id else "PUT"

    while True:
        try:
            resp = es_request(
                url=url,
                method=method,
                data=data,
                es_conf=es_conf
            )
            l.info(resp.read().decode())
            break
        except Exception as e:
            l.error("Error while attempting to insert: %s", str(e))
            if retries:
                l.info("Retrying insert ...")
                time.sleep(retry_interval)
                retries -= 1
            else:
                raise(e)


def insert_pub_json(index_name: str, json_path: t.Union[str, Path], es_conf: EsConfig, **insert_json_kwargs) -> None:
    json_path = Path(json_path)

    def prep_json_data(json_path):
        json_data = json.load(json_path.open("r", encoding="utf-8"))

        if "text" in json_data:
            del json_data["text"]
        if "pages" in json_data:
            del json_data["pages"]
        if "raw_text" in json_data:
            del json_data["raw_text"]

        return json_data

    json_data = prep_json_data(json_path)
    doc_id = generate_doc_id(json_path.stem)

    insert_json(
        index_name=index_name,
        data=json_data,
        doc_id=doc_id,
        es_conf=es_conf,
        **insert_json_kwargs
    )




# insert directory of pub jsons into given index
def index_pub_dir(index_name: str, json_dir: t.Union[str, Path], es_conf: EsConfig, max_threads: int = 10) -> None:
    json_dir = Path(json_dir).absolute()

    ThreadPool(max_threads).starmap(
        insert_pub_json,
        ((index_name, json_path, es_conf) for json_path in json_dir.glob("*.json"))
    )


def read_entities_csv(csv_file: t.Union[str, Path]) -> t.List[t.Dict[str, t.Any]]:
    csv_file = Path(csv_file).absolute()

    def clean_string(string):
        return " ".join(
            [i.lstrip("\n").strip().lstrip().replace("'", "")
             for i in string.split(" ")]
        )

    entities = []
    with csv_file.open("r", newline="") as f:
        for row in csv.DictReader(f):
            entities.append({
                "name": clean_string(row.get("entity_name", "")),
                "website": clean_string(row.get("Website", "")),
                "address": clean_string(row.get("Address", "")),
                "government_branch": clean_string(row.get("Government_Branch", "")),
                "parent_agency": clean_string(row.get("Parent_Agency", "")),
                "related_agency": clean_string(row.get("Related_Agency", "")),
                "information": row.get("information", ""),
                "entity_type": row.get("entity_type", ""),
                "crawlers": row.get("crawlers", ""),
                "num_mentions": row.get("num_mentions", ""),
                "aliases": [{"name": x} for x in row.get("Agency_Aliases", "").split(";")]
            })

    return entities


def index_entities_csv(csv_file: t.Union[str, Path], index_name: str, es_conf: EsConfig, max_threads: int = 10) -> None:
    ThreadPool(max_threads).starmap(
        insert_json,
        ((index_name, edata, es_conf) for edata in read_entities_csv(csv_file))
    )


# insert entities csv into index
def insert_entities_csv_into_index(entities_csv_path: t.Union[str, Path], index_name: str, es_conf: EsConfig) -> None:
    entities_csv_path = Path(entities_csv_path).absolute()

    for e in read_entities_csv(entities_csv_path):
        insert_json(
            index_name=index_name,
            data=e,
            es_conf=es_conf
        )


# upload dir to s3
def upload_dir_to_s3(local_dir: t.Union[str, Path], s3_prefix: str) -> None:
    local_dir = Path(local_dir).absolute()

    sub.run([
        "aws",
        "s3",
        "cp",
        "--recursive",
        str(local_dir),
        s3_prefix
    ], check=True)



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


def arg_int_gt_one(s: str) -> int:
    num = abs(int(s))
    if num < 1:
        raise argparse.ArgumentTypeError("Invalid number, must be greater than one.")
    return num


def arg_existing_path(s: str) -> str:
    p = Path(s).absolute()
    if not p.exists():
        raise argparse.ArgumentTypeError("Invalid path - does not exist.")
    return str(p)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GC data import tool",
        allow_abbrev=False,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('--tmp-dir',
                        type=str,
                        required=False,
                        default="/tmp",
                        help="Base temporary directory for the job")

    parser.add_argument('--es-host',
                        type=str,
                        required=True,
                        help="ES host")
    parser.add_argument('--es-port',
                        type=int,
                        required=True,
                        help="ES port")
    parser.add_argument('--es-user',
                        type=str,
                        default=None,
                        required=False,
                        help="ES username")
    parser.add_argument('--es-pass',
                        type=str,
                        default=None,
                        required=False,
                        help="ES password")
    parser.add_argument('--es-ssl',
                        action="store_true",
                        required=False,
                        help="Enable SSL when connecting to ES")

    parser.add_argument('--threads',
                        type=arg_int_gt_one,
                        default=10,
                        required=False,
                        help="Number of threads to use for indexing")
    parser.add_argument('--json-s3-prefix',
                        type=arg_s3_prefix_url,
                        required=True,
                        help="S3 URL prefix to json snapshot location")
    parser.add_argument('--pdf-s3-prefix',
                        type=arg_s3_prefix_url,
                        required=True,
                        help="S3 URL prefix to pdf snapshot location")
    parser.add_argument('--index-suffix',
                        type=str,
                        default=dt.datetime.now().strftime('%Y%m%d'),
                        required=False,
                        help="Suffix to be attached to all created indices")
    parser.add_argument("--skip-alias",
                        action="store_true",
                        required=False,
                        help="Skip setting aliases")
    parser.add_argument('--manifest',
                        type=arg_existing_path,
                        required=True,
                        help="Path to manifest.json of the import bundle")
    parser.add_argument('--bundle-dir',
                        type=arg_existing_path,
                        required=True,
                        help="Path to directory containing files in the manifest.json")
    parser.add_argument('--entities-csv',
                        type=arg_existing_path,
                        required=False,
                        default="",
                        help="Path to entities.csv")
    parser.add_argument('--ignore-mapping-for',
                        dest='unmapped_aliases',
                        action='append',
                        default=[],
                        required=False,
                        help="Ignore mapping file for given alias/index-basename")
    parser.add_argument('--ignore-indexing-for',
                        dest='unindexed_aliases',
                        action='append',
                        default=[],
                        required=False,
                        help="Ignore indexing for given alias/index-basename")
    return parser.parse_args()


if __name__ == '__main__':
    start_ts = dt.datetime.now()

    args = parse_args()

    job_tmp_dir=args.tmp_dir

    es_host=args.es_host
    es_port=args.es_port
    es_username=args.es_user
    es_password=args.es_pass
    es_ssl=args.es_ssl
    max_threads=args.threads

    json_s3_prefix = args.json_s3_prefix
    pdf_s3_prefix = args.pdf_s3_prefix
    index_suffix = args.index_suffix
    manifest_path = args.manifest
    bundle_dir = args.bundle_dir
    entities_csv = args.entities_csv
    skip_alias = args.skip_alias
    unmapped_aliases = args.unmapped_aliases
    unindexed_aliases = args.unindexed_aliases

    es_conf = EsConfig(
        host=es_host,
        username=es_username,
        password=es_password,
        port=es_port,
        ssl_on=es_ssl
    )

    extract_tmp_dir = tempfile.TemporaryDirectory(dir=job_tmp_dir, prefix="extract_tmp_dir_")
    extract_dir_path = Path(extract_tmp_dir.name).absolute()
    json_dir_path = Path(extract_dir_path, 'json')
    pdf_dir_path = Path(extract_dir_path, 'pdf')
    mappings_dir_path = Path(extract_dir_path, 'mappings')

    combined_archive_tmp_file = tempfile.NamedTemporaryFile(
        dir=job_tmp_dir,
        prefix="combined_export_bundle_",
        suffix=".tgz",
        delete=False
    )
    combined_archive_path = Path(combined_archive_tmp_file.name).absolute()

    try:
        l.info(f"Validating manifest ...")
        validate_manifest(
            manifest_path=manifest_path,
            file_dir=bundle_dir
        )

        l.info(f"Joining archive parts ...")
        join_split_archive(
            manifest_path=manifest_path,
            file_dir=bundle_dir,
            combined_archive_path=combined_archive_path
        )

        l.info(f"Unzipping archive ...")
        unzip_archive(
            archive_path=combined_archive_path,
            output_dir=extract_dir_path
        )

        for mappings_and_settings_file in mappings_dir_path.glob("*.json"):
            alias_name = mappings_and_settings_file.stem
            index_name = alias_name + "_" + index_suffix

            if index_exists(index_name, es_conf=es_conf):
                l.info(f"Index '%s' exists, skipping index creation ...", index_name)
                pass
            elif alias_name in unindexed_aliases:
                l.info(f"Skipping index '%s' creation ...", index_name)
                pass
            else:
                l.info(f"Creating index: %s", index_name)
                create_index(
                    index_name=index_name,
                    es_conf=es_conf,
                    **(
                        dict(mapping_file=mappings_and_settings_file)
                        if alias_name not in unmapped_aliases
                        else {}
                    )
                )

            if alias_name == "entities" and alias_name not in unindexed_aliases:
                l.info(f"Indexing entities into %s ...", index_name)
                index_entities_csv(
                    csv_file=entities_csv,
                    index_name=index_name,
                    es_conf=es_conf,
                    max_threads=max_threads
                )

            if alias_name == "gamechanger":
                l.info(f"Indexing publications into %s ...", index_name)
                index_pub_dir(
                    index_name=index_name,
                    json_dir=json_dir_path,
                    es_conf=es_conf,
                    max_threads=max_threads
                )
            if not skip_alias and alias_name not in unindexed_aliases:
                l.info(f"Setting alias %s -> %s ...", alias_name, index_name)
                set_alias(
                    index_name=index_name,
                    alias_name=alias_name,
                    es_conf=es_conf
                )

                l.info(f"Removing all references to alias %s , except %s ...", alias_name, index_name)
                prune_alias(
                    keep_index_name=index_name,
                    alias_name=alias_name,
                    es_conf=es_conf
                )

        l.info(f"Uploading PDF's to S3 ...")
        upload_dir_to_s3(
            local_dir=pdf_dir_path,
            s3_prefix=pdf_s3_prefix
        )

        l.info(f"Uploading JSON's to S3 ...")
        upload_dir_to_s3(
            local_dir=json_dir_path,
            s3_prefix=json_s3_prefix
        )

        l.info("IMPORT COMPLETED\n\tElapsed Time: %s", str(dt.datetime.now() - start_ts))

    finally:
        extract_tmp_dir.cleanup()
        if combined_archive_path.exists():
            combined_archive_path.unlink()
