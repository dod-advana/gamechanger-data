from tkinter import NONE
from path import Path
import requests
import logging
import os
import json
import time
import shutil
import pandas as pd
import argparse

logger = logging.getLogger()
training_dir= "gamechangerml/data/test"
http = requests.Session()

GC_ML_HOST = os.environ.get("GC_ML_HOST", default="localhost")
API_URL = f"{GC_ML_HOST}:5000" if "http" in GC_ML_HOST else f"http://{GC_ML_HOST}:5000"

def open_json(filename, path):
    '''Opens a json file'''
    with open(os.path.join(path, filename)) as f:
        return json.load(f)

def get_most_recent_dir(parent_dir):
    
    subdirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
    if len(subdirs) > 0:
        return max(subdirs, key=os.path.getctime)
    else:
        logger.error("There are no subdirectories to retrieve most recent data from")
        return None

def delete_files(path):
    '''Deletes all files in a directory'''
    print(f"Cleaning up: removing test files from {str(path)}")
    for file in os.listdir(path):
        fpath = os.path.join(path, file)
        print(fpath)
        try:
            shutil.rmtree(fpath)
        except OSError:
            os.remove(fpath)
    try:
        os.rmdir(path)
    except OSError as e:
        logger.error("Error: %s : %s" % (path, e.strerror))

def wait(filename, path, type, attempts=180):

    i = 0
    condition = False
    while i < attempts:
        if type == 'open_json':
            try:
                condition = open_json(filename, path)
            except:
                pass
        elif type == 'check_file':
            condition = os.path.isfile(os.path.join(path, filename))
        elif type == 'check_dir':
            condition = os.path.isdir(path) and len(os.listdir(path)) >0
        if condition:
            print("Condition met, breaking the wait loop")
            break
        else:
            print(f"Countdown: {str((attempts-i)*5)} seconds left...")
            i += 1
            time.sleep(5)
    
    return condition

def wait_matching_dir(base_dir, timestamp, attempts = 180):

    i = 0
    passed = False
    while i < attempts:
        print(f"Countdown: {str((attempts-i)*5)} seconds left...")
        most_recent = get_most_recent_dir(base_dir)
        if str(most_recent).split('/')[-1] == str(timestamp):
            print("Directory available, breaking the wait loop")
            passed = True
            break
        else:
            i += 1
            time.sleep(5)
    
    return passed

