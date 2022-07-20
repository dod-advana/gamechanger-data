# The MIT License (MIT)
# Subject to the terms and conditions in LICENSE
# borrowed from `run_glue.py`, HF
import logging
import os
import random
import time

import numpy as np
import torch
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler
from torch.utils.data import TensorDataset, random_split
from torch.utils.tensorboard import SummaryWriter
from tqdm import tqdm
from transformers import AdamW
from transformers import get_linear_schedule_with_warmup

import gamechangerml.src.text_classif.utils.config as config
import gamechangerml.src.text_classif.version as v
from gamechangerml.src.text_classif.utils import checkpoint_handler as ch
from gamechangerml.src.text_classif.utils import classifier_utils as cu
from gamechangerml.src.text_classif.utils import metrics as clf_metrics

logger = logging.getLogger(__name__)


class Classifier(object):

    __version__ = v.__version__

    def __init__(self, config_yaml):
        """
        This is a base class for sentence classification based on Hugging
        Face models and `torch`.

        The user is required to subclass this and provide methods for
        `load_model_tokenizer()`.

        Args:
            config_yaml (str): path and file of the configuration file

        Properties:
            cfg (Config): class whose attributes are the configuration items

            runtime (dict): holds configuration items and other data;
                subclasses can add whatever they need.

            true_val (list): validation labels (ground truth)

            predicted_val (list): predicted labels in validation

            logits (np.array): matrix of validation logits

        Raises
            FileNotFoundError if the checkpoint path is not valid

        """
        logger.info(
            "{} version {}".format(self.__class__.__name__, self.__version__)
        )
        try:
            self.cfg, cfg_dict = config.read_verify_config(config_yaml)
            _, self.cfg_name = os.path.split(config_yaml)
            self.config_yaml = config_yaml
        except (FileNotFoundError, ValueError) as e:
            raise e

        self.runtime = dict()
        self.runtime["class"] = str(self.__class__.__name__)
        self.runtime["version"] = self.__version__
        self.runtime["config"] = self.cfg_name

        cfg_stats = {k_.replace("_", " "): v_ for k_, v_ in cfg_dict.items()}
        self.runtime.update(cfg_stats)

        if self.cfg.random_state is None:
            self.cfg.random_state = np.random.randint(0, 100)
        random.seed(self.cfg.random_state)
        np.random.seed(self.cfg.random_state)
        torch.manual_seed(self.cfg.random_state)

        self.model = None
        self.tokenizer = None
        self.optimizer = None
        self.scheduler = None
        self.input_ids = None
        self.attention_masks = None
        self.tensor_labels = None
        self.optimizer_grouped_parameters = None

        self.predicted_val = None
        self.true_val = None
        self.logits = None
        self.global_step = 0

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.runtime["device"] = str(self.device)

        self.best_loss = float("inf")
        self.max_len = 0

        # set up tensorboard, if configured
        if self.device == "gpu":
            self.summary_writer = None
        elif self.cfg.tensorboard_path is not None:
            self.summary_writer = SummaryWriter(
                self.cfg.tensorboard_path, comment=self.cfg.log_id
            )
        else:
            self.summary_writer = None

        # XLM, DistilBERT and RoBERTa don't use segment_ids
        # so use token_type_ids for these model types
        self.t_id_models = ["xlnet"]

        self.batch_log_fmt = (
            "\tbatch {:>5,} / {:>5,} " + "\tloss : {:>0.3f}\telapsed : {:}"
        )
        self.epoch_fmt = (
            " " * 10 + "=" * 20 + " Epoch {:>3,d} / {:>3,d} " + "=" * 20
        )

        logger.info(self.__repr__())

        self.training_stats = list()
        self.load_model_tokenizer()

    def __repr__(self):
        return '{}(config_yml="{}")'.format(
            self.__class__.__name__,
            self.config_yaml,
        )

    def retrieve_model_name_path(self):
        """
        This function is used for supplying either the model name, or the saved model directory, when instantiating
        *ForSequenceClassification() objects. If no load_saved_model_dir is supplied, use the OOTB model from HF, otherwise
        load in the saved pytorch_model.bin from the load_saved_model_dir specified
        Returns: (str) model name, or model path, for the HF model
        """
        if self.cfg.load_saved_model_dir:
            model_name_or_path = self.cfg.load_saved_model_dir
        else:
            model_name_or_path = self.cfg.model_name
        return model_name_or_path

    def train_test_ds(self, texts, labels):
        """
        Split into training and validation subsets; create `TensorDataset`s

        Args:
            texts (list): text for training / validation

            labels (list): labels (`int`) corresponding to each sentence

        Returns:
            TensorDataset, TensorDataset
        """
        self._tokenize_encode(texts)
        labels = torch.tensor(labels)
        dataset = TensorDataset(self.input_ids, self.attention_masks, labels)

        train_size = int(self.cfg.split * len(dataset))
        val_size = len(dataset) - train_size

        train_dataset, val_dataset = random_split(
            dataset, [train_size, val_size]
        )

        self.runtime["training samples"] = train_size
        self.runtime["validation samples"] = val_size

        logger.info("    train samples : {:>5,d}".format(train_size))
        logger.info("      val samples : {:>5,d}".format(val_size))
        return train_dataset, val_dataset

    def load_model_tokenizer(self):
        """
        Wrapper for loading one of the SequenceClassifier models and
        a matching tokenizer. This method must set the class variables
        `model` and `tokenizer`.
        """
        raise NotImplementedError("this method requires implementation")

    def load_scheduler(self, train_dataloader):
        """
        Loads the scheduler for an `optimizer`. The default is
        `get_linear_schedule_with_warmup()`;

        Args:
            train_dataloader (DataLoader): a `DataLoader` object

        Returns:
            None

        """
        logger.info("load scheduler, epochs : {:>3,d}".format(self.cfg.epochs))

        total_steps = len(train_dataloader) * self.cfg.epochs
        self.scheduler = get_linear_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.cfg.warmup_steps,
            num_training_steps=total_steps,
        )
        self.runtime["total steps"] = total_steps
        logger.info("scheduler is loaded")

    def load_optimizer(self):
        """
        Loads the AdamW optimizer (default)

        Returns:
            None
        """
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.cfg.lr,
            eps=self.cfg.eps,
            weight_decay=self.cfg.weight_decay,
        )
        logger.info("optimizer is loaded : {}".format(str(self.optimizer)))
        self.runtime["optimizer"] = "AdamW"

    def fit(self, train_sentences, train_labels):
        """
        This creates the train/validation data and trains the model according
        to what is in the configuration.

        Args:
            train_sentences (list): text to train

            train_labels (list): label (`int`) in [0, 1, 2, ...] for each
                entry in `train_sentences`

        Returns:
            None

        """
        # TODO roll this into `train`?
        train_ds, test_ds = self.train_test_ds(train_sentences, train_labels)
        self.train(train_ds, test_ds)

    def _dataloader(self, train_dataset, val_dataset):
        train_dataloader = DataLoader(
            train_dataset,
            sampler=RandomSampler(train_dataset),
            batch_size=self.cfg.batch_size,
            drop_last=self.cfg.drop_last,
        )
        val_dataloader = DataLoader(
            val_dataset,
            sampler=SequentialSampler(val_dataset),
            batch_size=self.cfg.batch_size,
            drop_last=self.cfg.drop_last,
        )
        return train_dataloader, val_dataloader

    def _input_ids(self, sentences):
        for sent in sentences:
            input_ids = self.tokenizer.encode(sent, add_special_tokens=True)
            self.max_len = max(self.max_len, len(input_ids))

        if self.max_len > 512:
            logger.warning("truncate : {}".format(self.cfg.truncate))
        self.max_len = cu.next_pow_two(self.max_len)

    def _tokenize_encode(self, texts):
        if self.cfg.max_seq_len is None:
            self._input_ids(texts)
        else:
            self.max_len = self.cfg.max_seq_len

        logger.info("max seq length : {}".format(self.max_len))
        self.runtime["max seq len"] = self.max_len

        self.input_ids = list()
        self.attention_masks = list()

        # `encode_plus()` does all the heavy lifting
        logger.info("tokenizing, encoding...")
        for text in texts:
            encoded_dict = self.tokenizer.encode_plus(
                text,
                add_special_tokens=True,
                max_length=self.max_len,
                pad_to_max_length=True,
                padding="max_length",
                truncation=self.cfg.truncate,
                return_attention_mask=True,
                return_tensors="pt",
            )
            self.input_ids.append(encoded_dict["input_ids"])
            self.attention_masks.append(encoded_dict["attention_mask"])

        # make into tensors
        self.input_ids = torch.cat(self.input_ids, dim=0)
        self.attention_masks = torch.cat(self.attention_masks, dim=0)
        logger.info("done tokenizing, encoding...")

    def train(self, train_ds, val_ds):
        avg_loss_items = list()
        train_dataloader, val_dataloader = self._dataloader(train_ds, val_ds)

        self.load_model_tokenizer()
        self.model.to(self.device)
        self.load_optimizer()
        self.load_scheduler(train_dataloader)

        cfg_str = config.log_config(self.runtime)
        if self.summary_writer is not None:
            self.summary_writer.add_text(self.cfg.log_id, cfg_str)

        logger.info("into the breach...")
        start_t = time.time()
        for epoch in range(self.cfg.epochs):
            sum_train_loss = 0
            epoch_start_t = time.time()
            logger.info(self.epoch_fmt.format(epoch + 1, self.cfg.epochs))

            # put the model into training mode
            self.model.train()

            sum_train_loss, avg_loss_items = self._train_batch(
                train_dataloader, epoch_start_t, sum_train_loss, avg_loss_items
            )
            avg_train_loss = sum_train_loss / len(train_dataloader)
            avg_loss_items.append(avg_train_loss)
            train_t = time.time() - epoch_start_t
            logger.info("avg training loss : {:>3.4f}".format(avg_train_loss))

            self._validate(val_dataloader, epoch, avg_train_loss, train_t)

        logger.info(
            "training time : {}".format(cu.format_time(time.time() - start_t))
        )
        # final metrics  -> tensorboard
        if self.summary_writer is not None:
            self._tb_run_metrics()
        return self.training_stats

    def _train_batch(
        self, train_dataloader, epoch_start_t, sum_train_loss, avg_loss_items
    ):
        loss = float("inf")
        start_fibs = [1, 2]
        penultimate = start_fibs[-2]
        last = start_fibs[-1]
        next_log_step = penultimate + last
        len_train = len(train_dataloader)
        step = 0
        elapse = 0.0

        # the main show
        for step, batch in enumerate(train_dataloader):
            self.global_step += 1
            elapse = cu.format_time(time.time() - epoch_start_t)
            if step != 0 and step == next_log_step or step in start_fibs:
                b_log = self.batch_log_fmt.format(
                    step, len_train, loss, elapse
                )
                logger.info(b_log)
                if step not in start_fibs:
                    penultimate = last
                    last = next_log_step
                    next_log_step = penultimate + last

            batch = tuple(t.to(self.device) for t in batch)
            inputs = {
                "input_ids": batch[0],
                "attention_mask": batch[1],
                "labels": batch[2],
            }
            if self.cfg.model_type != "distilbert":
                inputs["token_type_ids"] = (
                    batch[2]
                    if self.cfg.model_type in self.t_id_models
                    else None
                )

            self.model.zero_grad()
            outputs = self.model(**inputs)
            loss, logits = outputs["loss"], outputs["logits"]

            sum_train_loss += loss.item()
            avg_loss_items.append(loss.item())

            # calc gradients; clip / norm to prevent exploding gradients
            loss.backward()
            if self.cfg.clip_grad_norm is not None:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), self.cfg.clip_grad_norm
                )
            # update tensorboard, if configured
            if self.summary_writer is not None:
                self.summary_writer.add_scalar(
                    "Loss / step", loss, self.global_step
                )
            # take one step forward
            self.optimizer.step()
            self.scheduler.step()

        b_log = self.batch_log_fmt.format(step + 1, len_train, loss, elapse)
        logger.info(b_log)
        return sum_train_loss, avg_loss_items

    def _validate_batch(self, validation_dataloader):
        for batch in tqdm(validation_dataloader):
            batch = tuple(t.to(self.device) for t in batch)
            inputs = {
                "input_ids": batch[0],
                "attention_mask": batch[1],
                "labels": batch[2],
            }
            if self.cfg.model_type != "distilbert":
                inputs["token_type_ids"] = (
                    batch[2]
                    if self.cfg.model_type in self.t_id_models
                    else None
                )

            with torch.no_grad():
                outputs = self.model(**inputs)
                loss, logits = outputs["loss"], outputs["logits"]
            yield inputs, loss, logits

    def _validate(
        self, validation_dataloader, epoch, avg_train_loss, trn_time
    ):
        logger.info("running validation")
        vt = time.time()
        total_eval_accuracy = 0.0
        total_eval_loss = 0.0
        val_loss = list()
        pred_flat = list()
        labels_flat = list()
        logits_score = list()
        logits_list = list()

        # change modes
        self.model.eval()
        for inputs, loss, logits in self._validate_batch(
            validation_dataloader
        ):
            total_eval_loss += loss.item()
            val_loss.append(loss.item())

            # move logits and labels to CPU
            logits = logits.detach().cpu().numpy()
            logits_score = clf_metrics.logit_score(logits)
            label_ids = inputs["labels"].to("cpu").numpy()

            total_eval_accuracy += clf_metrics.flat_accuracy(logits, label_ids)
            pred_flat_, lbl_flat = cu.flatten_labels(logits, label_ids)

            # accumulate the results across batches
            logits_list.append(logits)
            pred_flat.extend(pred_flat_)
            labels_flat.extend(lbl_flat)
            logits_score.extend(logits_score)

        self.predicted_val = pred_flat
        self.true_val = labels_flat
        self.logits = logits_score
        avg_val_accuracy = total_eval_accuracy / len(validation_dataloader)
        logger.info("   best loss : {:0.3f}".format(self.best_loss))

        # Calculate average loss over all of the batches.
        avg_val_loss = total_eval_loss / len(validation_dataloader)

        validation_time = cu.format_time(time.time() - vt)

        # gather metrics
        clf_report = clf_metrics.val_clf_report(labels_flat, pred_flat)
        cm_matrix = clf_metrics.cm_matrix(self.true_val, self.predicted_val)

        mcc = clf_metrics.mcc_val(self.true_val, self.predicted_val)

        # for multiclass classification, pass logits through softmax and use probability matrix in AUC computation
        if self.cfg.num_labels>2:
            softmax_layer = torch.nn.Softmax(dim=1)
            predicted_probas = softmax_layer(torch.Tensor(np.concatenate(logits_list)))
            try:
                auc_val = clf_metrics.auc_val(self.true_val, predicted_probas, binary_classif=False)
            except Exception as e:
                logger.warning(f"Unable to calcuate AUC for multiclass example, setting AUC to 0, due to following "
                               f"exception: {e}")
                auc_val=0.0
        else:
            auc_val = clf_metrics.auc_val(self.true_val, self.predicted_val, binary_classif=True)

        acc_score = clf_metrics.accuracy_score(
            self.true_val, self.predicted_val
        )

        logger.info("\n\n{}".format(clf_report))
        logger.info("confusion matrix\n\n\t{}\n".format(cm_matrix))
        logger.info("\tvalidation loss : {:>0.3f}".format(avg_val_loss))
        logger.info("\t            MCC : {:>0.3f}".format(mcc))
        logger.info("\t            AUC : {:>0.3f}".format(auc_val))
        logger.info("\t accuracy score : {:>0.3f}".format(acc_score))
        logger.info("\tvalidation time : {:}".format(validation_time))

        # Record all statistics from this epoch.
        self.training_stats.append(
            {
                "epoch": epoch + 1,
                "training_loss": avg_train_loss,
                "avg_val_loss": avg_val_loss,
                "avg_val_acc": avg_val_accuracy,
                "training_time": trn_time,
                "auc": auc_val,
                "mcc": mcc,
                "val_time": validation_time,
                "clf_report": clf_report,
                "config": self.runtime,
            }
        )
        # write to tensorboard, if it configured
        self._tb_epoch_metrics(avg_val_loss, auc_val, mcc, acc_score, epoch)

        if self.cfg.checkpoint_path is not None:
            self.runtime["timestamp"] = time.time()
            ch.write_checkpoint(
                self.cfg.checkpoint_path + "_epoch_{}".format(epoch + 1),
                self.model,
                self.tokenizer,
                avg_val_loss,
                self.training_stats[-1],
            )
            self.best_loss = avg_val_loss

    def _tb_epoch_metrics(self, avg_val_loss, auc_val, mcc, acc_score, epoch):
        if self.summary_writer is None:
            return
        self.summary_writer.add_scalar("avg loss/epoch", avg_val_loss, epoch)
        self.summary_writer.add_scalars(
            "Metrics",
            {"AUC": auc_val, "MCC": mcc, "ACC": acc_score},
            epoch,
        )

    def _tb_run_metrics(self):
        if self.summary_writer is None:
            return
        clf_report = clf_metrics.val_clf_report(
            self.true_val, self.predicted_val
        )
        cm_matrix = clf_metrics.cm_matrix(self.true_val, self.predicted_val)
        self.summary_writer.add_text("clf report", clf_report)
        self.summary_writer.add_text("cm matrix", cm_matrix.to_string())

        # kill it off
        self.summary_writer.flush()
        self.summary_writer.close()
        logger.info("tensorboard summary written")
