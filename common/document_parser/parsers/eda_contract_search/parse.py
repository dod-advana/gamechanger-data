from common.document_parser.lib import (
    pages,
    ref_list,
    page_rank,
    keywords,
    text_length,
    read_meta,
    pdf_reader,
    write_doc_dict_to_json,
)
from . import post_process, init_doc


def parse(f_name, meta_data=None, ocr_missing_doc=False, num_ocr_threads=2, out_dir="./"):
    meta_dict = read_meta.read_metadata(meta_data)
    doc_dict = init_doc.create_doc_dict_with_meta(meta_dict)

    init_doc.assign_f_name_fields(f_name, doc_dict)
    init_doc.assign_other_fields(doc_dict)
    doc_obj = pdf_reader.get_fitz_doc_obj(f_name)
    pages.handle_pages(doc_obj, doc_dict)
    doc_obj.close()

    page_rank.add_pagerank_r(doc_dict)


    text_length.add_txt_length(doc_dict)
    text_length.add_word_count(doc_dict)

    # adds dates but they arent supposed to be in output?
    # doc_dict = dates.process(doc_dict)

    # unnecessary renaming etc that should be fixed prior to this step
    doc_dict = post_process.process(doc_dict)
    if doc_dict.get('keyw_5'):
        del doc_dict['keyw_5']
    if doc_dict.get('publication_date_dt'):
        del doc_dict["publication_date_dt"]
    if doc_dict.get('version_hash'):
        del doc_dict["version_hash"]
    write_doc_dict_to_json.write(out_dir=out_dir, ex_dict=doc_dict)