class TestTrain():

    def __init__(self, model):

        self.model = model
    
    def call_finetune(self):

        print("*** Requesting finetune from MLAPI...")

        model_dict = {
            "build_type": "sent_finetune",
            "model": self.model,
            "batch_size": 8,
            "epochs": 1,
            "warmup_steps": 100,
            "remake_train_data": True,
            "testing_only": True
            }
        resp = http.post(API_URL + "/trainModel", json=model_dict)

        print(f"Connected to MLAPI: {str(resp.ok)}")


    def made_validation_data(self, val_path):

        try:
            ## check created validation data
            test_any = json.loads(open_json("intelligent_search_data.json", "gamechangerml/data/test_data/test_validation/any"))
            test_silver = json.loads(open_json("intelligent_search_data.json", "gamechangerml/data/test_data/test_validation/silver"))
            test_gold = json.loads(open_json("intelligent_search_data.json", "gamechangerml/data/test_data/test_validation/gold"))

            gold = json.loads(open_json("intelligent_search_data.json", os.path.join(val_path, "gold")))
            silver = json.loads(open_json("intelligent_search_data.json", os.path.join(val_path, "silver")))
            any_ = json.loads(open_json("intelligent_search_data.json", os.path.join(val_path, "any")))

            results = {
                "Gold correct data match": gold['correct_vals'] == test_gold['correct_vals'],
                "Gold incorrect data match": gold['incorrect_vals'] == test_gold['incorrect_vals'],
                "Silver correct data match": silver['correct_vals'] == test_silver['correct_vals'],
                "Silver incorrect data match": silver['incorrect_vals'] == test_silver['incorrect_vals'],
                "Any correct data match": any_['correct_vals'] == test_any['correct_vals'],
                "Any incorrect data match": any_['incorrect_vals'] == test_any['incorrect_vals']
            }
        except:
            results = {}

        print(results)

    def made_training_data(self, metadata, training_path):
        
        try:
            df = pd.read_csv(os.path.join(training_path, "retrieved_paragraphs.csv"))

            results = {
                "At least one matching doc per query": df['num_matching_docs'].min() >= 1,
                "At least one nonmatching doc per query": df['num_nonmatching_docs'].min() >= 1,
                "No overlapping docs between match/nonmatch paragraphs": df['overlap'].sum() == 0,
                "Balance of classes >=0.2 ": df['par_balance'].min() >= 0.2,
                "Train/test query counts match": metadata['n_queries'] == '21 train queries / 5 test queries'
            }

        except:
            results = {}

        print(results)
    

    def finetuned_model(self, metadata):

        try:
            results = {
                "Num training samples > 100": metadata["n_training_samples"] > 100
            }
        except:
            results = {}

        print(results)

    def evaluated_model(self, gold_evals_path):

        try:
            eval_file = [i for i in os.listdir(gold_evals_path) if i[:14]=="retriever_eval"][0]
            print(eval_file)
            gold_evals = open_json(eval_file, gold_evals_path)

            results = {
                "Made gold data evals": bool(gold_evals),
                "Query count matches": gold_evals["query_count"] == 33,
                "MRR greater than 0": gold_evals["MRR"] > 0,
                "mAP greater than 0": gold_evals["mAP"] > 0,
                "recall greater than 0": gold_evals["recall"] > 0
            }
        except:
            results = {}

        print(results)

    def cleanup_files(self, eval_path, training_path, model_path):

        try:
            delete_files(training_path)
            delete_files(eval_path)
            delete_files(model_path)
        except Exception as e:
            logger.warning("Could not delete test files")
            logger.warning(e)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Test finetuning")

    parser.add_argument("--model", "-m", dest="model", help="base transformer model for finetuning")
    parser.add_argument("--cleanup", "-c", dest="cleanup", required=False, help="whether to delete files after test")
    args = parser.parse_args()
    model = args.model
    cleanup = args.cleanup if args.cleanup else True
    
    try:
        test = TestTrain(model)
        test.call_finetune()
       
        time.sleep(15) # wait for a new directory

        print("\n*** Checking validation data created...")
        val_path = get_most_recent_dir("gamechangerml/data/validation/domain/sent_transformer")
        timestamp = str(val_path).split('/')[-1]
        gold_dir = os.path.join(val_path, "gold")
        print(f"Looking for gold validation data at: {gold_dir}")
        passed = wait("intelligent_search_data.json", gold_dir, type='check_file')

        if passed:
            test.made_validation_data(val_path)
        else:
            print("Did not find validation data")
            quit
        
        print("\n*** Checking training data created...")
        train_dir = ("gamechangerml/data/training/sent_transformer")
        passed = wait_matching_dir(train_dir, timestamp)

        if passed:
            training_path = get_most_recent_dir(train_dir)
        else:
            print("Could not get updated training data dir")
            quit

        print(f"Looking for training metadata at: {training_path}")
        metadata = wait("training_metadata.json", training_path, type='open_json') 
            
        if metadata:
            time.sleep(2)
            test.made_training_data(metadata, training_path)
        else:
            print("Did not find training data")
            quit
        
        
        print("\n*** Checking finetuned model created...")
        model_name = test.model + '_TEST_' + timestamp
        model_dir = "gamechangerml/models/transformers"
        passed = wait_matching_dir(model_dir, model_name)
        if passed:
            model_path = get_most_recent_dir(model_dir)
        else:
            print("Could not get updated model dir")
            quit

        print(f"Looking for finetuned model files at: {model_path}")
        model_metadata = wait("metadata.json", model_path, type = 'open_json')

        if model_metadata:
            test.finetuned_model(model_metadata)
        else:
            print("Did not finetune the model")
            quit
    

        print("\n*** Checking model evaluations created...")
        gold_evals_dir = os.path.join(model_path, "evals_gc", "gold")
        print(f"Looking for gold standard evaluations at: {gold_evals_dir}")
        passed = wait("", gold_evals_dir, type='check_dir', attempts=500)

        if passed:
            test.evaluated_model(gold_evals_dir)
        else:
            print("Did not evaluate the model")
            quit
        
        print("*** Deleting test files...")
        if passed and cleanup:
            test.cleanup_files(val_path, training_path, model_path)

    except Exception as e:
        logger.warning(e, exc_info=True)