import logging
import re
from typing import Dict, Generator, Union

# import fails in gensim 4.
# from gensim.summarization.summarizer import summarize
# from summarizer import Summarizer
# from summarizer.sentence_handler import SentenceHandler

from gamechangerml.src.utilities.text_utils import summary_clean

logger = logging.getLogger(__name__)


def chunker(seq: str, size: int) -> Generator[str, None, None]:
    """
    Splits up large text into smaller pieces for processing
    """
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))


class Summary(object):
    """
    Base class for summary objects (Gensim & Bert).
    Text to summarize is cleaned using summary_clean function from text_utils.

    TODO: add parsing for long docs
    """

    def __init__(self, text: str, min_par_len=15):
        self.text = summary_clean(text, min_par_len)


class GensimSumm(Summary):
    """
    Leverages Gensim's summarizer using the TextRank algorithm to create
    text summaries.
    https://radimrehurek.com/gensim_3.8.3/summarization/summariser.html
    https://arxiv.org/abs/1602.03606

    Args:
    - text (str): body of text to summarize
    - long_doc (bool): True if len(text) > 100000
    - word_count (int): maximum word count for returned summaries
    """

    def __init__(self, text: str, long_doc: bool = True, word_count: int = 30):

        super().__init__(text)
        self.long_doc = long_doc
        self.word_count = word_count

    def make_summary(self) -> Union[str, None]:  # from original summary.py

        count = 0
        try:
            if self.long_doc:
                summary = ""
                for group in chunker(seq=self.text, size=100000):
                    count += 1
                    summary += summarize(group, word_count=self.word_count)
                    summary += " "
            else:
                summary = summarize(self.text, word_count=self.word_count)

            if count > 3:
                summary = summarize(summary, word_count=self.word_count * 3)

            summary = re.sub(r"\n", " ", summary)
            summary = re.sub(r"\r", "", summary)
            summary = " ".join(summary.split())

        except ValueError as e:
            summary = ""
            print(e)

        if not summary:
            return None
        return summary


class BertExtractiveSumm(Summary):
    """
    Leverages the Bert Extractive Summarizer to create text summaries.
    https://pypi.org/project/bert-extractive-summarizer/
    https://arxiv.org/abs/1906.04165

    Args:
    - text (str): body of text to summarize
    - long_doc (bool): True if len(text) > 100000
    - model_args (Dict): configuration for Bert Extractive Summarizer
        (from config file)
    - coreference (bool): whether or not to use coreference (default = true)
    """

    def __init__(
        self,
        text: str,
        model_args: Dict[str, Dict[str, str]],
        long_doc: bool = False,
        coreference: bool = False,
    ):

        super().__init__(text)

        self.model_args = model_args
        self.long_doc = long_doc
        if coreference:
            raise NotImplementedError("coreference is not supported")
        else:
            self.handler = SentenceHandler()
        self.model = Summarizer(
            **self.model_args["initialize"], sentence_handler=self.handler
        )

    def make_summary(self) -> str:
        """
        Only apply when len(text) < 100000
        """
        model = self.model
        if self.long_doc:
            summary = ""
        else:
            try:
                summary = model(self.text, **self.model_args["fit"])
            except ValueError as e:
                summary = ""
                print(e)

        return "".join(summary)
