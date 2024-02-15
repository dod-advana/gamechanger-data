#                         MIT LICENSE
#          Copyright (c) 2013-2019 Chris Skiscim
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

import functools
import logging
from collections import defaultdict

import gamechangerml.src.featurization.keywords.optimized_stop_list as stops

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def add(x, y):
    return x + y


def is_number(s):
    """
    Test if a string is an int or float.

    :param s: input string (word)
    :type s: str
    :return: bool
    """
    try:
        float(s) if "." in s else int(s)
        return True
    except ValueError:
        return False


def separate_words(text, splitter):
    """
    Tokenizes the text into words for scoring, if the token is not a number.

    :param text: given text
    :type text: str
    :param splitter: regular expression used for tokenizing
    :type splitter: _sre.SRE_Pattern
    :return: list
    """
    return [
        w.strip()
        for w in splitter.split(text)
        if w.strip() and not is_number(w)
    ]


def split_sentences(text, sentence_delimiters):
    """
    Tokenizes text into a list of sentences.

    :param text: given text
    :type text: str
    :param sentence_delimiters: regular expression for sentence tokenizing
    :type sentence_delimiters: _sre.SRE_Pattern
    :return: list
    """
    return sentence_delimiters.split(text)


def gen_cand_keywords(sentence_list, stopword_re):
    """
    Splits the sentences on stopwords to produce candidate keywords.

    :param sentence_list: sentences to process
    :param stopword_re: optimized stopword regular expression
    :type stopword_re: _sre.SRE_Pattern
    :return: list
    """
    phrase_list = list()
    for s in sentence_list:
        p = stops.split_on_stopwords(s, stopword_re)
        phrase_list.extend(p)
    return phrase_list


def calc_word_scores(phrase_list, splitter):
    """
    Calculate phrase scores using the RAKE method.

    :param phrase_list: phrases to process
    :type phrase_list: list
    :param splitter: compiled word tokenizer regular expression
    :type splitter: _sre.SRE_Pattern
    :return: word_score, phrase_words
    """
    word_frequency = defaultdict(int)
    word_degree = defaultdict(int)
    phrase_words = list()

    for phrase in phrase_list:
        word_list = [
            w.strip().lower()
            for w in splitter.split(phrase)
            if w.strip() and not is_number(w)
        ]
        word_list_degree = len(word_list) - 1
        phrase_words.append((phrase, word_list))

        for word in word_list:
            word_frequency[word] += 1
            word_degree[word] += word_list_degree  # orig.

    for wf in word_frequency:
        word_degree[wf] = word_degree[wf] + word_frequency[wf]

    word_score = {
        w: word_degree[w] / word_frequency[w] for w in word_frequency
    }
    return word_score, phrase_words


def gen_cand_keyword_scores(phrase_words, word_score):
    """
    Computes the score for the input phrases.

    :param phrase_words: phrases to score
    :type phrase_words: list
    :param word_score: calculated word scores
    :type word_score: list
    :return: dict *{phrase: score, ...}*
    """
    keyword_candidates = defaultdict(int)
    for phrase, word_list in phrase_words:
        if not word_list:
            continue
        candidate_score = functools.reduce(
            add, [word_score[word] for word in word_list]
        )
        keyword_candidates[phrase] = candidate_score
    return keyword_candidates
