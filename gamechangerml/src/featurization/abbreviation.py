import json
import re
from collections import defaultdict
import os
import typing as t
from gamechangerml import DATA_PATH

def expand_abbreviations(
    text,
    dic: t.Union[
        t.Dict[str, t.Any], str
    ] = os.path.join(
        DATA_PATH,
        "features", "abbreviations.json"
    ),
):
    """
    Checks document text for abbreviations and returns with expansion found in document

    Args:
        text: text to be searched
        dic: path to dictionary of known abbreviations or an existing dictionary object
    """

    if not isinstance(dic, dict):
        with open(dic, "r") as file:
            dic = json.load(file)

    words = list(dic.keys())
    words = [
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=x)
        for x in words
    ]
    words = [x.strip(" ").lower() for x in words]
    realtext = text
    text = text.strip()
    # gets rid of characters not numbers, letters or the following: _ &'"-
    # prevents issues with punctuation and parenthesis same regex are used throughout
    text = re.sub(pattern=r"""[^0-9a-zA-Z_ &'"-]""", repl=" ", string=text)
    text = re.sub(pattern=r"\s+", repl=r" ", string=text)
    d = {key: None for key in words}
    lower = {
        # characters between ^ and ] are the ones allowed by this regex
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=k)
        .strip(" ")
        .lower(): v
        for k, v in dic.items()
    }
    for key in words:
        if " " in key:
            if key in text:
                for value in lower[key]:
                    val = re.sub(
                        # characters between ^ and ] are the ones allowed by this regex
                        pattern=r"""[^0-9a-zA-Z_ &-'"]""",
                        repl=" ",
                        string=value,
                    )  # removes characters not in the regex
                    val = re.sub(
                        pattern=r"\s+", repl=r" ", string=val
                    )  # eliminates excess spaces
                    if text.lower().find(val.lower()) != -1:
                        d[key.lower()] = val
                        # regex identifies where the abbreviaiton is and prevents finding abbreviations within words
                        realtext = re.sub(
                            rf"(?<!-)\b{re.escape(key)}\b(?!-)",
                            value,
                            realtext,
                        )
                        realtext = re.sub(
                            val + "[\,\.]?\s+" + val,
                            value,
                            realtext,
                            flags=re.I,
                        )
                        break

    docword = text.split(" ")

    for word in docword:
        if word.lower() in words:
            if word[0].isupper() or word in dic.keys():
                for value in lower[word.lower()]:
                    val = re.sub(
                        pattern=r"""[^0-9a-zA-Z_ &-'"]""",
                        repl=" ",
                        string=value,
                    )
                    val = re.sub(pattern=r"\s+", repl=r" ", string=val)
                    if text.lower().find(val.lower()) != -1:
                        d[word.lower()] = val
                        # regex identifies where the abbreviaiton is and prevents finding abbreviations within words
                        realtext = re.sub(
                            rf"(?<!-)\b{re.escape(word)}\b(?!-)",
                            value,
                            realtext,
                        )
                        realtext = re.sub(
                            val + "[\,\.]?\s+" + val,
                            value,
                            realtext,
                            flags=re.I,
                        )
                        break
    d = dict((k, v) for k, v in d.items() if v)
    abb_list = []
    for entry in d:
        abb_dict = {"abbr_s": d[entry], "description_s": entry}
        abb_list.append(abb_dict)

    return realtext, abb_list


def expand_abbreviations_no_context(
    text,
    dic: t.Union[
        t.Dict[str, t.Any], str
    ] = os.path.join(
        DATA_PATH,
        "features", "abbcounts.json"
    ),
):
    """
    Checks a text string for abbreviations and returns it with the most common expansion

    Args:
        text: string to be searched
        dic: path to dictionary of known abbreviations or an existing dictionary object
    """
    expansion = []

    if not isinstance(dic, dict):
        with open(dic, "r") as file:
            dic = json.load(file)

    words = list(dic.keys())
    words = [
        # characters between ^ and ] are the ones allowed by this regex
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=x)
        for x in words
    ]
    words = [x.strip(" ").lower() for x in words]
    text = text.strip()
    # characters between ^ and ] are the ones allowed by this regex
    text = re.sub(pattern=r"""[^0-9a-zA-Z_ &'"-]""", repl=" ", string=text)
    text = re.sub(pattern=r"\s+", repl=r" ", string=text)
    lower = {
        # characters between ^ and ] are the ones allowed by this regex
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=k)
        .strip(" ")
        .lower(): v
        for k, v in dic.items()
    }
    for key in words:
        if " " in key:
            if key in text:
                expansion.append(
                    max(
                        lower[key.lower()], key=lambda k: lower[key.lower()][k]
                    )
                )

    docword = text.split(" ")

    for word in docword:
        if word.lower() in words:
            if word[0].isupper() or word in dic.keys():
                expansion.append(
                    max(
                        lower[word.lower()],
                        key=lambda k: lower[word.lower()][k],
                    )
                )

    return expansion


