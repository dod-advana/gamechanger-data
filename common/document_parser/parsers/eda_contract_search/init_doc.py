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

    # doc_dict["init_date"] = "NA"
    # doc_dict["change_date"] = "NA"

    # doc_dict["entities"] = ["NA_1", "NA_2"]
    # doc_dict["author"] = "NA"
    # doc_dict["signature"] = "NA"
    # doc_dict["subject"] = "NA"
    # doc_dict["classification"] = "NA"
    doc_dict["par_count_i"] = 0


def create_doc_dict_with_meta(meta_data={}) -> dict:

    default_date = ""
    # default_crawler = "no_crawler_used"
    # default_url = ""
    # default_cac_login_required = True
    default_hash = ""

    # try:
    #     if meta_data["downloadable_items"][0]:
    #         meta_data["download_url"] = meta_data["downloadable_items"][0]['web_url']
    # except:
    #     pass

    doc_dict = {
        "access_timestamp": meta_data.get("access_timestamp", default_date),
        "publication_date": meta_data.get("publication_date", default_date),
        # "crawler_used": meta_data.get("crawler_used", default_crawler),
        # "source_fqdn": meta_data.get("source_fqdn", default_url),
        # "source_page_url": meta_data.get("source_page_url", default_url),
        # "cac_login_required": meta_data.get("cac_login_required", default_cac_login_required),
        # "download_url": meta_data.get("download_url", default_url),
        "version_hash": meta_data.get("version_hash", default_hash),

        # "title": meta_data.get("doc_title", "NA"),
        # "ingest_date": meta_data.get("access_timestamp", False),
        "meta_data": meta_data
    }

    return doc_dict
