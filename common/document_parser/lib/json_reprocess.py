import json
from typing import Callable, Union
from common.document_parser.lib.write_doc_dict_to_json import write
from common.document_parser.process import resolve_dynamic_func


def reprocess(f_name: str, process: Union[str, Callable[[dict], dict]], out_dir: str):
    """
    :param f_name: json filename to load
    :param process: function to call on loaded json
    :param out_dir: location to write out new json
    :return: bool : True if new file written successfully
    """
    with open(f_name) as f_in:
        doc_dict = json.load(f_in)

    if process is str:
        process = resolve_dynamic_func(process)

    process(doc_dict)

    return write(out_dir=out_dir, ex_dict=doc_dict)
