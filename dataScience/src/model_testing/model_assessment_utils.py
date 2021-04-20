from pathlib import Path
import random
import os
from dataScience.src.utilities.utils import read_corpus_s3
from dataScience.src.utilities.utils import download_models
from dataScience.src.text_handling.process import preprocess
from dataScience.src.search.semantic.models import D2V
from dataScience.src.text_handling.entity import Phrase_Detector
from dataScience.src.text_handling.corpus import LocalTaggedCorpus
import csv
import shutil


def get_docs_d2v(model_name):
    """Returns the corpus that the model was trained on. It returns a list of document names.
    Args:
        model_name: the name of the model to return the corpus of
    """
    doc_names = [n.split("_")[0] for n in model_name.get_corpus_list()]
    doc_names = list(set(doc_names))
    doc_names = [".".join(n.split(".")[:-1]) + ".json" for n in doc_names]
    return doc_names


def assess_model(
    model_name,
    logger,
    s3_corpus="corpus_20201013",
    model_dir=".",
    verbose=False,
):
    """Assesses a model, doing an exact match query to check if the cosine similarity between the query and itself
    in the results is high. We also check what percentage of queries result in the query being the first answer when
    ranked by cosine similarity, and which documents containing the query end up being the first in the ranked
    results.
        Args:
            model_name: the name of the model being assessed
            results_dict: the dictionary in which to add the results of this model
            logger: the logger for the program
            verbose: whether or not we print extra info statements
    """
    model_dir = os.path.join(model_dir, model_name)
    model = D2V(model_name)
    model.load(os.path.join(model_dir, model_name + "_model.d2v"))

    phrase_detector = Phrase_Detector(model_name)
    phrase_detector.load(model_dir)

    # Assess the model based on the corpus
    total = 0
    total_par_first = 0
    total_doc_first = 0
    total_above_70 = 0
    total_above_40 = 0
    total_above_10 = 0
    par_ranks = []
    doc_ranks = []

    # Get model's doctags and vectors
    docs_and_pars = model.get_corpus_list()
    doc_names = []
    # reformat the names to get the document names, not paragraphs names. We can pull entire docs from s3.
    for doc in docs_and_pars:
        doc_name = doc.split("_")[0].split(".pdf")[0] + ".json"
        doc_names.append(doc_name)

    doc_names = list(set(doc_names))

    # only sample 20% docs
    sample = random.sample(doc_names, int(len(doc_names) * 0.1))

    if verbose:
        logger.info("Sampling {0} docs from the corpus".format(len(sample)))

    for doc in sample:
        read_corpus_s3(doc, s3_corpus, "corpus")

    # TODO: remove when the corpus stuff is figured out
    path = os.getcwd()
    if len(list(Path(path).glob("corpus/*.json"))) == 0:
        logger.info("couldn't get any docs from corpus")
        return

    local_corpus = LocalTaggedCorpus("corpus/", phrase_detector)
    para_list = list(local_corpus.__iter__())
    # only sample 50% of paragraphs in corpus
    sample_size = int(len(para_list) * 0.5)
    sample_list = random.sample(para_list, sample_size)

    if verbose:
        logger.info("Sampling {0} paragraphs from the corpus".format(sample_size))

    for item in sample_list:
        p = " ".join(item[0])
        par_id = item[1][0]

        # preprocess to get the relevant words
        search_text = preprocess(
            p, min_len=2, phrase_detector=phrase_detector, remove_stopwords=True
        )

        # infer
        results = model.infer(
            search_text, num_docs=50, max_para=10
        )  # return top 50 docs, up to 10 pars for each
        if not results:
            continue

        # get name of first ranked doc, and see if it's the same doc that we passed in. if so, +1
        doc_id = par_id.split("_")[0]
        par_num = par_id.split("_")[1]
        returned_docs = list(results.keys())
        first_doc = returned_docs[0]

        if first_doc == doc_id:
            total_doc_first += 1

        first_par = first_doc + "_" + str(results[first_doc][0][0])
        if first_par == par_id:
            total_par_first += 1

        # get cosine similarities, check how many are >0.9, 0.4, 0.1.
        if doc_id in returned_docs:
            for par_result in results[doc_id]:
                if par_result[0] == par_num:
                    cossim = par_result[1]

                    if cossim > 0.1:
                        total_above_10 += 1
                    if cossim > 0.4:
                        total_above_40 += 1
                    if cossim > 0.7:
                        total_above_70 += 1

        total += 1
        if (total % 10 == 0) and verbose:
            logger.info(
                "Finished processing {0} out of {1} paragraphs".format(
                    total, sample_size
                )
            )

    if total == 0:
        logger.info("Didn't process any paragraphs.")
        total = 1
    results_dict = {}
    results_dict["model_name"] = model_name
    results_dict["total_above_70"] = total_above_70 / total * 100
    results_dict["total_above_40"] = total_above_40 / total * 100
    results_dict["total_above_10"] = total_above_10 / total * 100
    results_dict["total_par_first"] = total_par_first / total * 100
    results_dict["total_doc_first"] = total_doc_first / total * 100

    return results_dict


