import os
from common.document_parser.lib import (
    pages,
    paragraphs,
    entities,
    topics,
    ref_list,
    abbreviations,
    summary,
    page_rank,
    organizations,
    keywords,
    text_length,
    read_meta,
    pdf_reader,
    write_doc_dict_to_json,
    ocr,
    html_utils,
    ml_features,
)
from . import post_process, init_doc


def parse(
    f_name,
    meta_data=None,
    ocr_missing_doc=False,
    num_ocr_threads=2,
    force_ocr=False,
    out_dir="./",
):
    print("running policy_analyics.parse on", f_name)
    meta_dict = read_meta.read_metadata(meta_data)
    doc_dict = init_doc.create_doc_dict_with_meta(meta_dict)

    init_doc.assign_f_name_fields(f_name, doc_dict)
    init_doc.assign_other_fields(doc_dict)
    should_delete = False
    if ocr_missing_doc or force_ocr:
        f_name = ocr.get_ocr_filename(f_name, num_ocr_threads, force_ocr)
    if str(f_name).endswith("html"):
        f_name = html_utils.get_html_filename(f_name)
        should_delete = True
    try:
        doc_obj = pdf_reader.get_fitz_doc_obj(f_name)
        pages.handle_pages(doc_obj, doc_dict)
        doc_obj.close()

        paragraphs.handle_paragraphs(doc_dict)

        ref_list.add_ref_list(doc_dict)

        entities.extract_entities(doc_dict)
        topics.extract_topics(doc_dict)

        keywords.add_keyw_5(doc_dict)

        abbreviations.add_abbreviations_n(doc_dict)

        summary.add_summary(doc_dict)

        page_rank.add_pagerank_r(doc_dict)

        organizations.add_orgs_rs(doc_dict)

        keywords.add_kw_doc_score_r(doc_dict)

        text_length.add_txt_length(doc_dict)

        text_length.add_word_count(doc_dict)

        ml_features.pop_score(doc_dict)

        # TODO: ADD DATES ?
        # doc_dict = dates.process(doc_dict)

        # TODO: post process is mostly unnecessary renaming etc that can be refactored into prior steps
        doc_dict = post_process.process(doc_dict)

        write_doc_dict_to_json.write(out_dir=out_dir, ex_dict=doc_dict)
    except Exception as e:
        print("ERROR in policy_analytics.parse:", e)
    finally:
        if should_delete:
            os.remove(f_name)
