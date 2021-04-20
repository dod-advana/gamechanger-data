# The MIT License (MIT)
# Subject to the terms and conditions contained in LICENSE
import logging

from transformers import RobertaForSequenceClassification
from transformers import RobertaTokenizer

from dataScience.src.text_classif.classifier import Classifier
from dataScience.src.text_classif.utils.checkpoint_handler import (
    load_checkpoint,
)

logger = logging.getLogger(__name__)


class RobertaClassifier(Classifier):
    def __init__(self, config_yaml):

        self.model_class = RobertaForSequenceClassification
        self.tokenizer_class = RobertaTokenizer

        super(RobertaClassifier, self).__init__(config_yaml)

    def load_model_tokenizer(self):
        """
        This sets the class attributes `model` and `tokenizer`

        Returns:
            None

        """
        logger.info("loading model tokenizer")
        if self.cfg.use_checkpoint:
            logger.info("loading from checkpoint")
            self.model, self.tokenizer = load_checkpoint(
                self.cfg.use_checkpoint, self.model_class,
                self.tokenizer_class, self.device, self.__version__)
            logger.info(
                "model loaded from checkpoint : {}".format(self.model_class)
            )
        else:
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
