"""
usage: python top_k_entities.py [-h] -i INPUT_FILE [-o OUTPUT_FILE] -k TOP_K

retrieve the top_k entity mentions

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        json 'mentions'
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        json of top k entities per document
  -k TOP_K, --top-k TOP_K
                        top k entities per document
"""
import json
import logging

logger = logging.getLogger(__name__)

excluded_entities = ("Department of Defense",)


def top_k_entities(mentions_json, output_json=None, top_k=3):
    """
    Extracts the top k entities from the `mentions_json`. Optionally, the
    results can be written to a .json file.

    Args:
        mentions_json (str): input .json mentions file

        output_json (str): Optional. If present, the results will be dumped to
           this file.

        top_k (int): top occurring entities, excluding those in the
            `excluded_entities` list.

    Returns:
        dict
    """
    top_k_out = dict()
    with open(mentions_json) as fp:
        mentions = json.load(fp)
        for key, val in mentions.items():
            mentions = [
                entity for entity, _ in val if entity not in excluded_entities
            ]
            top_k_out[key] = mentions[:top_k]
    if output_json is not None:
        top_k_enc = json.dumps(output_json)
        with open(output_json, "w") as fp:
            fp.write(top_k_enc)
    return top_k_out


if __name__ == "__main__":
    from argparse import ArgumentParser
    import os

    from gamechangerml.src.text_classif.utils.log_init import initialize_logger

    initialize_logger(to_file=False, log_name="none")

    fp_ = os.path.split(__file__)
    fp_ = "python " + fp_[-1]
    parser = ArgumentParser(
        prog=fp_,
        description="retrieve the top_k entity mentions",
    )
    parser.add_argument(
        "-i",
        "--input-file",
        dest="input_file",
        type=str,
        help="json 'mentions'",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        type=str,
        default=None,
        required=False,
        help="json of top k entities per document",
    )
    parser.add_argument(
        "-k",
        "--top-k",
        dest="top_k",
        type=int,
        help="top k entities per document",
        required=True,
    )

    args = parser.parse_args()
    output_dict = top_k_entities(args.input_file, args.output_file, args.top_k)