def add_abbreviations(add, path):
    """
    Add abbreviations and their expansions to the current Dictionary

    Args:
        path: current dictionary location
        add: dictionary of abbreviations with list of definitions
    """
    with open(path, "r") as file:
        dict = json.load(file)

    for k, v in add.items():
        if k in dict:
            dict[k] = list(set(dict[k] + v))
        else:
            dict[k] = v

    with open(path, "w") as file:
        json.dump(dict, file)


def find_abbreviations(
    text,
    dic: t.Union[
        t.Dict[str, t.Any], str
    ] = os.path.join(
        DATA_PATH,
        "features", "abbreviations.json"
    ),
):
    """
    find abbreviations and their expansions in the text and create a dictionary of counts

    Args:
        text: text to search
        dic: path to dictionary of abbreviations with list of definitions or an existing dictionary object
    """
    if not isinstance(dic, dict):
        with open(dic, "r") as file:
            dic = json.load(file)

    words = list(dic.keys())
    # characters between ^ and ] are the ones allowed by this regex
    words = [
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=x)
        for x in words
    ]
    words = [x.strip(" ").lower() for x in words]
    clean = {}
    for key in dic.keys():
        # characters between ^ and ] are the ones allowed by this regex
        k = (
            re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=key)
            .strip(" ")
            .lower()
        )
        if k in clean:
            clean[k].append(key)
        else:
            clean[k] = [key]
    text = text.strip()
    # characters between ^ and ] are the ones allowed by this regex
    text = re.sub(pattern=r"""[^0-9a-zA-Z_ &'"-]""", repl=" ", string=text)
    text = re.sub(pattern=r"\s+", repl=r" ", string=text)
    d = {key: None for key in words}
    # characters between ^ and ] are the ones allowed by this regex
    lower = {
        re.sub(pattern=r"""[^0-9a-zA-Z_ '"-]""", repl="", string=k)
        .strip(" ")
        .lower(): v
        for k, v in dic.items()
    }
    for key in words:
        if " " in key:
            if key in text:
                for item in clean[key.lower()]:
                    for value in dic[item]:
                        # characters between ^ and ] are the ones allowed by this regex
                        val = re.sub(
                            pattern=r"""[^0-9a-zA-Z_ &-'"]""",
                            repl=" ",
                            string=value,
                        )
                        val = re.sub(pattern=r"\s+", repl=r" ", string=val)
                        if text.lower().find(val.lower()) != -1:
                            # regex identifies where the abbreviaiton is and prevents finding abbreviations within words
                            num = len(
                                re.findall(
                                    rf"(?<!-)\b{re.escape(key)}\b(?!-)", text
                                )
                            )
                            d[item] = [value, num]
                            break

    docword = text.split(" ")

    for word in docword:
        if word.lower() in words:
            if word[0].isupper() or word in dic.keys():
                for item in clean[word.lower()]:
                    for value in dic[item]:
                        # characters between ^ and ] are the ones allowed by this regex
                        val = re.sub(
                            pattern=r"""[^0-9a-zA-Z_ &-'"]""",
                            repl=" ",
                            string=value,
                        )
                        val = re.sub(pattern=r"\s+", repl=r" ", string=val)
                        if text.lower().find(val.lower()) != -1:
                            # regex identifies where the abbreviaiton is and prevents finding abbreviations within words
                            num = len(
                                re.findall(
                                    rf"(?<!-)\b{re.escape(word)}\b(?!-)", text
                                )
                            )
                            d[item] = [value, num]
                            break
    d = dict((k, v) for k, v in d.items() if v)
    return d


def count_abbreviations(directory, output):
    """
    Create abbreviation dictionary with the counts for the given directory.

    Args:
        directory: directory of files to be counted
        output: name of file to save counts to
    """
    counts = defaultdict(lambda: defaultdict(int))
    for file in os.listdir(directory):
        with open(directory + "/" + file, "r") as f_in:
            try:
                doc_dict = json.load(f_in)
            except:
                continue
        abbs = find_abbreviations(doc_dict["raw_text"])
        for k, v in abbs.items():
            counts[k][v[0]] += v[1]
    with open(output, "w") as file:
        json.dump(dict(counts), file)
