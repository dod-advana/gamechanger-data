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

#    try:
#        if meta_data["downloadable_items"][0]:
#            meta_data["download_url_s"] = meta_data["downloadable_items"][0]['download_url']
#    except:
#        pass

    doc_dict = {
        "access_timestamp_dt": meta_data.get("access_timestamp_dt", default_date),
        "publication_date_dt": meta_data.get("publication_date_dt", default_date),
        "crawler_used_s": meta_data.get("crawler_used_s", default_crawler),
        "source_fqdn_s": meta_data.get("source_fqdn_s", default_url),
        "source_page_url_s": meta_data.get("source_page_url_s", default_url),
        "cac_login_required_b": meta_data.get("cac_login_required_b", default_cac_login_required),
        "download_url_s": meta_data.get("download_url_s", default_url),
        "file_ext_s": meta_data.get("file_ext_s", default_url),
        "version_hash_s": meta_data.get("version_hash_s", default_hash),
        "display_doc_type_s": meta_data.get("display_doc_type_s", default_doc_type),
        "display_org_s": meta_data.get("display_org_s", default_org),
        "data_source_s": meta_data.get("data_source_s", default_source),
        "source_title_s": meta_data.get("source_title_s", default_source_title),
        "display_source_s": meta_data.get("display_source_s", default_source),
        "display_title_s": meta_data.get("display_title_s", default_title),
        "is_revoked_b": meta_data.get("is_revoked_b", default_revoked),
        "title": meta_data.get("doc_title", "NA"),
        "ingest_date": meta_data.get("access_timestamp_dt", False),
        "meta_data": meta_data
    }

    return doc_dict
