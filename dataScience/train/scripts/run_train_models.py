import argparse
import logging
import os
from datetime import datetime

from dataScience.configs.config import D2VConfig, DefaultConfig
from dataScience.src.search.query_expansion.build_ann_cli import (
    build_qe_model as bqe,
)
from dataScience.src.utilities import utils
from dataScience.src.search.sent_transformer.model import SentenceEncoder

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s")
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
    sentenceTrans=False,
    gpu=False,
):
    model_dir = model_dest

    # get model name schema
    model_id = utils.create_model_schema(model_dir, model_id)

    # todo: revise try/catch logic so mlflow_id is not referenced before assignment
    mlflow_id = None

    try:
        import mlflow
        from mlflow.tracking import MlflowClient
    except RuntimeError:
        logger.warning("MLFLOW may not be installed")
    # start experiment
    try:
        # try to create experiment by exp name
        mlflow_id = mlflow.create_experiment(name=exp_name)
    except:
        try:
            # if it exists set id
            mlflow_id = mlflow.get_experiment_by_name(exp_name).experiment_id
        except:
            # if mlflow does not exist
            logger.warning("cannot get experiment from MLFlow")
    # attempt mlflow start
    try:
        with mlflow.start_run(experiment_id=mlflow_id):
            # build ANN indices
            index_dir = os.path.join(model_dest, model_id)
            bqe.main(
                corpus_dir,
                index_dir,
                num_trees=125,
                num_keywords=2,
                ngram=(1, 2),
                word_wt_file="word-freq-corpus-20201101.txt",
                abbrv_file=None,
            )
            for param in D2VConfig.MODEL_ARGS:
                mlflow.log_param(param, D2VConfig.MODEL_ARGS[param])
            mlflow.log_param("model_id", model_id)
            logger.info(
                "-------------- Model Training Complete --------------")
            logger.info(
                "-------------- Building Sentence Embeddings --------------")
            if sentenceTrans:
                encoder = SentenceEncoder(
                    "dataScience/models/transformers/msmarco-distilbert-base-v2",
                    use_gpu=gpu,
                )
                encoder.index_documents(
                    corpus_dir, os.path.join(index_dir, "embeddings")
                )
            if save_remote:
                utils.save_all_s3(model_dest, model_id)

            if validate:
                logger.info(
                    "-------------- Running Assessment Model Script --------------"
                )

                logger.info(
                    "-------------- Assessment is not available--------------")
                """
                results = mau.assess_model(
                    model_name=model_id,
                    logger=logger,
                    s3_corpus="corpus_20200909",
                    model_dir="dataScience/models/",
                    verbose=True,
                )
                for metric in results:
                    if metric != "model_name":
                        mlflow.log_metric(key=metric, value=results[metric])
                """
                logger.info(
                    "-------------- Finished Assessment --------------")
            else:
                logger.info("-------------- No Assessment Ran --------------")

        mlflow.end_run()
    except Exception:
        # try only models without mlflow
        logger.info("-------------- Training without MLFLOW --------------")
        index_dir = os.path.join(model_dest, model_id)
        bqe.main(
            corpus_dir,
            index_dir,
            num_trees=125,
            num_keywords=2,
            ngram=(1, 2),
            word_wt_file="word-freq-corpus-20201101.txt",
            abbrv_file=None,
        )
        if save_remote:
            utils.save_all_s3(model_dest, model_id)
    logger.info("-------------- Model Training Complete --------------")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Train Models")
    parser.add_argument(
        "--nameflag",
        "-f",
        dest="nameflag",
        type=str,
        help="model name flag i.e. best",
    )
    parser.add_argument("--saveremote", "-s", dest="save",
                        help="save to s3 flag")
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
    parser.add_argument(
        "--sentenceTrans",
        "-s",
        dest="sentenceTrans",
        default=False,
        help="True or False Flag for building sentence index",
    )
    parser.add_argument(
        "--gpu",
        "-gpu",
        dest="usegpu",
        default=False,
        help="True or False Flag for using gpu",
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
    if args.sentenceTrans == "True" or args.sentenceTrans == "true":
        sentTrans = True
    else:
        sentTrans = False
    if args.usegpu == "True" or args.usegpu == "true":
        gpu = True
    else:
        gpu = False

    if not model_dest:
        model_dest = DefaultConfig.LOCAL_MODEL_DIR
    run_train(
        model_id=modelname,
        save_remote=save,
        corpus_dir=args.corpus,
        model_dest=model_dest,
        exp_name=args.experimentName,
        validate=validate,
        sentenceTrans=sentTrans,
        gpu=gpu,
    )
