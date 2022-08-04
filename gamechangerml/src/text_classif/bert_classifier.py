# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging

from transformers import BertForSequenceClassification
from transformers import BertTokenizer

from gamechangerml.src.text_classif.classifier import Classifier

logger = logging.getLogger(__name__)


class BertClassifier(Classifier):
    def __init__(self, config_yaml):
        super(BertClassifier, self).__init__(config_yaml)

    def load_model_tokenizer(self):
        model_name_or_path = self.retrieve_model_name_path()
        self.model = BertForSequenceClassification.from_pretrained(
            model_name_or_path,
            num_labels=self.cfg.num_labels,
            output_attentions=False,
            output_hidden_states=False,
            return_dict=True,
        )

        self.tokenizer = BertTokenizer.from_pretrained(
            self.cfg.model_name, do_lower_case=True
        )
        logger.info("model is loaded : {}".format(self.cfg.model_name))
