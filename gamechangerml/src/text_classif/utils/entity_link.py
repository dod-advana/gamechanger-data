import logging
import os
import re

import pandas as pd

import gamechangerml.src.text_classif.utils.entity_mentions as em
from gamechangerml.src.text_classif.utils.predict_glob import predict_glob
from gamechangerml.src.text_classif.utils.top_k_entities import top_k_entities

logger = logging.getLogger(__name__)


class EntityLink(object):
    def __init__(
        self, entity_csv=None, mentions_json=None, use_na=True, topk=3
    ):
        """
        Links a statement to an entity using a type of 'nearest entity' method.
        If such linking is not possible, the top k most frequently occurring
        entities is used.

        Args:
            entity_csv (str): csv containing entity,abbreviation  if
                an abbreviation exists

            mentions_json (str): name of the entity mentions json produced by
                `entity_mentions.py`

            use_na (bool): if True, use self.NA instead of the top k mentions
                when entity linking fails

            topk (int): top k mentions to use when an entity has failed
        """
        if not os.path.isfile(entity_csv):
            raise FileExistsError("no entity file, got {}".format(entity_csv))
        if not os.path.isfile(mentions_json):
            raise FileExistsError(
                "no mentions file {}, got".format(mentions_json)
            )

        topk = max(1, topk)
        logger.info("top k : {}".format(topk))
        self.top_k_in_doc = top_k_entities(mentions_json, top_k=topk)
        self.abbrv_re, self.entity_re = em.make_entity_re(entity_csv)

        self.use_na = use_na
        self.RESP = "RESPONSIBILITIES"
        self.SENT = "sentence"

        # NB: KW can be any valid regex like "shall|will"
        self.KW = "shall"
        self.KW_RE = re.compile("\\b" + self.KW + "\\b[:,]?")

        self.NA = "Unable to connect Responsibility to Entity"

        self.TOPCLASS = "top_class"
        self.ENT = "entity"
        self.SRC = "src"

        self.USC_DOT = "U.S.C."
        self.USC = "USC"
        self.USC_RE = "\\b" + self.USC + "\\b"
        self.PL = "P.L."
        self.PL_DOT = "P. L."
        self.PL_RE = "\\b" + self.PL_DOT + "\\b"
        self.EO = "E.O."
        self.EO_DOT = "E. O."
        self.EO_RE = "\\b" + self.EO_DOT + "\\b"

        self.dotted = [self.USC_DOT, self.PL, self.EO]
        self.subs = [self.USC, self.PL, self.EO]
        self.sub_back = [self.USC_DOT, self.PL_DOT, self.EO_DOT]
        self.unsub_re = [self.USC_RE, self.PL_RE, self.EO_RE]

        self.pop_entities = None
        self.failed = list()

    def _new_edict(self, value=None):
        if value is None:
            value = self.NA
        return {self.ENT: value}

    def _re_sub(self, sentence):
        for regex, sub in zip(self.dotted, self.subs):
            sentence = re.sub(regex, sub, sentence)
        return sentence

    def _unsub_df(self, df, regex, sub):
        df[self.SENT] = [re.sub(regex, sub, str(x)) for x in df[self.SENT]]

    def _resolve_na(self, doc_name):
        if self.use_na:
            return self.NA
        if doc_name in self.top_k_in_doc:
            ent = ";".join(self.top_k_in_doc[doc_name])
            logger.debug("entity : {}".format(self.top_k_in_doc[doc_name]))
            return ent
        else:
            logger.warning("can't find {} for lookup".format(doc_name))
            return self.NA

    def _link_entity(self, output_list, entity_list, default_ent):
        curr_entity = default_ent
        for prediction in output_list:
            sentence = prediction[self.SENT]
            sentence = self._re_sub(sentence)

            new_entry = self._new_edict(value=curr_entity)
            new_entry.update(prediction)

            if prediction[self.TOPCLASS] == 0:
                new_entry[self.ENT] = default_ent
                match_obj = re.search(self.KW, sentence)
                if match_obj is not None:
                    cand_entity = re.split(self.KW_RE, sentence, maxsplit=1)[
                        0
                    ].strip()
                    ent_list = em.contains_entity(
                        cand_entity, self.entity_re, self.abbrv_re
                    )
                    if ent_list:
                        curr_entity = cand_entity
            elif prediction[self.TOPCLASS] == 1:
                new_entry[self.ENT] = curr_entity
            else:
                msg = "unknown prediction for '{}', ".format(sentence)
                msg += "got {}".format(prediction[self.TOPCLASS])
                logger.warning(msg)
            entity_list.append(new_entry)

    def _populate_entity(self, output_list):
        entity_list = list()
        for idx, entry in enumerate(output_list):
            doc_name = entry[self.SRC]
            default_ent = self._resolve_na(doc_name)
            e_dict = self._new_edict(value=self._resolve_na(doc_name))
            e_dict.update(entry)
            if e_dict[self.TOPCLASS] == 0 and self.RESP in entry[self.SENT]:
                entity_list.append(e_dict)
                self._link_entity(
                    output_list[idx + 1 :], entity_list, default_ent
                )
                return entity_list
            else:
                entity_list.append(e_dict)
        return entity_list

    def make_table(self, model_path, data_path, glob, max_seq_len, batch_size):
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
            logger.info("num input : {:>4,d}".format(len(output_list)))
            pop_list = self._populate_entity(output_list)
            logger.info(
                "processed : {:>4,d}  {}".format(len(pop_list), file_name)
            )
            self.pop_entities.extend(pop_list)

    def _to_df(self):
        if not self.pop_entities:
            raise ValueError("no data to convert; please run `make_table()`?")
        else:
            return pd.DataFrame(self.pop_entities)

    def to_df(self):
        """
        Creates a pandas data frame from the populated entities list

        Returns:
            pd.DataFrame

        """
        df = self._to_df()
        for regex, sub in zip(self.unsub_re, self.sub_back):
            self._unsub_df(df, regex, sub)
        return df

    def to_csv(self, output_csv):
        df = self._to_df()
        df.to_csv(output_csv, index=False)
