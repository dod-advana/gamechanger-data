import logging
import re

import pandas as pd

import dataScience.src.text_classif.utils.entity_lookup as el
from dataScience.src.text_classif.utils.predict_glob import predict_glob

logger = logging.getLogger(__name__)


class EntityCoref(object):
    def __init__(self):
        """
        This implements a simplistic entity co-reference mechanism geared to
        the structure of many DoD documents.

        When the 'responsibilities' section has been reached, begin looking
        for the word 'shall'. If found, see if it contains a entity in the
        lookups. The entity is associated with sentences labeled as '1'
        (modulo details).
        """
        self.RESP = "RESPONSIBILITIES"
        self.SENTENCE = "sentence"
        self.KW = "shall"
        self.KW_RE = re.compile("\\b" + self.KW + "\\b[:,]?")
        self.NA = "NA"
        self.TC = "top_class"
        self.ENT = "entity"
        self.USC_DOT = "U.S.C."
        self.USC = "USC"
        self.USC_RE = "\\b" + self.USC + "\\b"

        self.abrv_lu, self.ent_lu = el.build_entity_lookup()
        self.pop_entities = None

    def _new_edict(self, value=None):
        value = self.NA or value
        return {self.ENT: value}

    def _attach_entity(self, output_list, entity_list):
        curr_entity = self.NA
        last_entity = self.NA

        for entry in output_list:
            logger.debug(entry)
            sentence = entry[self.SENTENCE]
            new_entry = self._new_edict()
            new_entry.update(entry)

            if entry[self.TC] == 0 and self.KW in sentence:
                curr_entity = re.split(self.KW_RE, sentence, maxsplit=1)[
                    0
                ].strip()
                if not el.contains_entity(
                    curr_entity, self.abrv_lu, self.ent_lu
                ):
                    curr_entity = self.NA
                else:
                    last_entity = curr_entity
            elif entry[self.TC] == 1:
                if curr_entity == self.NA:
                    curr_entity = last_entity
                    last_entity = curr_entity
                new_entry[self.ENT] = curr_entity
                logger.debug("entity : {}".format(curr_entity))
            entity_list.append(new_entry)

    def _populate_entity(self, output_list):
        entity_list = list()
        for idx, entry in enumerate(output_list):
            e_dict = self._new_edict()
            e_dict.update(entry)
            if e_dict[self.TC] == 0 and self.RESP in entry[self.SENTENCE]:
                entity_list.append(e_dict)
                self._attach_entity(output_list[idx + 1 :], entity_list)
                return entity_list
            else:
                entity_list.append(e_dict)
        return entity_list

    def make_table(
        self, model_path, data_path, glob, max_seq_len, batch_size, output_csv
    ):
        """
        Loop through the documents, predict each piece of text and attach
        an entity.

        The arguments are shown below in `args`.

        A list entry looks like:

            {'top_class': 0,
             'prob': 0.997,
              'src': 'DoDD 5105.21.json',
             'label': 0,
             'sentence': 'Department of...'}

        --> `top_class` is the predicted label

        Returns:
            None

        """
        self.pop_entities = list()
        for output_list, file_name in predict_glob(
            model_path, data_path, glob, max_seq_len, batch_size
        ):
            logger.debug("num input : {:,}".format(len(output_list)))
            self.pop_entities = self._populate_entity(output_list)
            logger.debug(
                "processed : {:,}  {}".format(
                    len(self.pop_entities), file_name
                )
            )
        try:
            if output_csv is not None:
                self.to_csv(output_csv)
        except FileNotFoundError as e:
            raise e

    def to_df(self):
        df = pd.DataFrame(self.pop_entities)
        df[self.SENTENCE] = [
            re.sub(self.USC_RE, self.USC_DOT, str(x))
            for x in df[self.SENTENCE]
        ]
        return df

    def to_csv(self, output_csv):
        df = self.to_df()
        df.to_csv(output_csv, index=False)
