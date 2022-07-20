from gamechangerml import DATA_PATH
from gamechangerml.api.utils import processmanager
from datetime import datetime
from gamechangerml.api.utils.logger import logger
from gamechangerml.src.utilities import utils as utils
from gamechangerml.src.utilities.test_utils import open_json, save_json, timestamp_filename
from gamechangerml.scripts.run_evaluation import eval_sent
from time import sleep
import tqdm
import threading
import logging
import gc
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import pandas as pd
from datetime import date
import sys
import os
import json
import torch
from torch.optim import Adam
import torch.nn.functional as F
from torch import nn
torch.cuda.empty_cache()

S3_DATA_PATH = "bronze/gamechanger/ml-data"

logging.root.addHandler(logging.StreamHandler(sys.stdout))
logging.basicConfig(force=True)
logger.setLevel(logging.INFO)


def fix_model_config(model_load_path):
    """Workaround for error with sentence_transformers==0.4.1 (vs. version 2.0.0 which our model was trained on)"""

    try:
        config = open_json("config.json", model_load_path)
        if "__version__" not in config.keys():
            try:
                st_config = open_json(
                    "config_sentence_transformers.json", model_load_path)
                version = st_config["__version__"]["sentence_transformers"]
                config["__version__"] = version
            except:
                config["__version__"] = "2.0.0"
            with open(os.path.join(model_load_path, "config.json"), "w") as outfile:
                json.dump(config, outfile)
    except:
        logger.info("Could not update model config file")

def format_inputs(train, test, data_dir):
    """Create input data for dataloader and df with train/test split data"""

    train_samples = []
    all_data = []
    count = 0
    total = len(train.keys()) + len(test.keys())
    for i in train.keys():
        texts = [train[i]["query"], train[i]["paragraph"]]
        score = float(train[i]["label"])
        inputex = InputExample(str(count), texts, score)
        train_samples.append(inputex)
        all_data.append([train[i]["query"], train[i]["doc"], score, "train"])
        count += 1

    for x in test.keys():
        texts = [test[x]["query"], test[x]["paragraph"]]
        score = float(test[x]["label"])
        all_data.append([test[x]["query"], test[x]["doc"], score, "test"])
        count += 1
        processmanager.update_status(processmanager.loading_data, count, total)

    df = pd.DataFrame(all_data, columns=["key", "doc", "score", "label"])
    df.drop_duplicates(subset = ['doc', 'score', 'label'], inplace = True)
    logger.info(f"Generated training data CSV of {str(df.shape[0])} rows")
    df_path = os.path.join(data_dir, timestamp_filename("finetuning_data", ".csv"))
    df.to_csv(df_path)

    return train_samples, df_path

class STFinetuner():

    def __init__(self, model_load_path, model_save_path, shuffle, batch_size, epochs, warmup_steps):

        fix_model_config(model_load_path)
        self.model_load_path = model_load_path
        self.model = SentenceTransformer(model_load_path)
        self.model_save_path = model_save_path
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.epochs = epochs
        self.warmup_steps = warmup_steps
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    def retrain(self, data_dir, testing_only, version):

        try:
            data = open_json("training_data.json", data_dir)
            train = data["train"]
            test = data["test"]

            if testing_only:
                logger.info(
                    "Creating smaller dataset just for testing finetuning.")
                train_queries = list(set([train[i]['query'] for i in train.keys()]))[:30]
                test_queries = list(set([test[i]['query'] for i in test.keys()]))[:10]
                train = {k: train[k] for k in train.keys() if train[k]['query'] in train_queries}
                test = {k: test[k] for k in test.keys() if test[k]['query'] in test_queries}
            
            del data
            gc.collect()

            processmanager.update_status(processmanager.training, 0, 1,thread_id=threading.current_thread().ident)
            sleep(0.1)
            # make formatted training data
            train_samples, df_path = format_inputs(train, test, data_dir)
            len_samples = len(train_samples)
            # finetune on samples
            logger.info("Starting dataloader...")
            # pin_memory=self.pin_memory)
            train_dataloader = DataLoader(
                train_samples, shuffle=self.shuffle, batch_size=self.batch_size)
            train_loss = losses.CosineSimilarityLoss(model=self.model)
            #del train_samples
            #gc.collect()
            logger.info("Finetuning the encoder model...")
            self.model.fit(train_objectives=[
                           (train_dataloader, train_loss)], epochs=self.epochs, warmup_steps=self.warmup_steps)
            processmanager.update_status(processmanager.training, 1, 0,thread_id=threading.current_thread().ident)
            logger.info("Finished finetuning the encoder model")
            # save model
            self.model.save(self.model_save_path)
            logger.info("Finetuned model saved to {}".format(
                str(self.model_save_path)))

            # save metadata with the finetuned model
            metadata = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "model_type": "finetuned encoder",
                "base_model_path": self.model_load_path,
                "current_model_path": self.model_save_path,
                "training_data_dir": df_path,
                "n_training_samples": len_samples,
                "version": version,
                "testing_only": testing_only,
                "shuffle": self.shuffle,
                "batch_size": self.batch_size,
                "epochs": self.epochs,
                "warmup_steps": self.warmup_steps
            }

            save_json("metadata.json", self.model_save_path, metadata)
            logger.info(f"Finetuned model metadata saved to {self.model_save_path}/metadata.json")
            
            # when not testing only, save to S3
            if not testing_only:
                logger.info("Saving data to S3...")
                s3_path = os.path.join(S3_DATA_PATH, f"{version}")
                logger.info(f"****    Saving new data files to S3: {s3_path}")
                dst_path = data_dir + ".tar.gz"
                model_name = datetime.now().strftime("%Y%m%d")
                logger.info("*** Attempting to save data tar")
                utils.create_tgz_from_dir(data_dir, dst_path)
                logger.info("*** Attempting to upload data to s3")
                utils.upload(s3_path, dst_path, "data", model_name)

                logger.info("Saving model to S3...")
                dst_path = self.model_save_path + ".tar.gz"
                utils.create_tgz_from_dir(src_dir=self.model_save_path, dst_archive=dst_path)
                model_id = self.model_save_path.split('_')[1]
                logger.info(f"*** Created tgz file and saved to {dst_path}")

                S3_MODELS_PATH = "bronze/gamechanger/models"
                s3_path = os.path.join(S3_MODELS_PATH, str(version))
                utils.upload(s3_path, dst_path, "transformers", model_id)
                logger.info(f"*** Saved model to S3: {s3_path}")

        except Exception as e:
            logger.warning("Could not complete finetuning")
            logger.error(e)
        
        return
