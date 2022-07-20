import random
import pandas as pd
import os
import json
from datetime import date
from typing import List, Union, Dict, Tuple

from gamechangerml.configs.config import (
    TrainingConfig,
    ValidationConfig,
    SimilarityConfig,
)
from gamechangerml.src.search.sent_transformer.model import SentenceSearcher
from gamechangerml.src.model_testing.query_es import *
from gamechangerml.src.utilities.text_utils import normalize_query
from gamechangerml.src.utilities.test_utils import *
from gamechangerml.api.utils.logger import logger
from gamechangerml.api.utils.pathselect import get_model_paths
from gamechangerml.scripts.update_eval_data import make_tiered_eval_data
from gensim.utils import simple_preprocess
from gamechangerml import DATA_PATH, CORPUS_PATH
from gamechangerml.src.utilities import gc_web_api, es_utils

model_path_dict = get_model_paths()
random.seed(42)

LOCAL_TRANSFORMERS_DIR = model_path_dict["transformers"]
SIM_MODEL = SimilarityConfig.BASE_MODEL
training_dir = os.path.join(DATA_PATH, "training", "sent_transformer")
tts_ratio = TrainingConfig.DATA_ARGS["train_test_split_ratio"]
gold_standard_path = os.path.join(
    "gamechangerml/data/user_data",
    ValidationConfig.DATA_ARGS["retriever_gc"]["gold_standard"],
)

corpus_docs = []
try:
    corpus_docs = [
        i.split(".json")[0]
        for i in os.listdir(CORPUS_PATH)
        if os.path.isfile(os.path.join(CORPUS_PATH, i))
    ]
except Exception as e:
    logger.error(e)


scores = {
    "strong_match": 0.95,
    "weak_match": 0.75,
    "neutral": 0.5,
    "negative": -0.95
}

gcClient = gc_web_api.GCWebClient()
esu = es_utils.ESUtils()

def clean_id(id_1: str) -> str:
    """Normalizes doc ids to compare"""
    return id_1.split('.pdf')[0].upper().strip().lstrip()

def get_matching_es_result(query, doc):

    try:
        docid = doc + ".pdf_0"
        search_query = make_query_one_doc(query, docid)
        r = esu.client.search(index=esu.es_index, body=dict(search_query))
        return r
    except Exception as e:
        logger.warning("Failed to get ES results")
        logger.warning(e)

def get_any_es_result(query):

    try:
        search_query = make_query(query)
        r = esu.client.search(index=esu.es_index, body=dict(search_query))
        return r
    except Exception as e:
        logger.warning("Failed to get ES results")
        logger.warning(e)

def get_paragraph_results(resp):
    """Get list of paragraph texts for each search result"""

    texts = []
    if resp["hits"]["total"]["value"] > 0:
        docs = resp["hits"]["hits"]
        for doc in docs:
            doc_id = "_".join(doc["fields"]["id"][0].split("_")[:-1])
            hits = doc["inner_hits"]["paragraphs"]["hits"]["hits"]
            for par in hits:
                par_id = doc_id + "_" + str(par["_nested"]["offset"])
                par_text = par["fields"]["paragraphs.par_raw_text_t"][0]
                processed = ' '.join(simple_preprocess(par_text, min_len=2, max_len=100))
                texts.append({"par_id": par_id, "par_text": processed})

    return texts

def format_matching_paragraphs(query, doc, uid, score):
    """Retrieve & format matching positive/negative paragraphs from ES"""
    found = {}
    not_found = {}
    try:
        matches = get_matching_es_result(query, doc)
        results = get_paragraph_results(matches)
        for r in results:
            offset = r['par_id'].split('_')[-1]
            uid = uid + "_" + offset
            found[uid] = {
                "query": query,
                "doc": r['par_id'],
                "paragraph": r['par_text'],
                "label": score
            }

    except Exception as e:
        logger.error(f"Could not get results for {query} / {doc}")
        logger.error(e)
        not_found[uid] = {"query": query, "doc": doc, "label": score}
    
    return found, not_found

def format_nonmatching_paragraphs(query, matching_docs, single_matching_docs, par_count):
    found = {}
    try:
        non_matches = get_any_es_result(query)
        results = get_paragraph_results(non_matches)
        previous_text = ''
        logger.info(f"Positive num: {par_count}")
        for r in results:
            if len(found) >= (par_count * 4): # stop getting negatives after 1:4 ratio
                logger.info("Exceeded balance, stop retrieving paragraphs")
                break
            else:
                doc_id = r['par_id'].split('.pdf_')[0]
                if doc_id in matching_docs:
                    logger.info("Paragraph comes from a matching doc, skipping")
                else:
                    if doc_id in single_matching_docs:
                        label = scores["weak_match"]
                    else:
                        label = scores["neutral"]
                    if r['par_text'] != previous_text: # skip duplicate paragraphs
                        uid = query + "_|_" + r['par_id']
                        resultdict = {
                            "query": query,
                            "doc": r['par_id'],
                            "paragraph": r['par_text'],
                            "label": label,
                        }
                        found[uid] = resultdict
                        previous_text = r['par_text']
    except Exception as e:
        logger.warning(f"Could not get non-matching results from ES for {query}")
    
    return found

