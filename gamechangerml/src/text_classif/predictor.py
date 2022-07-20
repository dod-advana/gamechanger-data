import datetime
import json
import logging
import os

import torch
import torch.nn.functional as nnf
import transformers as trf
from packaging import version

import gamechangerml.src.text_classif.version as v
from gamechangerml.src.text_classif.utils import classifier_utils as cu

logger = logging.getLogger(__name__)


def _from_pretrained(cls, *args, **kw):
    """
    Load the transformers model
    """
    try:
        return cls.from_pretrained(*args, **kw)
    except OSError as e:
        raise e


def _log_metadata(model_path, curr_version):
    stats_path = os.path.join(model_path, "run_stats.json")
    if not os.path.isfile(stats_path):
        logger.info("no 'run_stats.json' in the checkpoint directory")
        return

    ts = os.path.getmtime(os.path.join(model_path, "config.json"))
    with open(stats_path) as f:
        chkpt_stats = json.load(f)
    if "timestamp" in chkpt_stats:
        ts = chkpt_stats["timestamp"]

    c_version = chkpt_stats["config"]["version"]
    if curr_version is not None:
        if version.parse(c_version) < version.parse(curr_version):
            msg = "model was created with v{}; you're using v{}".format(
                c_version, curr_version
            )
            logger.warning(msg)

    ts = datetime.datetime.fromtimestamp(ts)
    val_loss = chkpt_stats["avg_val_loss"]
    logger.info(
        "      checkpoint time : {}".format(ts.strftime("%Y-%m-%d %H:%M:%S"))
    )
    class_name = chkpt_stats["config"]["class"]
    base_model = chkpt_stats["config"]["model name"]
    logger.info("      current version : {}".format(curr_version))
    logger.info(" created with version : {}".format(c_version))
    logger.info("       training class : {}".format(class_name))
    logger.info("           base model : {}".format(base_model))
    logger.info("                epoch : {}".format(chkpt_stats["epoch"]))
    logger.info("         avg val loss : {:0.3f}".format(val_loss))
    logger.info("                  mcc : {:0.3f}".format(chkpt_stats["mcc"]))


class Predictor:

    __version__ = v.__version__

    def __init__(self, model_name_or_path, num_labels=2):
        """
        Loads a model and predicts each example in a dictionary of examples.

        Args:
            model_name_or_path (str): HF model name or path of the model

            num_labels (int): number of labels

        Raises:
            OSError, RuntimeError if model loading fails
        """
        self.model_pn = model_name_or_path
        self.num_labels = num_labels

        self.compute_grads = False
        self.been_warned = False

        logger.info("{} v{}".format(self.__class__.__name__, self.__version__))

        try:
            self.tokenizer = trf.AutoTokenizer.from_pretrained(
                model_name_or_path
            )
            model_config = trf.AutoConfig.from_pretrained(
                model_name_or_path,
                num_labels=self.num_labels,
                output_hidden_states=True,
                output_attentions=True,
            )
            self.model = _from_pretrained(
                trf.AutoModelForSequenceClassification,
                model_name_or_path,
                config=model_config,
            )
            _log_metadata(model_name_or_path, self.__version__)
            self.model.eval()

            logging.info("model loaded")
        except (OSError, RuntimeError) as e:
            raise e

    def predict(self, inputs, batch_size=8, max_seq_len=128):
        """
        Predict the class on a set of inputs.

        Args:
            inputs (list): text to be classified, one example per entry

            batch_size (int): batch size to use

            max_seq_len (int): number of tokens to use

        Yields:
            List[Dict]

        """
        if not 128 <= max_seq_len <= 512:
            raise ValueError(
                "must have  128 <= max_seq_len <= 512, got {}".format(
                    max_seq_len
                )
            )
        if not self.been_warned and batch_size < 8:
            logger.warning("batch_size of at least 8 is recommended")
            self.been_warned = True

        batch_size = min(len(inputs), batch_size)
        batch = list()
        for ex in inputs:
            if len(batch) < batch_size:
                batch.append(ex)
            if len(batch) >= batch_size:
                outputs = self._predict_batch(batch, max_seq_len)
                yield outputs
                batch = list()
        if len(batch) > 0:
            outputs = self._predict_batch(batch, max_seq_len)
            yield outputs

    def _predict_batch(self, inputs, max_seq_len):
        try:
            encoded_input = self.tokenizer.batch_encode_plus(
                [ex["sentence"] for ex in inputs],
                return_tensors="pt",
                add_special_tokens=True,
                max_length=max_seq_len,
                padding="longest",
                truncation="longest_first",
            )
        except (KeyError, RuntimeError) as e:
            raise e
        # Check and send to cuda (GPU) if available
        if torch.cuda.is_available():
            self.model.cuda()
            for tensor in encoded_input:
                encoded_input[tensor] = encoded_input[tensor].cuda()

        # Run a forward pass with gradient.
        with torch.set_grad_enabled(self.compute_grads):
            out: trf.modeling_outputs.SequenceClassifierOutput = self.model(
                **encoded_input
            )
        probas = nnf.softmax(out.logits, dim=1)
        top_p, top_class = probas.topk(1, dim=1)
        batched_outputs = {
            "prob": top_p,
            "input_ids": encoded_input["input_ids"],
            "ntok": torch.sum(encoded_input["attention_mask"], dim=1),
            "top_class": top_class,
            "cls_emb": out.hidden_states[-1][:, 0],  # last layer, first token
        }
        detached_outputs = {
            k: val.cpu().detach().numpy() for k, val in batched_outputs.items()
        }
        batch_output = self._post_process(detached_outputs, inputs)
        return batch_output

    @staticmethod
    def _post_process(detached_outputs, inputs):
        outputs = list()
        keys = inputs[0].keys()
        for idx, output in enumerate(cu.unbatch_preds(detached_outputs)):
            out_dict = dict()
            tc = detached_outputs["top_class"].flatten()
            prob = detached_outputs["prob"].flatten()
            out_dict["top_class"] = tc[idx]
            out_dict["prob"] = prob[idx]
            out_dict.update({k: inputs[idx][k] for k in keys})
            outputs.append(out_dict)
        return outputs
