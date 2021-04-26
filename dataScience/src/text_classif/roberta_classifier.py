# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging

from transformers import RobertaForSequenceClassification
from transformers import RobertaTokenizer

from dataScience.src.text_classif.classifier import Classifier

logger = logging.getLogger(__name__)


class RobertaClassifier(Classifier):
    def __init__(self, config_yaml):
        super(RobertaClassifier, self).__init__(config_yaml)

    def load_model_tokenizer(self):
        """
        This sets the class attributes `model` and `tokenizer`

        Returns:
            None

        """
        logger.info("loading model tokenizer")
        self.model = RobertaForSequenceClassification.from_pretrained(
            self.cfg.model_name,
            num_labels=self.cfg.num_labels,
            output_attentions=False,
            output_hidden_states=False,
            return_dict=True,
        )
        self.tokenizer = RobertaTokenizer.from_pretrained(
            self.cfg.model_name, do_lower_case=True
        )
        logger.info("model is loaded : {}".format(self.cfg.model_name))
