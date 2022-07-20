import os
import re
import json
import pandas as pd
import math
import numpy as np
from dateutil import parser
from datetime import date, datetime
import signal
import torch
import random
import shutil
from gamechangerml.api.utils.logger import logger
from gamechangerml.configs.config import ValidationConfig

MATAMO_DIR = ValidationConfig.DATA_ARGS['matamo_dir']
SEARCH_HIST = ValidationConfig.DATA_ARGS['search_hist_dir']

MATAMO_TEST_FILE = "gamechangerml/data/test_data/MatamoFeedback_TEST.csv"
SEARCH_TEST_FILE = "gamechangerml/data/test_data/SearchPDFMapping_TEST.csv"


# https://stackoverflow.com/questions/25027122/break-the-function-after-certain-time/25027182
class TimeoutException(Exception):   # Custom exception class
    pass

def init_timer():
    '''Creates a timer using signal'''
    # https://stackoverflow.com/questions/25027122/break-the-function-after-certain-time/25027182
    def timeout_handler(signum, frame):   # Custom signal handler
        raise TimeoutException
    signal.signal(signal.SIGALRM, timeout_handler)
    logger.info("Created timer.")

    return

def check_file_size(filename, path):
    '''Returns the filesize (in bytes) of a file'''
    return os.path.getsize(os.path.join(path, filename))

# from create_embeddings.py
def get_user(logger):
    '''Gets user or sets value to 'unknown' (from create_embeddings.py)'''
    try:
        user = os.environ.get("GC_USER", default="root")
        if (user =="root"):
            user = str(os.getlogin())
    except Exception as e:
        user = "unknown"
        logger.info("Could not get system user")
        logger.info(e)

def save_json(filename, path, data):
    '''Saved a json file'''
    filepath = os.path.join(path, filename)
    with open(filepath, "w") as outfile: 
        return json.dump(data, outfile)

def open_json(filename, path):
    '''Opens a json file'''
    with open(os.path.join(path, filename)) as f:
        return json.load(f)

def open_jsonl(filename, path):
    '''Opens a jsonl file'''
    with open(os.path.join(path, filename), 'r') as json_file:
        json_list = list(json_file)

    data = []
    for json_str in json_list:
        result = json.loads(json_str)
        data.append(result)
    
    return data

def open_txt(filepath):
    '''Opens a txt file'''
    with open(filepath, "r") as fp:
        return fp.readlines()

def get_index_size(sent_index_path):
    '''Checks the size of a sentence index by # of doc ids.'''
    doc_ids = open_txt(os.path.join(sent_index_path, 'doc_ids.txt'))
    return len(doc_ids)

def timestamp_filename(filename, extension):
    '''Makes a filename that include a %Y-%m-%d timestamp'''
    today = date.today()
    formatted = '_'.join([filename, today.strftime("%Y%m%d")])
    return formatted + extension

def check_directory(directory):
    '''Checks if a directory exists, if it does not makes the directory'''
    if not os.path.exists(directory):
        logger.info("Creating new directory {}".format(directory))
        os.makedirs(directory)

    return directory

def make_timestamp_directory(base_dir):

    now = datetime.now()
    new_dir = os.path.join(base_dir, now.strftime("%Y-%m-%d_%H%M%S"))
    if not os.path.exists(new_dir):
        logger.info("Creating new directory {}".format(new_dir))
        os.makedirs(new_dir)
    else:
        logger.info("Directory {} already exists.".format(new_dir))
    
    return new_dir

# stackoverflow
class CustomJSONizer(json.JSONEncoder):
    def default(self, obj):
        return super().encode(bool(obj)) \
            if isinstance(obj, np.bool_) \
            else super().default(obj)

def clean_nans(value):
    '''Replaces null value with 0'''
    if value == None or math.isnan(value):
        return 0
    else:
        return value

## Evaluation utility functions

def get_most_recent_eval(directory):
    '''Gets the most recent eval json from a directory'''
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    evals = [f for f in files if f.split('.')[-1]=='json']
    if evals:
        evals.sort(key=lambda x:int(x.split('_')[-1].split('.')[0].replace('-', '')))
        return evals[-1]
    else:
        return ''

def collect_evals(directory):
    '''Checks if a model directory has any evaluations'''
    sub_dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]
    eval_dirs = [os.path.join(directory, d) for d in sub_dirs if d.split('_')[0]=='evals']
    if not eval_dirs:
        return {}
    else:
        evaldict = {}
        for i in eval_dirs:
            name = i.split('_')[1]
            file = get_most_recent_eval(i)
            if file != '':
                evaldict[name] = open_json(file, i)
            else:
                evaldict[name] = {}
        return evaldict

