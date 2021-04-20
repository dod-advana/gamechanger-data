import fnmatch
import json
import logging
import os

logger = logging.getLogger(__name__)


def gen_json_mult_keys(data_dir, keys=("title", "f_name")):
    """
    Generator to read and extract the a specifice key type from
    a JSON file in the `data_dir`.

    Args:
        data_dir (str): path to the JSON files

        key (str): JSON element to yield common options
            are pages or paragraphs

    Yields:
        child document text (str), filename (str), doc_id (str)

    Raises:
        ValueError if the directory is not valid
        JSONDecodeError if json.load() fails
        IOError, RuntimeError if there is a problem opening or reading a file

    """
    if not os.path.isdir(data_dir):
        raise ValueError("invalid data_dir, got {}".format(data_dir))

    logger.info("processing corpus dir: {}".format(data_dir))

    json_glob = "*.json"

    try:
        file_list = [
            f_name
            for f_name in sorted(os.listdir(data_dir))
            if fnmatch.fnmatch(f_name, json_glob)
        ]
        for f_name in file_list:
            with open(os.path.join(data_dir, f_name)) as fp:
                json_doc = json.load(fp)
                values = [json_doc[key] for key in keys if key in json_doc]
                yield values
            # if key in json_doc:
            #     yield json_doc[key]
            # else:
            #     logger.warning("no {} in {}".format(key, f_name))
    except (IOError, json.JSONDecodeError, RuntimeError) as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise


def gen_json(data_dir, key="pages"):
    """
    Generator to read and extract the a specifice key type from
    a JSON file in the `data_dir`.

    Args:
        data_dir (str): path to the JSON files

        key (str): JSON element to yield common options
            are pages or paragraphs

    Yields:
        child document text (str), filename (str), doc_id (str)

    Raises:
        ValueError if the directory is not valid
        JSONDecodeError if json.load() fails
        IOError, RuntimeError if there is a problem opening or reading a file

    """
    if not os.path.isdir(data_dir):
        raise ValueError("invalid data_dir, got {}".format(data_dir))

    logger.info("processing corpus dir: {}".format(data_dir))

    json_glob = "*.json"

    try:
        file_list = [
            f_name
            for f_name in sorted(os.listdir(data_dir))
            if fnmatch.fnmatch(f_name, json_glob)
        ]
        for f_name in file_list:
            with open(os.path.join(data_dir, f_name)) as fp:
                json_doc = json.load(fp)
            if key in json_doc:
                yield json_doc[key]
            else:
                logger.warning("no {} in {}".format(key, f_name))
    except (IOError, json.JSONDecodeError, RuntimeError) as e:
        logger.exception("{}: {}".format(type(e), str(e)), exc_info=True)
        raise


def child_doc_gen(doc_gen, child_type="page", key="p_raw_text"):
    """
    Generator intended to be used with `gen_json` to iterate over each
    page (or key) in a child document. Usage is as follows:
    NB: The text may contain unicode characters.

    Args:
        doc_gen (Generator): Instantiated generator

        child_type (str): JSON tag for document element

        key (str): JSON tag for what text to retrieve

    Yields:
        text (str), file name (str)
    """
    type_key = "type"
    id_ = "filename"

    for child_items in doc_gen:
        for child_item in child_items:
            if child_item[type_key] == child_type:
                if id_ in child_item:
                    f_name = child_item[id_]
                else:
                    f_name = "NA"
                text = child_item[key]
                yield text, f_name
