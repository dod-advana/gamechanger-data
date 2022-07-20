import logging
from collections import defaultdict

import pandas as pd

from gamechangerml.src.text_classif.utils.log_init import initialize_logger

logger = logging.getLogger(__name__)


def count_output(
    df, no_entity_id="Unable to connect Responsibility to Entity"
):
    resp_per_doc = defaultdict(int)
    resp_no_entity = defaultdict(int)
    ref_entities = defaultdict(int)
    for _, row in df.iterrows():
        if row["Organization / Personnel"] != no_entity_id:
            resp_per_doc[row["Source Document"]] += 1
            ref_entities[row["Organization / Personnel"]] += 1
        else:
            resp_no_entity[row["Source Document"]] += 1

    num_docs = len(df["Source Document"].unique())
    num_uniq_entities = len(ref_entities)
    logger.info("           num docs : {:>6,d}".format(num_docs))
    logger.info("num unique entities : {:>6,d}".format(num_uniq_entities))
    return resp_per_doc, resp_no_entity, num_uniq_entities, num_docs


if __name__ == "__main__":
    from argparse import ArgumentParser

    initialize_logger(to_file=False, log_name="none")

    parser = ArgumentParser(prog="python resp_stats.py")
    parser.add_argument(
        "-c",
        "--csv-path",
        dest="csv_path",
        type=str,
        required=True,
        help="final RE to be post-processed",
    )
    args = parser.parse_args()
    final_df = pd.read_csv(args.csv_path)

    # unclear as to what to do with this output
    resp_doc, resp_no_ent, n_uniq_ents, n_docs = count_output(
        final_df, no_entity_id="not available"
    )