def collect_sent_evals_gc(index_path):
    '''gets evals for index'''
    eval_dict = {}
    subdict = {}
    evals_path = os.path.join(index_path, 'evals_gc')
    logger.info(f"evals path: {evals_path}")
    for level in ['gold', 'silver']:
        fullpath = os.path.join(evals_path, level)
        file = get_most_recent_eval(fullpath)
        logger.info(f"file: {file}")
        if file != '':
            subdict[level] = open_json(file, fullpath)
        else:
            subdict[level] = ''
    
    eval_dict["gc"] = subdict
    return eval_dict

def handle_sent_evals(index_path):
    try:
        return collect_sent_evals_gc(index_path)
    except Exception as e:
        logger.warning(e)
        return collect_evals(index_path)
        
# from sentence_transformers==2.0.0
#https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/util.py
def cos_sim(a, b):
    """
    Computes the cosine similarity cos_sim(a[i], b[j]) for all i and j.
    :return: Matrix with res[i][j]  = cos_sim(a[i], b[j])
    """
    if not isinstance(a, torch.Tensor):
        a = torch.tensor(a)

    if not isinstance(b, torch.Tensor):
        b = torch.tensor(b)

    if len(a.shape) == 1:
        a = a.unsqueeze(0)

    if len(b.shape) == 1:
        b = b.unsqueeze(0)

    a_norm = torch.nn.functional.normalize(a, p=2, dim=1)
    b_norm = torch.nn.functional.normalize(b, p=2, dim=1)
    return torch.mm(a_norm, b_norm.transpose(0, 1))

def update_dictionary(old_dict, new_additions, prefix):
    '''Update master dictionary of unique queries'''

    def make_ids(new_additions, last_count, prefix):
        '''Make UUIDs for new queries/docs'''
    
        new_dict = {}
        for i in new_additions:
            if i not in old_dict.values():
                last_count += 1
                myid = str(last_count)
                add = str(0) * ( 7 - len(myid))
                myid = prefix + add + myid 
                new_dict[myid] = i

        return new_dict

    if old_dict != {}:
        last_count = [re.sub(r'[A-Z]', '', i) for i in old_dict.keys()][-1]
    else:
        last_count = -1
    new_dict = make_ids(new_additions, last_count, prefix)
        
    return {**old_dict, **new_dict}

def map_ids(iddict, df, mapcol, idcol):
    '''Map IDs back to df'''

    reverse = {iddict[k]: k for k in iddict.keys()}
    col = 'ID_' + idcol
    df[col] = df[mapcol].map(reverse)

    return df

def update_meta_relations(metadata, df, query_col, return_col):
    '''Update dict with relations and metadata about each match'''
    
    df = df.sort_values(by = ['date'], ascending = False).sort_values(by = ['ID_key'])

    for x in df['ID_key'].unique():
        subset = df[df['ID_key']==x].copy()
        for i in subset['ID_value'].unique():
            subsubset = subset[subset['ID_value']==i]
            exact_matches = []
            for k in subsubset.index:
                em = {}
                em['exact_query'] = subsubset.loc[k, query_col]
                em['exact_result'] = subsubset.loc[k, return_col]
                em['source'] = subsubset.loc[k, 'source']
                em['date'] = subsubset.loc[k, 'date']
                exact_matches.append(em)
                
            if x in metadata.keys() and i in metadata[x]:
                metadata[x][i]['exact_matches'].extend(exact_matches)
            else:
                matchdict = {}
                matchdict['correct_match'] = subset['correct_match'].all()
                matchdict['last_match_date'] = list(subset['date'])[0]
                matchdict['exact_matches'] = exact_matches
            
            if x in metadata.keys():
                metadata[x][i] = matchdict
            else:
                searchdict = {}
                searchdict[i] = matchdict
                metadata[x] = searchdict
                
            metadata[x][i]['times_matched'] = len(metadata[x][i]['exact_matches'])
            
    return metadata
    
