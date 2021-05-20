import argparse
import logging
import os
from dataScience.src.model_testing.model_assessment_utils import (
    assess_all_models,
)
import dataScience.src.model_testing.version_ as v

if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    logger.info(
        "Semantic model assessment script version {}".format(v.__version__)
    )

    parser = argparse.ArgumentParser(description="Run the assessment script")
    parser.add_argument(
        "--local",
        help="only use models in local directory",
        action="store_true",
    )
    parser.add_argument(
        "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "--gold_standard", help="runs the gold standard test", action="store_true"
    )

    parser.add_argument(
        "--iterate", help="iterate from top 5 - 50 documents returned for each assessment", action="store_true"
    )
    args = parser.parse_args()

    cwd_path = os.getcwd()

    passed = assess_all_models(cwd_path, logger, args.local, args.verbose, args.gold_standard, args.iterate)

    # if not passed:
    #   sys.exit(-1) TODO: uncomment when tests are passing/corpus is fixed