def get_any_matches(any_matches, matching_docs, query):
    """Collect docs that were clicked on at all for this query (so we can adjust their score)"""
    try:
        single_matching_docs = [clean_id(i) for i in any_matches[query] if clean_id(i) not in matching_docs]
        logger.info(f"Found {str(len(single_matching_docs))} other docs opened for this query.")
        return single_matching_docs
    except:
        return []

def collect_paragraphs_es(correct, incorrect, queries, collection, any_matches):
    """Query ES for search/doc matches and negative samples and add them to query results with a label"""

    all_found = {}
    all_not_found = {}
    fullcount = 0
    total = len(correct.keys())
    for i in correct.keys():
        found = {}
        notfound = {}
        logger.info(f"{str(fullcount)} / {str(total)}")
        fullcount += 1
        query = queries[i]
        matching_docs = []
        par_count = 0
        for k in correct[i]: # for each possible match, collect positive samples
            doc = collection[k] # get the docid
            uid = query + "_|_" + doc
            matching_docs.append(doc)
            logger.info(f" *** Querying ES: {query} / {doc} (POS)***")
            p_found, p_not_found = format_matching_paragraphs(query, doc, uid, score=scores['strong_match'])
            found.update(p_found)
            notfound.update(p_not_found)
            par_count += len(p_found)

        # check for negative samples
        if i in list(incorrect.keys()):
            for n in incorrect[i]:
                doc = collection[n] # get the docid
                uid = query + "_|_" + doc
                matching_docs.append(doc)
                logger.info(f" *** Querying ES: {query} / {doc} (NEG)***")
                n_found, n_not_found = format_matching_paragraphs(query, doc, uid, score=scores['negative'])
                found.update(n_found)
                notfound.update(n_not_found)

        if par_count > 0:
            single_matching_docs = get_any_matches(any_matches, matching_docs, query)
            neutral_found = format_nonmatching_paragraphs(query, matching_docs, single_matching_docs, par_count)
            if len(neutral_found) > 0:
                found.update(neutral_found)
                all_found.update(found)
                all_not_found.update(notfound)
            else:
                logger.info(f"\n**** No non-matching results retrieved for {query}")
        else:
            logger.info(f"\n**** No matching results retrieved for {query}")
    
    return all_found, all_not_found


def add_gold_standard(
    intel: Dict[str, str], gold_standard_path: Union[str, os.PathLike]
) -> Dict[str, str]:
    """Adds original gold standard data to the intel training data.
    Args:
        intel [Dict[str,str]: intelligent search evaluation data
        gold_standard_path [Union[str, os.PathLike]]: path to load in the manually curated gold_standard.csv
    Returns:
        intel [Dict[str,str]: intelligent search evaluation data with manual entries added
    """
    gold_original = pd.read_csv(gold_standard_path, names=['query', 'document'])
    logger.info(f"Reading in {gold_original.shape[0]} queries from the Gold Standard data")

    def add_extra_queries(intel: Dict[str,str]) -> Dict[str,str]:
        '''Multiply query/doc pairs to add by using title/filename/id as queries'''
        extra_queries = []
        docs = []
        for doc_id in intel['collection'].values():
            try:
                json = open_json(doc_id + '.json', CORPUS_PATH)
                extra_queries.append(json['display_title_s'])
                docs.append(doc_id)
                logger.info(f"Added extra queries for {doc_id}")
            except:
                logger.warning(f"Could not add extra queries for {doc_id}")
        
        df = pd.DataFrame()
        df['query'] = extra_queries
        df['document'] = docs
        return df
    
    extra_queries_df = add_extra_queries(intel)
    gold = pd.concat([gold_original, extra_queries_df])
    gold.reset_index(inplace = True)
    logger.info(f"Added {extra_queries_df.shape[0]} extra queries to the Gold Standard")
    
    gold['query_clean'] = gold['query'].apply(lambda x: normalize_query(x))
    gold['docs_split'] = gold['document'].apply(lambda x: x.split(';'))
    all_docs = list(set([a for b in gold['docs_split'].tolist() for a in b]))

    def add_key(mydict: Dict[str, str]) -> str:
        """Adds new key to queries/collections dictionaries"""
        last_key = sorted([*mydict.keys()])[-1]
        key_len = len(last_key) - 1
        last_prefix = last_key[0]
        last_num = int(last_key[1:])
        new_num = str(last_num + 1)

        return last_prefix + str(str(0) * (key_len - len(new_num)) + new_num)

    # check if queries already in dict, if not add
    for i in gold["query_clean"]:
        if i in intel["queries"].values():
            logger.info(f"'{i}' already in intel queries")
            continue
        else:
            logger.info(f"adding '{i}' to intel queries")
            new_key = add_key(intel["queries"])
            intel["queries"][new_key] = i

    # check if docs already in dict, if not add
    for i in all_docs:
        if i in intel["collection"].values():
            logger.info(f"'{i}' already in intel collection")
            continue
        else:
            logger.info(f"adding '{i}' to intel collection")
            new_key = add_key(intel["collection"])
            intel["collection"][new_key] = i

    # check if rels already in intel, if not add
    reverse_q = {v: k for k, v in intel["queries"].items()}
    reverse_d = {v: k for k, v in intel["collection"].items()}
    for i in gold.index:
        q = gold.loc[i, "query_clean"]
        docs = gold.loc[i, "docs_split"]
        for j in docs:
            q_id = reverse_q[q]
            d_id = reverse_d[j]
            if q_id in intel["correct"]:  # if query in rels, add new docs
                if d_id in intel["correct"][q_id]:
                    continue
                else:
                    intel["correct"][q_id] += [d_id]
            else:
                intel["correct"][q_id] = [d_id]

    return intel