def filter_rels(metadata, min_correct_matches, max_results):
    '''Filter relations by criteria'''
    
    correct_rels = {}
    incorrect_rels = {}
    logger.info(f"Generating data for {str(len(metadata))} queries with {str(max_results)} max results and {str(min_correct_matches)} min correct matches")
    for key in metadata:
        acceptable_positive_results = []
        negative_results = []
        if max_results and len(metadata[key]) > max_results: # if we have more than n max results, skip this match
            logger.info(f"Skipping {key}: has {str(len(metadata[key]))} unique matches")
            continue
        for match in metadata[key]:
            result = metadata[key][match]
            sources = [i['source'] for i in result['exact_matches']]
            if result['correct_match'] == True:
                if 'matamo' in sources: # we trust matamo data
                    acceptable_positive_results.append(match)
                elif result['times_matched'] >= min_correct_matches: # only pull history matches occurring more than x times
                    acceptable_positive_results.append(match)
                else:
                    logger.info(f"Skipping {key}, {match}: matched {str(result['times_matched'])} times")
            elif result['correct_match'] == False:
                negative_results.append(match)

        if acceptable_positive_results != []:
            correct_rels[key] = acceptable_positive_results
        if negative_results != []:
            incorrect_rels[key] = negative_results

    logger.info(f"Generated {str(len(correct_rels))} correct queries")
    logger.info(f"Generated {str(len(incorrect_rels))} incorrect queries")
        
    return correct_rels, incorrect_rels

def convert_timestamp_to_datetime(timestamp):
    return pd.to_datetime(parser.parse(timestamp).strftime("%Y-%m-%d"))

## filter users and dates when csv read in
def filter_date_range(df, start_date, end_date):
    if 'createdAt' in df.columns:
        timecol = 'createdAt'
    elif 'searchtime' in df.columns:
        timecol = 'searchtime'
    df['dt'] = df[timecol].apply(lambda x: convert_timestamp_to_datetime(x))
    logger.info(f"Available date range: {str(min(df['dt']))} - {str(max(df['dt']))}")
    subset = df.copy()
    if start_date:
        subset = subset[subset['dt'] >= pd.to_datetime(start_date)]
    if end_date:
        subset = subset[subset['dt'] <= pd.to_datetime(end_date)]
    logger.info(f"New date range: {str(min(subset['dt']))} - {str(max(subset['dt']))}")
    return subset

def concat_csvs(directory):
    '''Combines csvs in directory into one df; drops entirely null columns'''
    df = pd.DataFrame()
    logger.info(str(directory))
    csvs = [i for i in os.listdir(directory) if i.split('.')[-1]=='csv']
    csvs = [i for i in csvs if i[:2] != '._']
    logger.info(f"Combining csvs: {str(csvs)}")
    for i in csvs:
        try:
            f = pd.read_csv(os.path.join(directory, i))
            df = pd.concat([df, f])
        except Exception as e:
            logger.warning(e)
            pass
    return df

def concat_matamo(testing_only=False):
    if testing_only:
        return pd.read_csv(MATAMO_TEST_FILE)
    else:
        return concat_csvs(MATAMO_DIR)

def concat_search_hist(testing_only=False):
    if testing_only:
        return pd.read_csv(SEARCH_TEST_FILE)
    else:
        return concat_csvs(SEARCH_HIST)

def get_most_recent_dir(parent_dir):
    
    subdirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    if len(subdirs) > 0:
        return max(subdirs, key=os.path.getctime)
    else:
        logger.error("There are no subdirectories to retrieve most recent data from")
        return None

def make_test_corpus(
    corpus_dir, # main corpus dir
    save_dir, # where to save the test corpus
    percent_random, # float from 0-1 percentage of index to make from random docs
    max_size=1000, # max size of the index (to save on time building)
    include_ids=None, # if any IDs need to be in the test, pass as list
    max_file_size=100000 # max size of random files to add to the test corpus
    ):
    '''Makes a small test corpus for checking validation'''
    all_files = [f.split('.json')[0] + '.json' for f in os.listdir(corpus_dir) if os.path.isfile(os.path.join(corpus_dir, f))]
    if percent_random > 1:
        percent_random = percent_random / 100
    if include_ids:
        logger.info(f"{str(len(include_ids))} ids required in test corpus")
        include_ids = [f.split('.json')[0] + '.json' for f in include_ids] # make sure json at end of filenames
        subset = list(set(all_files).intersection(include_ids)) # only get ids in the main corpus
        if len(subset) < len(include_ids):
            logger.info(f"Did not find all required ids in the main corpus dir.")
            logger.info(f"Found {str(len(subset))} / {str(len(include_ids))} ids")
        other = [i for i in all_files if i not in include_ids]
        if percent_random > 0:
            num_add = round(len(subset)/percent_random - len(subset))
        else:
            num_add = 0
    else:
        subset = []
        other = all_files
        num_add = max_size
    
    ## add random docs
    for i in range(num_add):
        filesize = 1000000
        while filesize > max_file_size: # as we iterate, skip large files
            random_index = random.randint(0,len(other)-1)
            file = other[random_index] # pick a random file
            filesize = check_file_size(file, corpus_dir) # if filesize is smaller than max, break loop
        subset.append(file)
        subset = list(set(subset)) # remove duplicates

    logger.info(f"Collected {str(len(subset))} jsons")
    return subset
