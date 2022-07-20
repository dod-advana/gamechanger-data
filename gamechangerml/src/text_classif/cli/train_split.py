# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))


def main(data_file, topn=10000, suffix=""):
    try:
        df = pd.read_csv(data_file)
        df = df.sample(frac=1.0)
        train = df.head(topn)
        train.to_csv(
            os.path.join(here, "train_" + suffix),
            sep=",",
            index=False,
            header=False,
        )
        logger.info("train : {:5,d}".format(len(train)))
    except FileNotFoundError as e:
        logger.fatal("\n{} : {}".format(type(e), str(e)))
        raise e


if __name__ == "__main__":
    from argparse import ArgumentParser

    log_fmt = (
        "[%(asctime)s %(levelname)-8s], [%(filename)s:%(lineno)s - "
        + "%(funcName)s()], %(message)s"
    )
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    desc = "Shuffles and splits a .csv"
    parser = ArgumentParser(
        prog="python train_test_split.py", description=desc
    )

    parser.add_argument(
        "-i",
        "--input-csv",
        dest="data_file",
        required=True,
        help="input .csv file",
    )
    parser.add_argument(
        "-t",
        "--topn",
        dest="topn",
        type=int,
        default=10000,
        help="if > 0, take the topn, else take all",
    )
    parser.add_argument(
        "-s",
        "--suffix",
        dest="suffix",
        default="",
        type=str,
        help="suffix the output files with this string",
    )
    args = parser.parse_args()
    main(args.data_file, topn=args.topn, suffix=args.suffix)