def train_test_split(data: Dict[str, str], tts_ratio: float) -> Tuple[Dict[str, str]]:
    """Splits a dictionary into train/test set based on split ratio"""

    queries = list(set([data[i]["query"] for i in data]))

    # split the data into positive and negative examples grouped by query
    neg_passing = {}
    pos_passing = {}
    for q in queries:
        subset = {i:data[i] for i in data.keys() if data[i]['query']==q}
        pos_sample = [i for i in subset.keys() if subset[i]['label']==0.95]
        neg_sample = [i for i in subset.keys() if subset[i]['label']==-0.5]
        if len(neg_sample)>0: #since we have so few negative samples, add to neg list if it has a negative ex
            neg_passing[q] = subset
        elif (
            len(pos_sample) > 0
        ):  # only add the other samples if they have a positive matching sample
            pos_passing[q] = subset

    pos_train_size = round(len(pos_passing.keys()) * tts_ratio)
    neg_train_size = round(len(neg_passing.keys()) * tts_ratio)

    pos_train_keys = random.sample(pos_passing.keys(), pos_train_size)
    neg_train_keys = random.sample(neg_passing.keys(), neg_train_size)

    pos_test_keys = [i for i in pos_passing.keys() if i not in pos_train_keys]
    neg_test_keys = [i for i in neg_passing.keys() if i not in neg_train_keys]

    train_keys = []
    test_keys = []
    for x in pos_train_keys:
        train_keys.extend(pos_passing[x])
    for x in pos_test_keys:
        test_keys.extend(pos_passing[x])
    for x in neg_train_keys:
        train_keys.extend(neg_passing[x])
    for x in neg_test_keys:
        test_keys.extend(neg_passing[x])

    train = {i: data[i] for i in train_keys}
    test = {i: data[i] for i in test_keys}

    metadata = {
        "date_created": str(date.today()),
        "n_queries": f"{str(len(pos_train_keys))} train queries / {str(len(pos_test_keys))} test queries",
        "total_train_samples_size": len(train),
        "total_test_samples_size": len(test),
        "split_ratio": tts_ratio
    }

    return train, test, metadata

def get_all_single_matches(validation_dir):
    directory = os.path.join(validation_dir, "any")
    any_matches = {}
    try:
        f = open_json("intelligent_search_data.json", directory)
        intel = json.loads(f)
        for x in intel["correct"].keys():
            query = intel["queries"][x]
            doc_keys = intel["correct"][x]
            docs = [intel["collection"][k] for k in doc_keys]
            any_matches[query] = docs
    except Exception as e:
        logger.warning("Could not load all validation data")
        logger.warning(e)

    return any_matches

