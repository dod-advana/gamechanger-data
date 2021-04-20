import re
import json


class Hieharchy(object):
    """
    Defines the hieharchy structure that
    makes nested dictionary update easier
    """
    def __init__(self):
        self.dictionary = {}

    def update(self, keys, value, old_id = "-"):
        """
        Update the dictionary given a list
        of key and value to be assigned
        """
        dic = self.dictionary
        for key in keys:
            if key not in dic:
                dic[key] = {}
            dic = dic[key]
        dic["text"] = value
        dic["old_id"] = old_id

class DocumentParser(object):
    """
    Class containing the defined regular expressions,
    parsing function, and structure conditions to parse
    the GAMECHANGER documents for Sentence Transformer use
    """
    def __init__(self):
        self.pattern_corpus = [
            [
                "\d+\s?\.\s?[A-Z0-9o()& ,/]{3,}\.(?<! )",   # 1 . PURPOSE
                "(?<![a-z])[a-z]\s?\.\s?(?=[A-Z])",         # a . SUBHEADER
                "\(\s\d\s\)(?= [A-Z])",                     # ( 1 )
                "\(\s[a-z]\s\)(?= [A-Z])"                   # ( a )
            ],
            [
                "[A-Z]{3,}\s\d\s\:\s[A-Zo ]{3,}",   # SECTION: PURPOSE
                "\d\.\d?\s\.\s[A-Zo ]{3,}\s?\.",    # 1.1 . SUBSECTION
                "(?<![a-z])[a-z]\ \.(?=[A-Z])",     # a .
                "\(\s\d\s\)\s?(?=[A-Z])",           # ( 1 )
            ]
        ]

        self.pattern_cond = [
            self._pattern_1_cond,
            self._pattern_2_cond,
        ]

        self.dictionary = Hieharchy()
        self.title = None

        self.mapper = {}

    def _pattern_1_cond(self, data):
        """
        Default pattern
        """
        return True

    def _pattern_2_cond(self, data):
        """
        Any high level keys have "SECTION" at the beginning
        """
        section_keys = [key.startswith("SECTION") for key in data.keys()]
        return any(section_keys)

    def parse(self, fpath):
        """
        Parse the document under GC format (as of April 5 2021) to
        a nested dictionary structured to contain 
        """
        document = self.load_json(fpath)
        self.dictionary = Hieharchy()
        headers = ["COVER PAGE"]
        texts = []

        rev_pcorp = self.pattern_corpus[::-1]
        rev_pcond = self.pattern_cond[::-1]

        if "title" in document:
            self.title = document["title"]

        for pattern_idx, (pattern_set, pattern_cond) in enumerate(zip(rev_pcorp, rev_pcond)):
            self.dictionary = Hieharchy()
            # Merge all potential patterns            
            pattern_str = "(" + "|".join(pattern_set) + ")"

            # Loop through each paragraph
            for paragraph in document["paragraphs"]:
                paragraph_id = paragraph["id"]
                s = paragraph["par_raw_text_t"]
                # Get all matches with the pattern set
                matches = re.findall(pattern_str, s, re.DOTALL)
                # Get matches per level
                match_levels = [re.findall(pattern, s, re.DOTALL) for pattern in pattern_set]

                if len(matches) > 0:
                    # Split the text on the match
                    splits = [i for i in re.split(pattern_str, s) if len(i) > 2]
                    for split in splits:
                        if (split in matches) and (split not in headers):
                            # Update dictionary with header sequence and text
                            self.dictionary.update(headers, ". ".join(texts), paragraph_id)
                            # Identify header level
                            i_level = [i for i, level in enumerate(match_levels) if split in level][0]
                            # Update header sequence
                            if len(headers) < i_level:
                                pad_len = i_level - len(headers)
                                headers += ["-"] * pad_len
                            headers = headers[:i_level]
                            headers.append(split)
                            # Reset text
                            texts = []
                        else:
                            texts.append(split.lstrip().rstrip())
                else:
                    texts.append(s.lstrip().rstrip())

            # Use structure if the condition is met
            if pattern_cond(self.dictionary.dictionary):
                break

    def load_json(self, fpath):
        with open(fpath, "r") as fp:
            data = json.load(fp)
        return data

    def save_dict(self, fpath):
        with open(fpath, "w") as fp:
            json.dump(self.dictionary.dictionary, fp)

if __name__ == "__main__":
    pass