def print_results(results_list, logger):
    """
    Prints the results of all the models assessed. It goes through the results dictionary and prints the scores
    for each model.
        Args:
            results_dict: the results dictionary containing the models and their scores
            logger: the logger for the program
    """
    total_passed = 0
    for model in results_list:
        logger.info(
            "(DOCUMENT) Percentage of queries with the document as the first result: "
            + str(model["total_doc_first"])
        )
        logger.info(
            "(PARAGRAPH) Percentage of queries with the paragraph as the first result: "
            + str(model["total_par_first"])
        )
        logger.info("Total cos_sim above 0.70: " + str(model["total_above_70"]))
        logger.info("Total cos_sim above 0.4: " + str(model["total_above_40"]))
        logger.info("Total cos_sim above 0.1: " + str(model["total_above_10"]))

        if model["total_above_70"] > 70:
            logger.info("PASSED TEST: " + model["model_name"])
            total_passed += 1
        else:
            logger.info("FAILED TEST: " + model["model_name"])

    if total_passed != len(results_list):
        logger.info(
            str(total_passed) + " / " + str(len(results_list)) + " tests passed"
        )

    return total_passed == len(results_list)


def assess_model_gs(model_name, logger, model_dir=".", verbose=False, top_n=50):
    """Assesses a model against a gold standard dataset of queries and expected top match. We pass in a
    query text then check if the expected document is the to match.
        Args:
            model_name: the name of the model being assessed
            logger: the logger for the program
            model_dir: the directory where all the models are
            verbose: whether or not we print extra info statements
            top_n: the number of documents to return in inference
    """
    model_dir = os.path.join(model_dir, model_name)
    model = D2V(model_name)
    model.load(os.path.join(model_dir, model_name + "_model.d2v"))

    phrase_detector = Phrase_Detector(model_name)
    phrase_detector.load(model_dir)
    logger.info(
        "Testing model "
        + str(model_name)
        + ", returning top "
        + str(top_n)
        + " documents."
    )

    overall_found = 0
    overall_total = 0

    # Read the gold standard csv into a dictionary.
    with open("gold_standard.csv", mode="r", encoding="utf-8-sig") as infile:
        reader = csv.reader(infile)
        gs_dict = {rows[0]: rows[1].split(";") for rows in reader}

    for i, p in enumerate(list(gs_dict.keys())):
        # preprocess to get the relevant words
        search_text = preprocess(
            p, min_len=1, phrase_detector=phrase_detector, remove_stopwords=True
        )

        # infer
        results = model.infer(
            search_text, num_docs=top_n, max_para=10
        )  # return top 50 docs, up to 10 pars for each
        if not results:
            continue

        expect_list = gs_dict[p]
        total = len(expect_list)
        overall_total += len(expect_list)
        found = 0

        for expected in expect_list:
            if (expected + ".pdf") in list(results.keys()):
                found += 1
                overall_found += 1

        if verbose:
            logger.info(
                "Finished processing "
                + str(i)
                + " / "
                + str(len(list(gs_dict.keys())))
                + " queries."
            )

        logger.info(
            "Model found " + str(found) + " / " + str(total) + " expected results."
        )

    logger.info(
        "Model found "
        + str(overall_found)
        + " / "
        + str(overall_total)
        + " overall expected results."
    )
    return overall_found > overall_total * 0.5


def remove_files(corpus_dir, model_list, logger, verbose=False):
    """
    Removes all model and json files from the current working directory. The purpose is to clean up the directory.
        Args:
            corpus_dir: the corpus directory
            model_list: list of models
            logger: the logger for the program
            verbose: whether or not we print the extra info statements
    """
    if verbose:
        logger.info("removing test files")

    if os.path.exists(corpus_dir):
        shutil.rmtree(corpus_dir)

    for model_dir in model_list:
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)

    if verbose:
        logger.info("finished removing test files")


def assess_all_models(
    model_path, logger, local=False, verbose=False, gold_standard=False, iterate=False
):
    """
    A wrapper util function that either downloads the latest models or selects models from the current working
    directory and runs them through the assessment. It returns a boolean that states whether ot not all models have
    passed.
        Args:
            model_path: path with all the model folders
            logger: the logger for the program
            local: whether we are using local models in the cwd or downloading models from s3
            verbose: whether or not we print the extra info statements
            gold_standard: whether or not we run the gold standard test
            iterate: whether or not we iterate from top 5 to top 50 docs returned (recall @k)
    """
    # only download files if you're not testing local files
    if not local:
        model_list = download_models("models/v3/", model_path)
        if verbose:
            logger.info("using local model files")
    else:
        model_list = [
            name
            for name in os.listdir(model_path)
            if os.path.isdir(os.path.join(model_path, name))
        ]

    if "corpus" in model_list:
        model_list.remove("corpus")
    if "__pycache__" in model_list:
        model_list.remove("__pycache__")

    results_list = []

    for model_name in model_list:
        if gold_standard:
            if iterate:
                number_passed = 0
                for iterations in [1] + [i * 5 for i in range(1, 11)]:
                    if assess_model_gs(
                        model_name=model_name,
                        model_dir=model_path,
                        logger=logger,
                        verbose=verbose,
                        top_n=iterations,
                    ):
                        number_passed += 1

                passed = number_passed >= 5

            else:
                passed = assess_model_gs(
                    model_name=model_name,
                    model_dir=model_path,
                    logger=logger,
                    verbose=verbose,
                )
        else:
            results_list.append(
                assess_model(
                    model_name=model_name,
                    model_dir=model_path,
                    logger=logger,
                    verbose=verbose,
                )
            )

            passed = print_results(results_list, logger)

    remove_files("corpus", model_list, logger, verbose)

    return passed