def make_training_data_csv(data, label):
    
    df = pd.DataFrame(data).T
    df['match'] = df['label'].apply(lambda x: 1 if x >= 0.95 else 0)
    matches = df[df['match']==1]
    non_matches = df[df['match']==0]
    
    
    def get_docs(mylist):
        try:
            return [i.split('.pdf')[0] for i in mylist]
        except:
            return []

    def count_unique(mylist):
    
        return len(set(get_docs(mylist)))
    
    agg_match = pd.DataFrame(matches.groupby('query')['doc'].apply(list))
    agg_match.rename(columns = {'doc': 'matching_paragraphs'}, inplace = True)
    agg_match['num_matching_paragraphs'] = agg_match['matching_paragraphs'].apply(lambda x: len(x))
    agg_match['num_matching_docs'] = agg_match['matching_paragraphs'].apply(lambda x: count_unique(x))

    agg_nonmatch = pd.DataFrame(non_matches.groupby('query')['doc'].apply(list))
    agg_nonmatch.rename(columns = {'doc': 'nonmatching_paragraphs'}, inplace = True)
    agg_nonmatch['num_nonmatching_paragraphs'] = agg_nonmatch['nonmatching_paragraphs'].apply(lambda x: len(x))
    agg_nonmatch['num_nonmatching_docs'] = agg_nonmatch['nonmatching_paragraphs'].apply(lambda x: count_unique(x))

    combined = agg_match.merge(agg_nonmatch, on='query', how = 'outer')
    combined['label'] = label
        
    def check_overlap(list1, list2):
        return len(set(get_docs(list1)).intersection(get_docs(list2)))
        
    combined['overlap'] = [check_overlap(x, y) for x, y in zip(combined['matching_paragraphs'], combined['nonmatching_paragraphs'])]
    combined['par_balance'] = combined['num_matching_paragraphs'] / combined['num_nonmatching_paragraphs']
    combined['doc_balance'] = combined['num_matching_docs'] / combined['num_nonmatching_docs']

    combined.fillna(0, inplace = True)
    
    return combined
    

def make_training_data(
    index_path: Union[str, os.PathLike],
    level: str, 
    update_eval_data: bool, 
    testing_only: bool=False,
    gold_standard_path: Union[str,os.PathLike]=gold_standard_path,
    tts_ratio: float=tts_ratio,
    training_dir: Union[str,os.PathLike]=training_dir) -> Tuple[Dict[str,str]]:
    """Makes training data based on new user search history data
    Args:
        index_path [str|os.PathLike]: path to the sent index for retrieving the training data (should be most recent index)
        level [str]: level of eval tier to use for training data (options: ['all', 'silver', 'gold'])
        update_eval_data [bool]: whether or not to update the eval data before making training data
        gold_standard_path [Union[str,os.PathLike]]: path to load in the manually curated gold_standard.csv
        tts_ratio [float]: train/test split ratio, float from 0-1
        training_dir [Union[str,os.PathLike]]: directory for saving training data
    Returns:
        [Tuple[Dict[str,str]]]: training data and training metadata dictionaries
    """
    # open json files
    if (
        not os.path.exists(
            os.path.join(DATA_PATH, "validation", "domain", "sent_transformer")
        )
        or update_eval_data
    ):
        logger.info("****    Updating the evaluation data")
        make_tiered_eval_data(index_path, testing_only)

    validation_dir = get_most_recent_dir(
        os.path.join(DATA_PATH, "validation", "domain", "sent_transformer")
    )
    directory = os.path.join(validation_dir, level)
    logger.info(
        f"****    Loading in intelligent search data from {str(directory)}")
    try:
        f = open_json("intelligent_search_data.json", directory)
        intel = json.loads(f)
    except Exception as e:
        logger.warning("Could not load intelligent search data")
        logger.warning(e)
        intel = {}

    # make save_dir
    timestamp = str(validation_dir).split('/')[-1]
    save_dir = os.path.join(training_dir, timestamp)
    os.makedirs(save_dir)
    logger.info(f"Created training data save directory {str(save_dir)}")
    
    ## gather all possible matches
    any_matches = get_all_single_matches(validation_dir)

    # add gold standard samples
    logger.info("****   Adding gold standard examples")
    intel = add_gold_standard(intel, gold_standard_path)

    try:
        found, notfound = collect_paragraphs_es(
            correct=intel['correct'], 
            incorrect=intel['incorrect'], 
            queries=intel['queries'], 
            collection=intel['collection'],
            any_matches=any_matches)
        logger.info(f"---Number of correct query/result pairs that were not found: {str(len(notfound))}")
    except Exception as e:
        logger.warning(e)
        logger.warning("\nCould not retrieve positive matches from ES\n")

    ## train/test split  
    train, test, metadata = train_test_split(found, tts_ratio)
    metadata["sent_index_used"] = index_path
    metadata["validation_data_used"] = validation_dir
    metadata["not_found_search_pairs"] = str(len(notfound))

    data = {"train": train, "test": test}

    logger.info(f"**** Generated training data: \n {metadata}")

    ## Make summary csv of training data
    train_df = make_training_data_csv(train, "train")
    test_df = make_training_data_csv(test, "test")
    fulldf = pd.concat([train_df, test_df])
    csv_path = os.path.join(save_dir, "retrieved_paragraphs.csv")
    fulldf.to_csv(csv_path)

    ## save data and metadata files
    save_json("training_data.json", save_dir, data)
    save_json("training_metadata.json", save_dir, metadata)
    save_json("not_found_search_pairs.json", save_dir, notfound)

    logger.info(f"Finished saving training data files to {save_dir}")

    return
