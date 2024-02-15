#                         MIT LICENSE
#          Copyright (c) 2017-2019 Chris Skiscim
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import logging
import operator
import re

import gamechangerml.src.featurization.keywords.optimized_stop_list as stops
import gamechangerml.src.featurization.keywords.rake_alg as alg
import gamechangerml.src.featurization.keywords.version_ as v

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _clean(string):
    cleaned = re.sub("\\n", " ", string)
    cleaned = re.sub("[\u201c\u201d]+", "", cleaned, re.U)
    cleaned = re.sub('"', "", cleaned)
    cleaned = re.sub("(?:\\d+\\.)+", " ", cleaned)
    cleaned = re.sub("- {2,}", " ", cleaned)
    cleaned = re.sub("\\.\\.{2,}", " ", cleaned)
    cleaned = re.sub("\\(\\w\\)", " ", cleaned, re.I)
    cleaned = re.sub("\\w\\. ?", " ", cleaned, re.I)
    return re.sub("\\s{2,}", " ", cleaned)


def _check_params(ngram, topn):
    if ngram[0] > ngram[1]:
        raise ValueError("illegal value for ngram; got {}".format(ngram))

    if ngram[0] < 1 or ngram[1] < 1:
        raise ValueError("ngrams must all be > 1; got {}".format(ngram))

    if topn <= 1:
        raise ValueError("illegal value for topn; got {}".format(topn))


def _word_length(string):
    return string.count(" ") + 1


class Rake(object):
    __version__ = v.__version__

    def __init__(self, stop_words="smart"):
        """
        Rake object to find key-phrases. Optimized regular expressions for
        splitting on stop words are available for the 'smart', 'nltk' and
        'google' stop word lists.

        :param stop_words: one of 'smart', 'nltk', 'google'
        :type stop_words: str
        :raises: ValueError, OSError
        """
        try:
            self._stop_words_re = stops.load_stops(stop_words, trailing=True)
        except (ValueError, OSError):
            raise

        self.stop_words = stop_words

        self._word_splitter = re.compile("[^a-zA-Z0-9_\\+\\-/]")
        self._sentence_delimiters = re.compile(
            "[.!?,;:\t\\\\\"\\(\\)\\'\u2019\u2013]|\\s\\-\\s"
        )
        self.nb_keywords = 0

        logger.debug(self.__repr__())
        logger.info(
            "{} version {}".format(self.__class__.__name__, self.__version__)
        )

    def __repr__(self):
        return "{}(stop_words={})".format(
            self.__class__.__name__, self.stop_words
        )

    def rank(self, input_text, ngram=(2, 2), topn=5, clean=True):
        """
        Perform the keyword ranking. This returns a list of tuples
        of the form *[(keyword, score),...]*

        :param input_text: text to process
        :type input_text: str
        :param ngram: minimum / maximum length of a keyword
        :type ngram: tuple
        :param topn: how many top-scoring keywords to return
        :type topn: int
        :param clean: performs text cleaning if True
        :type clean: bool
        :return: sorted_keywords
        :raises ValueError
        """

        try:
            _check_params(ngram, topn)
            if not input_text.strip():
                logger.warning(" input text is empty")
                return []
        except ValueError as e:
            raise e

        if clean:
            input_text = _clean(input_text)

        sentence_list = alg.split_sentences(
            input_text, self._sentence_delimiters
        )

        phrase_list = alg.gen_cand_keywords(sentence_list, self._stop_words_re)

        word_scores, phrase_words = alg.calc_word_scores(
            phrase_list, self._word_splitter
        )

        keyword_candidates = alg.gen_cand_keyword_scores(
            phrase_words, word_scores
        )

        sorted_keywords = sorted(
            keyword_candidates.items(),
            key=operator.itemgetter(1),
            reverse=True,
        )
        sorted_keywords = [
            kw.lower()
            for kw, score in sorted_keywords
            if ngram[0] <= _word_length(kw) <= ngram[1]
        ]

        sorted_keywords = list(dict.fromkeys(sorted_keywords))

        num_returned = max(1, len(sorted_keywords[:topn]))
        return sorted_keywords[:num_returned]
