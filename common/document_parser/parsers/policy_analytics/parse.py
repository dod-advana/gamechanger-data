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
)
from . import post_process, init_doc
from common.document_parser.lib.ml_features import (
    add_pagerank_r, add_popscore_r, add_orgs_rs, add_kw_doc_score_r, add_txt_length)


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
    funcs = [ref_list.add_ref_list, entities.extract_entities, topics.extract_topics, keywords.add_keyw_5, abbreviations.add_abbreviations_n, summary.add_summary, add_pagerank_r, add_popscore_r, add_orgs_rs,
             add_kw_doc_score_r, add_txt_length, text_length.add_word_count]
    try:
        doc_obj = pdf_reader.get_fitz_doc_obj(f_name)
        pages.handle_pages(doc_obj, doc_dict)
        doc_obj.close()

        paragraphs.handle_paragraphs(doc_dict)

        for func in funcs:
            try:
                func(doc_dict)
            except Exception as e:
                print(e)
                print("Could not run %s on document dict" % func)
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
