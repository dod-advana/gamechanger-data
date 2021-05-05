# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging
import os
import numpy as np

import dataScience.src.text_classif.utils.classifier_utils as cu

logger = logging.getLogger(__name__)
here = os.path.dirname(os.path.realpath(__file__))


def main(data_file, topn=0, ident="", split=0.90):
    try:
        df = cu.read_gc_df(data_file)
        if topn > 0:
            df = df.head(topn)
        train, test = np.split(
            df.sample(frac=1), [int(split * len(df))]
        )
        train.to_csv(
            os.path.join(here, "train_" + ident),
            sep=",",
            index=False,
            header=False,
        )
        test.to_csv(
            os.path.join(here, "test_" + ident),
            sep=",",
            index=False,
            header=False,
        )
        logger.info("train : {:5,}".format(len(train)))
        logger.info(" test : {:5,}".format(len(test)))
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
        help="input .csv file"
    )
    parser.add_argument(
        "-t",
        "--topn",
        dest="topn",
        type=int,
        default=0,
        help="if > 0, take the topn, else take all"
    )
    parser.add_argument(
        "-s",
        "--suffix",
        dest="ident",
        default="",
        type=str,
        help="suffix the output files with this string"
    )
    parser.add_argument(
        "--split",
        dest="split",
        type=float,
        default=0.90,
        help="split using this value"
    )
    args = parser.parse_args()
    main(args.data_file, topn=args.topn, ident=args.ident, split=args.split)
