import os
from common.document_parser.lib import (
    pages,
    paragraphs,
    entities,
    topics,
    ref_list,
    abbreviations,
    summary,
    keywords,
    text_length,
    read_meta,
    pdf_reader,
    write_doc_dict_to_json,
    ocr,
    file_utils,
)
from common.document_parser.lib.section_parse import add_sections
from . import post_process, init_doc
from common.document_parser.lib.ml_features import (
    add_pagerank_r,
    add_popscore_r,
)


def parse(
    f_name,
    meta_data=None,
    ocr_missing_doc=False,
    num_ocr_threads=2,
    force_ocr=False,
    out_dir="./",
):
    print("running policy_analyics.parse on", f_name)
    try:
        meta_dict = read_meta.read_metadata(meta_data)
        doc_dict = init_doc.create_doc_dict_with_meta(meta_dict)

        init_doc.assign_f_name_fields(f_name, doc_dict)
        init_doc.assign_other_fields(doc_dict)
        should_delete = False
        if ocr_missing_doc or force_ocr:
            f_name = ocr.get_ocr_filename(f_name, num_ocr_threads, force_ocr)
        if not str(f_name).endswith(".pdf"):
            f_name = file_utils.coerce_file_to_pdf(f_name)
            should_delete = True
        funcs = [
            ref_list.add_ref_list,
            entities.extract_entities,
            topics.extract_topics,
            keywords.add_keyw_5,
            abbreviations.add_abbreviations_n,
            summary.add_summary,
            add_pagerank_r,
            add_popscore_r,
            text_length.add_word_count,
            add_sections,
        ]

        doc_obj = pdf_reader.get_fitz_doc_obj(f_name)
        pages.handle_pages(doc_obj, doc_dict)
        doc_obj.close()

        paragraphs.add_paragraphs(doc_dict)

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
