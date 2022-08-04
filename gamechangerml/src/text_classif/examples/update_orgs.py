import pandas as pd

# import numpy as np
from argparse import ArgumentParser
import logging
import time

from gamechangerml.src.text_classif.utils.entity_lookup import (
    update_dod_org_list,
)
from src.text_classif.utils.log_init import initialize_logger
import src.text_classif.utils.classifier_utils as cu

"""Sample command line: python gamechangerml/src/text_classif/examples/update_orgs.py 
                        --dodorg-path gamechangerml/src/text_classif/utils/dod-orgs.txt 
                        --agencies-path gamechangerml/data/agencies/agencies.csv"""

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    desc = "Updating the DoD Orgs reference table based on inputs from the agencies.csv file."
    parser = ArgumentParser(prog="python update_orgs.py", description=desc)
    parser.add_argument(
        "-d",
        "--dodorg-path",
        dest="dodorg_path",
        type=str,
        required=True,
        help="directory of the dod orgs file",
    )
    parser.add_argument(
        "-a",
        "--agencies-path",
        dest="agencies_path",
        type=str,
        required=True,
        help="directory of the agencies file",
    )

    initialize_logger(to_file=False, log_name="none")

    args = parser.parse_args()

    start = time.time()
    updated_file = pd.DataFrame(
        update_dod_org_list(args.agencies_path, args.dodorg_path)
    )
    updated_file.to_csv("updated_dod_orgs.txt", header=False, index=False)
    elapsed = time.time() - start

    logger.info("total time : {:}".format(cu.format_time(elapsed)))
