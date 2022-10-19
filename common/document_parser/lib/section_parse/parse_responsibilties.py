from common.document_parser.lib.section_parse import add_sections
import re
from string import punctuation
from common.document_parser.lib import entities
## need "roman"
from glob import glob
from tqdm import tqdm
import json
from common.document_parser.cli import get_default_logger
import pandas as pd
import os


class ResponsibilityParser:
    def __init__(self):
        self._logger = get_default_logger()
        # this is a character that is (sometimes) used at the end of the responsibility role line and is used as part of
        # the inclusion criteria logic
        self.new_role_find_character = ":"
        self.new_role_key_words = ["shall", "establish", "provide"]
        self.break_words = ["GLOSSARY", "Glossary", "ACRONYMS", "REFERENCES", "SUMMARY OF CHANGE"]
        self.results_df = None

    @staticmethod
    def _extract_numbering(text):
        # the formats of the numbering are either 1./a. or (1)/(a)
        if "." in text[:3] or set(["(", ")"]).difference(text[:4]) == set():
            try:
                numbering, text_no_numbering = text.split(" ", 1)
                # items such as "(b), blah bla" are an edge case here (and is connected to the previous line such as "reference (b), bla bla"
                if not numbering.endswith(","):
                    return numbering, text_no_numbering
            # if there is no spaces/text other than the numbering (such as (b).) usually means that this is a continuation
            # of a previous line
            except:
                pass
        return "", text

    @staticmethod
    def _parse_entities(text):
        text = entities.replace_nonalpha_chars(text, "")
        ent_info_list = [
            (
                e[1],
                e[2],
                entities.ENTITIES_LOOKUP_DICT[e[0]]["raw_ent"],
                entities.ENTITIES_LOOKUP_DICT[e[0]]["ent_type"],
            )
            for e in entities.PROCESSOR.extract_keywords(text, span_info=True)
        ]
        return list(set([ent_info[2] for ent_info in entities.remove_overlapping_ents(ent_info_list)]))

    def parse_responsibility_list(self, resp_list, file_name, title):
        resp_results_list = []
        resp_intro_numbering, resp_intro_text = self._extract_numbering(resp_list[0])
        resp_intro_entities = self._parse_entities(resp_intro_text)

        if len(resp_list) > 1:
            for resp_body_text in resp_list[1:]:
                resp_body_numbering, resp_body_text = self._extract_numbering(resp_body_text)
                resp_results_list.append(
                    {
                        "filename": file_name,
                        "documentTitle": title,
                        "organizationPersonnelNumbering": resp_intro_numbering,
                        "organizationPersonnelText": resp_intro_text,
                        "organizationPersonnelEntities": ",".join(resp_intro_entities),
                        "responsibilityNumbering": resp_body_numbering,
                        "responsibilityText": resp_body_text,
                        "responsibilityEntities": ",".join(self._parse_entities(resp_body_text))
                    }
                )
        else:
            resp_results_list.append(
                {
                    "filename": file_name,
                    "documentTitle": title,
                    "organizationPersonnelNumbering": resp_intro_numbering,
                    "organizationPersonnelText": resp_intro_text,
                    "organizationPersonnelEntities": ",".join(resp_intro_entities),
                    "responsibilityNumbering": "",
                    "responsibilityText": "",
                    "responsibilityEntities": ""
                }
            )
        return resp_results_list

    def parse_line_with_numbering(self, text):
        split_text = text.split(self.new_role_find_character)
        # won't hit loop if there is not a self.new_role_find_character found
        for i in range(len(split_text) - 1):
            numbering, text_no_numbering = self._extract_numbering(split_text[i + 1].strip())
            if numbering:
                return self.new_role_find_character.join(split_text[:i + 1]), self.new_role_find_character.join(
                    split_text[i + 1:])
        return text, ""

    def save_results_to_excel(self, output_filepath):
        try:
            self.results_df.to_excel(output_filepath, index=False)
        except Exception as e:
            self._logger.error(f"Error saving results dataframe to Excel with exception: {e}")

    def save_results_to_excel(self, output_filepath):
        try:
            self.results_df.to_excel(output_filepath, index=False)
        except Exception as e:
            self._logger.error(f"Error saving results dataframe to Excel with exception: {e}")

    def main(self, files_input_directory, excel_save_filepath=None):
        parse_files = glob(os.path.join(files_input_directory,"*.json"))
        doc_results = {}
        for parse_file in tqdm(parse_files):
            dod_json = json.load(open(parse_file, "r"))
            title = dod_json["title"]
            filename = dod_json["filename"]

            try:
                resp_sections = dod_json['sections']["responsibilities_section"]
                if not resp_sections:
                    self._logger.info(
                        f"File: {filename} has no nested responsibilities_section, skipping file from results")
            except Exception as e:
                self._logger.error(f"{filename} threw error with Exception: {e}, skipping file from results")
                continue

            role_resp_sections = []
            for resp_section in resp_sections:
                section_resp_lines = []
                multiple_roles_present = True
                new_role_start_metadata = {
                    "n_periods": 0,
                    "n_parenthesis": 0,
                    "n_numbers": 0,
                    "n_letters": 0,
                }

                for i, resp_line in enumerate(resp_section):
                    if any(term in resp_line for term in self.break_words):
                        break
                    if "\n" in resp_line:
                        resp_line, next_line = resp_line.split("\n", 1)
                        resp_section.insert(i + 1, next_line)
                    if self.new_role_find_character in resp_line:
                        resp_line, next_line = self.parse_line_with_numbering(resp_line)
                        if next_line:
                            resp_section.insert(i + 1, next_line)

                    resp_line = resp_line.replace("\t", "").strip()
                    numbering, line_text = self._extract_numbering(resp_line)
                    entities_found_list = self._parse_entities(line_text)
                    if numbering:
                        ### sometimes the next line is an extension of the previous line that needs to be appended to previouse.g.
                        # ... section 139 of Reference
                        # (b).
                        # for lines such as 5. RESPONSIBILITIES AND FUNCTIONS.  The Director, PFPA: - there is only one role being
                        # assigned responsibilties in this document, and we need to capture out the `The Director, PFPA:` part
                        if section_resp_lines == []:
                            if resp_line.endswith(self.new_role_find_character) and entities_found_list:

                                if "RESPONSIBILITIES" in resp_line:
                                    multiple_roles_present = False
                                    section_resp_lines.append(line_text.strip())
                                else:
                                    new_role_start_metadata = {
                                        "n_periods": numbering.count("."),
                                        "n_parenthesis": numbering.count(")"),
                                        "n_numbers": sum(c.isdigit() for c in numbering),
                                        "n_letters": sum(c.isalpha() for c in numbering),
                                    }
                                    section_resp_lines.append(resp_line)
                                    # if there are any entities found or if any new role keywords are present in the line
                            elif any(word in resp_line for word in self.new_role_key_words) or entities_found_list:
                                new_role_start_metadata = {
                                    "n_periods": numbering.count("."),
                                    "n_parenthesis": numbering.count(")"),
                                    "n_numbers": sum(c.isdigit() for c in numbering),
                                    "n_letters": sum(c.isalpha() for c in numbering),
                                }
                                section_resp_lines.append(resp_line)

                        else:
                            ## A new role is being assigned a set of responsibilities, so capture this as a new grouping
                            if multiple_roles_present and \
                                    new_role_start_metadata["n_periods"] == numbering.count(".") and \
                                    new_role_start_metadata["n_parenthesis"] == numbering.count(")") and \
                                    new_role_start_metadata["n_numbers"] <= sum(c.isdigit() for c in numbering) and \
                                    new_role_start_metadata["n_letters"] <= sum(
                                    c.isalpha() for c in numbering):  # and \
                                # resp_line.endswith(self.new_role_find_character):
                                if section_resp_lines:
                                    role_resp_sections.append(
                                        self.parse_responsibility_list(section_resp_lines, filename, title))
                                    section_resp_lines = []
                            section_resp_lines.append(resp_line)

                    ## determine whether the current line (w/o any numbering/punctuation) is a continuation of an existing line
                    # or a new line that should be captured as a new line
                    elif section_resp_lines != []:
                        ## if the previous line ended in punctuation, then add this text as a new line
                        if section_resp_lines[-1].strip().endswith(self.new_role_find_character):
                            section_resp_lines.append(resp_line)
                        # no punctuation at end of previous line, so this line is a continuation of the previous line of text
                        else:
                            section_resp_lines[-1] += f" {resp_line}"
                    ## determine whether there is a free text line/paragraph at the beginning of the responsibility section to add
                    else:
                        if " 1. " in resp_line:
                            section_resp_lines.append(f"1.{resp_line.split('1.')[-1]}")
                            new_role_start_metadata = {
                                "n_periods": 1,
                                "n_parenthesis": 0,
                                "n_numbers": 1,
                                "n_letters": 0,
                            }
                        # if not any(word in resp_line.lower() for word in ["section","enclosure","responsibilities"]):
                        elif (entities_found_list and resp_line.strip().endswith(self.new_role_find_character)) or any(
                                word in resp_line for word in self.new_role_key_words):
                            section_resp_lines.append(resp_line)
                if section_resp_lines:
                    role_resp_sections.append(self.parse_responsibility_list(section_resp_lines, filename, title))
            doc_results[filename] = role_resp_sections
        self.results_df = pd.DataFrame(
            [record for file_records in list(doc_results.values()) for record_list in file_records for record in
             record_list])
        if excel_save_filepath:
            self.save_results_to_excel(excel_save_filepath)
