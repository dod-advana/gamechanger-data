import re
import os
import pandas as pd

import nltk
from gamechangerml import NLTK_DATA_PATH, DATA_PATH

if not NLTK_DATA_PATH in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_PATH)

import ssl


# TODO: move env dependency setup to the config scripts & requests
# TODO: download dir should be hardcoded to avoid deployment issues
def download_nltk_data():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download("punkt")


# TODO: env dependency setup should be in config scripts
if os.environ.get("DOWNLOAD_NLTK_DATA") == "yes":
    download_nltk_data()


def get_responsibilities(text, agencies=None):
    check = True
    if not agencies:
        df = pd.read_csv(os.path.join(DATA_PATH, "features", "agencies.csv"))
        agencies = list(df["Agency_Name"])
        agencies = [x.lower() for x in agencies]

    if "RESPONSIBILITIES" in text:
        new = text.split("RESPONSIBILITIES", 1)[1].lstrip()
        prev = text.split("RESPONSIBILITIES", 1)[0].strip().split(" ")[-2:]
        while new[0] == ".":
            if "RESPONSIBILITIES" in new:
                prev = (
                    new.split("RESPONSIBILITIES", 1)[0].strip().split(" ")[-2:]
                )
                new = new.split("RESPONSIBILITIES", 1)[1].lstrip()
            else:
                check = False
                break
        if new.split(" ")[0] == "SECTION":
            if "RESPONSIBILITIES" in new:
                prev = (
                    new.split("RESPONSIBILITIES", 1)[0].strip().split(" ")[-2:]
                )
                new = new.split("RESPONSIBILITIES", 1)[1].lstrip()
        if check:
            prev = " ".join(prev)
            prev = re.sub("\n", " ", prev)
            prev = re.sub(pattern=r"\s+", repl=r" ", string=prev)
            first = prev.split(" ")[-1]
            if re.match("([0-9].)+", first) is not None:
                it = re.sub(
                    "(\d+)(?!.*\d)", lambda x: str(int(x.group(0)) + 1), first
                )
            elif any(i.isdigit() for i in first):
                it = prev.split(" ")[-2]
            else:
                return {}
            parsed = parse(new.split(it)[0])
            if parsed:
                extracted = extract(parsed, agencies)
                return extracted
            else:
                return {}


def parse(ptext):
    temp = []
    it = ptext.split(" ")[0]
    text = ptext
    if "1." in it:
        text = text.split(" ", 1)[1]
        while it in ptext:
            it = re.sub(
                "(\d+)(?!.*\d)", lambda x: str(int(x.group(0)) + 1), it
            )
            temp.append(text.split(it, 1)[0])
            if len(text.split(it, 1)) > 1:
                text = text.split(it, 1)[1]
            else:
                break
        return temp
    elif "a." in it:
        text = text.split(" ", 1)[1]
        char = ord("a")
        while it in ptext:
            char += 1
            it = "\n" + chr(char) + "."
            temp.append(text.split(it, 1)[0])
            if len(text.split(it, 1)) > 1:
                text = text.split(it, 1)[1]
            else:
                break
        return temp
    else:
        return False


def extract(parsed, agencies):

    extracted = {}
    for k in range(len(parsed)):
        agency = None
        responsibilities = []

        new = nltk.tokenize.sent_tokenize(re.sub("\n", " ", parsed[k]))
        if not new:
            continue

        entity = new[0].split("shall")[0]
        if any(sub in entity.lower() for sub in agencies):
            for a in agencies:
                if a in entity.lower():
                    agency = a
        for i in range(1, len(new)):
            if " " in new[i]:
                responsibilities.append(new[i])
        extracted[entity] = {
            "Agency": agency,
            "Responsibilities": responsibilities,
        }
    return extracted
