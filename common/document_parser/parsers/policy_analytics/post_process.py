from datetime import datetime

from common.document_parser.parsers.policy_analytics.display_mappings import (
    DISPLAY_TYPE_LOOKUP,
    CRAWLER_TO_DISPLAY_ORG_LOOKUP,
    CRAWLER_TO_DATA_SOURCE_LOOKUP,
    CRAWLER_TO_SOURCE_TITLE_LOOKUP
)

from common.utils.parsers import parse_timestamp
from gamechangerml.src.utilities.text_utils import utf8_pass, clean_text

DEFAULT_DATE_STRFMT = '%Y-%m-%dT%H:%M:%S'
DEFAULT_DATE_STR = datetime.strftime(datetime.utcnow(), DEFAULT_DATE_STRFMT)

def get_access_timestamp(doc_dict):

    try:
        return datetime.strftime(
            datetime.strptime(
                doc_dict.get("access_timestamp", None),
                '%Y-%m-%d %H:%M:%S.%f'),
            DEFAULT_DATE_STRFMT
        )
    except:
        # TODO: fix date field logic to omit date fields altogether when unknown
        return DEFAULT_DATE_STR


def get_publication_date(doc_dict):
    try:
        parsed_date = parse_timestamp(doc_dict.get("publication_date", None))
        if parsed_date:
            return datetime.strftime(parsed_date, DEFAULT_DATE_STRFMT)
    except:
        # TODO: fix date field logic to omit date fields altogether when unknown
        return DEFAULT_DATE_STR


def get_display_doc_type(doc_dict, meta_data):
    """
    get display type for cards on web app
    :return: string
    """
    if "display_doc_type" in meta_data:
        return meta_data["display_doc_type"]

    if "doc_type" in meta_data:
        doc_type = meta_data["doc_type"].strip().lower()

    else:
        doc_type = str(doc_dict["f_name"]).split(" ")[0].lower()

    return DISPLAY_TYPE_LOOKUP[doc_type]


def get_display_org(meta_data):
    """
    get display org for cards on web app
    :return: string
    """
    if 'display_org' in meta_data:
        return meta_data['display_org']

    crawler_used = meta_data["crawler_used"]
    display_org = CRAWLER_TO_DISPLAY_ORG_LOOKUP[crawler_used]

    return display_org

def get_data_source(meta_data):
    """
    get data source for cards on web app
    :return: string
    """
    if 'data_source' in meta_data:
        return meta_data['data_source']

    crawler_used = meta_data["crawler_used"]
    display_source = CRAWLER_TO_DATA_SOURCE_LOOKUP[crawler_used]

    return display_source

def get_source_title(meta_data):
    """
    get source title for cards on web app
    :return: string
    """
    if 'source_title' in meta_data:
        return meta_data['source_title']

    crawler_used = meta_data["crawler_used"]
    display_source = CRAWLER_TO_SOURCE_TITLE_LOOKUP[crawler_used]

    return display_source

def get_display_source(meta_data):
    """
    get display source for cards on web app
    :return: string
    """
    data_source = get_data_source(meta_data)
    source_title =get_source_title(meta_data)
    return data_source + " - " + source_title

def get_display_title(meta_data):
    """
    get display org for cards on web app
    :return: string
    """
    doc_type = meta_data["doc_type"].strip()
    doc_num = meta_data["doc_num"].strip()
    doc_title = meta_data["doc_title"].strip()
    return doc_type + " " + doc_num + " " + doc_title


def get_file_extension(meta_data):
    """
    get file extension for cards on webapp
    :return: string
    """
    file_ext = meta_data["downloadable_items"][0]["doc_type"]
    return file_ext


def rename_and_format(doc_dict):
    doc_dict["raw_text"] = utf8_pass(doc_dict["text"])
    doc_dict["text"] = clean_text(doc_dict["text"])
    doc_dict["access_timestamp_dt"] = get_access_timestamp(doc_dict)
    doc_dict["publication_date_dt"] = get_publication_date(doc_dict)

    if doc_dict["meta_data"]:
        doc_dict["file_ext_s"] = get_file_extension(doc_dict["meta_data"])
        doc_dict["display_doc_type_s"] = get_display_doc_type(
            doc_dict, doc_dict["meta_data"])
        doc_dict["display_title_s"] = get_display_title(doc_dict["meta_data"])
        doc_dict["display_org_s"] = get_display_org(doc_dict["meta_data"])
        doc_dict["data_source_s"] = get_data_source(doc_dict["meta_data"])
        doc_dict["source_title_s"] = get_source_title(doc_dict["meta_data"])
        doc_dict["display_source_s"] = get_display_source(doc_dict["meta_data"])

    doc_dict["is_revoked_b"] = False

    to_rename = [
        ("txt_length", "text_length_r"),
        ("crawler_used", "crawler_used_s"),
        ("source_fqdn", "source_fqdn_s"),
        ("source_page_url", "source_page_url_s"),
        ("cac_login_required", "cac_login_required_b"),
        ("download_url", "download_url_s"),
        ("version_hash", "version_hash_s")
    ]

    for current, needed in to_rename:
        try:
            doc_dict[needed] = doc_dict[current]
            del doc_dict[current]
        except:
            pass

    if doc_dict["meta_data"]:
        if "extensions" in doc_dict["meta_data"]:
            extensions = doc_dict["meta_data"]["extensions"]
            for key in extensions:
                doc_dict[key] = extensions[key]

    to_delete = [
        "meta_data",
        "access_timestamp",
        "publication_date",
        "crawler_used",
        "source_fqdn",
        "source_page_url",
        "cac_login_required",
        "download_url",
        "version_hash",
        "ingest_date",
        "orgs",
        "f_name"
    ]

    for key in to_delete:
        try:
            del doc_dict[key]
        except:
            pass

    return doc_dict


def process(doc_dict):
    processed_dict = rename_and_format(doc_dict)
    return processed_dict
