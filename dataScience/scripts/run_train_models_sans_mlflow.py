import argparse
import logging
from datetime import datetime

from dataScience.configs.config import D2VConfig, DefaultConfig
from dataScience.src.search.semantic.models import D2V
from dataScience.src.text_handling.corpus import LocalCorpus, LocalTaggedCorpus
from dataScience.src.text_handling.entity import Phrase_Detector
from dataScience.src.text_handling.process import preprocess
from dataScience.src.utilities import utils
from dataScience.src.search.query_expansion.build_ann_cli import (
    build_qe_model as bqe,
)
from dataScience.src.model_testing import model_assessment_utils as mau
import os

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
"""
Usage:
    to use on CLI:
        # to save with a test flag  {YYYYMMDD-test}
        python -m dataSciece.scripts.run_train_models --nameflag test --save-remote True --corpus PATH_TO_CORPUS

        # no flag
        python -m dataSciece.scripts.run_train_models --save-remote True --corpus PATH_TO_CORPUS

    NOTE: MUST RUN setup_env.sh to save to S3
optional arguments:
    -h, help messages
    -c, --corpus CORPUS DIRECTORY
    -s, --saveremote BOOLEAN SAVE TO S3 (TRUE/FALSE)
    -f, --nameflag STR tag for the model name
    -d, --modeldest MODEL PATH DIR
    -v  , --validate True or False
    -x  , --experimentName name of experiment, if exists will add as a run
"""

modelname = datetime.now().strftime("%Y%m%d")


def run_train(
    model_id,
    save_remote=False,
    corpus_dir=DefaultConfig.DATA_DIR,
    model_dest=DefaultConfig.LOCAL_MODEL_DIR,
    exp_name=modelname,
    validate=False,
):
    corp_dir = corpus_dir
    model_dir = model_dest

    # get model name schema
    model_id = utils.create_model_schema(model_dir, model_id)

    # get corpus
    corpus = LocalCorpus(corp_dir)
    phrase_detector = Phrase_Detector(model_id=model_id)
    phrase_detector.train(corpus)
    phrase_detector.save(model_dir)

    tagged_corpus = LocalTaggedCorpus(corp_dir, phrase_detector)

    # build ANN indices
    bqe.main(corpus_dir, os.path.join(model_dest, model_id), model_id=model_id)

    # start experiment
    model = D2V(model_id=model_id)
    model.train(D2VConfig.MODEL_ARGS, tagged_corpus)
    # this SAVES ALL MODELS in dir
    model.save(model_dest, save_remote)
    logger.info("-------------- Model Training Complete --------------")
    if validate:
        logger.info(
            "-------------- Running Assessment Model Script --------------"
        )
        results = mau.assess_model(
            model_name=model_id,
            logger=logger,
            s3_corpus="corpus_20200909",
            model_dir="dataScience/models/",
            verbose=True,
        )
    else:
        logger.info("-------------- No Assessment Ran --------------")

    logger.info("-------------- Testing Inference --------------")
    logger.info(
        model.infer(
            preprocess(
                "taxes",
                min_len=1,
                phrase_detector=phrase_detector,
                remove_stopwords=True,
            )
        )
    )
    logger.info(
        model.infer(
            preprocess(
                "National Parks",
                min_len=1,
                phrase_detector=phrase_detector,
                remove_stopwords=True,
            )
        )
    )
    logger.info(
        model.infer(
            preprocess(
                "taxes",
                min_len=1,
                phrase_detector=phrase_detector,
                remove_stopwords=True,
            )
        )
    )

    logger.info("-------------- Finished Inference --------------")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Train Models")
    parser.add_argument(
        "--nameflag",
        "-f",
        dest="nameflag",
        type=str,
        help="model name flag i.e. best",
    )
    parser.add_argument(
        "--saveremote", "-s", dest="save", help="save to s3 flag"
    )
    parser.add_argument(
        "--modeldest", "-d", dest="model_dest", help="model destination dir"
    )
    parser.add_argument("--corpus", "-c", dest="corpus", help="corpus dir")
    parser.add_argument(
        "--validate",
        "-v",
        dest="validate",
        help="flag for running validation tests and appending metrics",
    )
    parser.add_argument(
        "--experimentName",
        "-x",
        dest="experimentName",
        default=modelname,
        help="experiement name, keep consistent if you want to compare in mlfow",
    )

    args = parser.parse_args()
    if args.nameflag:
        modelname = f"{modelname}-{args.nameflag}"
    if args.save == "True" or args.save == "true":
        save = True
    else:
        save = False
    if args.validate:
        validate = True
    else:
        validate = False
    model_dest = args.model_dest
    if not model_dest:
        model_dest = DefaultConfig.LOCAL_MODEL_DIR
    run_train(
        model_id=modelname,
        save_remote=save,
        corpus_dir=args.corpus,
        model_dest=model_dest,
        exp_name=args.experimentName,
        validate=validate,
    )
