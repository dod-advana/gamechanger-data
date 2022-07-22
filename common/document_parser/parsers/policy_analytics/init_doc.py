from pathlib import Path
from datetime import datetime


def assign_f_name_fields(f_name, doc_dict):
    filename = (
        f_name.absolute().name
        if isinstance(f_name, Path)
        else Path(str(f_name)).name
    )
    doc_dict['filename'] = filename
    doc_dict['f_name'] = filename
    doc_dict["id"] = filename + "_0"
    doc_dict["group_s"] = filename + "_0"

    meta_data = doc_dict["meta_data"]

    doc_dict["doc_type"] = meta_data.get("doc_type", str(f_name).split(" ")[0])
    doc_dict["doc_num"] = meta_data.get(
        "doc_num", str(f_name).split(",")[0].split(" ")[-1])


def assign_other_fields(doc_dict):
    doc_dict["type"] = "document"

    doc_dict["init_date"] = "NA"
    doc_dict["change_date"] = "NA"

    doc_dict["entities"] = ["NA_1", "NA_2"]
    doc_dict["author"] = "NA"
    doc_dict["signature"] = "NA"
    doc_dict["subject"] = "NA"
    doc_dict["classification"] = "NA"
    doc_dict["par_count_i"] = 0


def create_doc_dict_with_meta(meta_data={}) -> dict:

    default_date = ""
    default_crawler = "no_crawler_used"
    default_url = ""
    default_cac_login_required = True
    default_hash = ""
    default_doc_type = "" 
    default_org = ""
    default_source = ""
    default_source_title = ""
    default_title = ""
    default_revoked = ""

    doc_dict = {
        "access_timestamp": meta_data.get("access_timestamp", default_date),
        "publication_date": meta_data.get("publication_date", default_date),
        "crawler_used": meta_data.get("crawler_used", default_crawler),
        "source_fqdn": meta_data.get("source_fqdn", default_url),
        "source_page_url": meta_data.get("source_page_url", default_url),
        "cac_login_required": meta_data.get("cac_login_required", default_cac_login_required),
        "download_url": meta_data.get("download_url", default_url),
        "file_ext": meta_data.get("file_ext", default_url),
        "version_hash": meta_data.get("version_hash", default_hash),
        "display_doc_type": meta_data.get("display_doc_type", default_doc_type),
        "display_org": meta_data.get("display_org", default_org),
        "data_source": meta_data.get("data_source", default_source),
        "source_title": meta_data.get("source_title", default_source_title),
        "display_source": meta_data.get("display_source", default_source),
        "display_title": meta_data.get("display_title", default_title),
        "is_revoked": meta_data.get("is_revoked", default_revoked),
        "title": meta_data.get("doc_title", "NA"),
        "ingest_date": meta_data.get("access_timestamp", False),
        "office_primary_resp": meta_data.get("office_primary_resp", None),
        "meta_data": meta_data
    }

    return doc_dict