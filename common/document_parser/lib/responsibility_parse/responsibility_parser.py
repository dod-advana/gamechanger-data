from common.document_parser.lib.section_parse import add_sections
from common.document_parser.lib import entities
from glob import glob
from tqdm import tqdm
import json
from common.document_parser.cli import get_default_logger
import pandas as pd
import os
import pandas as pd


class ResponsibilityParser:
    def __init__(self):
        self._logger = get_default_logger()
        # this is a character that is (sometimes) used at the end of the responsibility role line and is used as part of
        # the inclusion criteria logic
        self.new_role_find_character = ":"
        self.new_role_key_words = ["shall", "establish", "provide"]
        self.break_words = ["GLOSSARY", "Glossary", "ACRONYMS", "REFERENCES", "SUMMARY OF CHANGE"]
        self.results_df = None
        self.error_files = set()
        self.files_missing_responsibility_section = set()

    @staticmethod
    def extract_numbering(text):
        """
        Utility function used to extract the numbering component of a line of text and separate it out from the
        body of the line of text
        Args:
            text: (str) A line of the responsibility section

        Returns:
            (tuple) (str numbering, str text_no_numbering) with the element at index 0 being the numbering portion of
            the text, and the element at index 1 being the remainder of the text without the numbering portion. In cases
            where numbering is missing from the text returns an empty string for the numbering portion

        """
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
    def parse_entities(text):
        """
        Utility function used to extract extract out entities found within the responsibility line and return those as a
        list.
        Args:
            text: (str) Text that the entity extraction should be applied to

        Returns:
            (list of strings) List of deduplicated entities identified in the text. If no entities are found, returns
            an empty list

        """
        text = entities.replace_nonalpha_chars(text, "")
        ent_info_list = [
            (e[1], e[2], entities.ENTITIES_LOOKUP_DICT[e[0]]["raw_ent"],
            entities.ENTITIES_LOOKUP_DICT[e[0]]["ent_type"])
            for e in entities.PROCESSOR.extract_keywords(text, span_info=True)
        ]
        unique_entities_list = list(set([ent_info[2] for ent_info in entities.remove_overlapping_ents(ent_info_list)]))
        unique_entities_list.sort()
        return unique_entities_list

    def format_responsibility_results(self, resp_list, file_name, title):
        """
        Utility function used to format a block of responsibility results into a list of dictionaries which is later used
        to create a dataframe/spreadsheet of the results
        Args:
            resp_list: (List of strings) A block/list of responsibility results where the element at index 0 is the intro
                       text (e.g., "3. The Director, DIA shalL:") and each remaining element in the list are
                       responsibilities associated with that role
            file_name: (str) The filename (PDF) of the results being parsed
            title: (str) The title of the document for the results being parsed

        Returns:
            (List of dicts) List of formatted/standardized results (dicts) where the keys are the columns that will be
            in the final dataframe/xlsx file, and the values are the values for a record/row in the dataframe.

        """
        resp_results_list = []
        resp_intro_numbering, resp_intro_text = self.extract_numbering(resp_list[0])
        resp_intro_entities = self.parse_entities(resp_intro_text)

        if len(resp_list) > 1:
            for resp_body_text in resp_list[1:]:
                resp_body_numbering, resp_body_text = self.extract_numbering(resp_body_text)
                resp_results_list.append(
                    {
                        "filename": file_name,
                        "documentTitle": title,
                        "organizationPersonnelNumbering": resp_intro_numbering,
                        "organizationPersonnelText": resp_intro_text,
                        "organizationPersonnelEntities": ";".join(resp_intro_entities),
                        "responsibilityNumbering": resp_body_numbering,
                        "responsibilityText": resp_body_text,
                        "responsibilityEntities": ";".join(self.parse_entities(resp_body_text))
                    }
                )
        else:
            resp_results_list.append(
                {
                    "filename": file_name,
                    "documentTitle": title,
                    "organizationPersonnelNumbering": resp_intro_numbering,
                    "organizationPersonnelText": resp_intro_text,
                    "organizationPersonnelEntities": ";".join(resp_intro_entities),
                    "responsibilityNumbering": "",
                    "responsibilityText": "",
                    "responsibilityEntities": ""
                }
            )
        return resp_results_list

    def split_text_with_role_midline(self, text):
        """
        This function is a utility function used to identify cases where responsibilities begin mid-line, such as if
        "The Director, DIA shall: a. Do X.", Split on the new_role_find_character and try to identify if numbering is present
        subsequent to the new_role_find_character.

        Args:
            text: (str) Text to identify/split if there is numbering in the middle of the text

        Returns:
            (tuple) (str, str) with the element at index 0 being the portion of the text before numbering (see function description)
             and the element at index 1 being the remainder of the text with the numbering portion. In cases
            where there is no mid-text numbering present, the element in index 0 of the tuple is the full text that was
            passed in and the second element is an empty string
        """
        split_text = text.split(self.new_role_find_character)
        # won't hit loop if there is not a self.new_role_find_character found
        for i in range(len(split_text) - 1):
            numbering, text_no_numbering = self.extract_numbering(split_text[i + 1].strip())
            if numbering:
                return self.new_role_find_character.join(split_text[:i + 1])+":", self.new_role_find_character.join(
                    split_text[i + 1:])
        return text, ""

    def save_results_to_excel(self, output_filepath):
        """
        Utility function for saving the results dataframe to excel
        Args:
            output_filepath: (str) Filepath (including filename) of the file where the results should be stored

        Returns:
            (void)

        """
        try:
            self.results_df.to_excel(output_filepath, index=False)
        except Exception as e:
            self._logger.error(f"Error saving results dataframe to Excel with exception: {e}")

    def parse_responsibility_section(self, resp_section):
        """
        For each document's responsibility section(s), this function is the main logic and wrapper around other functions
        which performs the parsing of the responsibility section of text

        Args:
            resp_section: (str) Containing the responsibility lines as newline (\n) delimited chunks within a single block
            of text

        Returns:
            (List of Lists) Containing all of the responsibility lines (inner most list) for each role being assigned
            responsibilities in the document

        """
        responsibility_section_list = []
        resp_section = resp_section.split("\n")
        section_resp_lines = []
        multiple_roles_present = True
        ## This metadata is used to find the characteristics of numbering which denotes a new role. I.e., these are special
        ## numbering in each doc where another role will begin being assigned responsibilities. e.g.,
        ## 2. Director, DIA shall:
        ## ...
        ## 3. Director, DLA shall:
        ## the 2. and 3. numbering is "profiled" using this variable so that the algorithm is able to identify that anytime
        ## numbering comes up with 1 digit and 1 period, a new role is being assigned the responsibility
        new_role_start_metadata = {
            "n_periods": 0,
            "n_parenthesis": 0,
            "n_numbers": 0,
            "n_letters": 0,
        }

        for i, resp_line in enumerate(resp_section):
            if any(term in resp_line for term in self.break_words):
                break

            if self.new_role_find_character in resp_line:
                resp_line, next_line = self.split_text_with_role_midline(resp_line)
                if next_line:
                    resp_section.insert(i + 1, next_line)

            resp_line = resp_line.replace("\t", "").strip()
            numbering, line_text = self.extract_numbering(resp_line)
            entities_found_list = self.parse_entities(line_text)
            if numbering:
                ### sometimes the next line is an extension of the previous line that needs to be appended to previous e.g.
                # ... section 139 of Reference
                # (b).
                # for lines such as 5. RESPONSIBILITIES AND FUNCTIONS.  The Director, PFPA: - there is only one role being
                # assigned responsibilities in this document, and we need to capture out the `The Director, PFPA:` part
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
                            responsibility_section_list.append(section_resp_lines)
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

                elif (entities_found_list and resp_line.strip().endswith(self.new_role_find_character)) or any(
                        word in resp_line for word in self.new_role_key_words):
                    section_resp_lines.append(resp_line)
        if section_resp_lines:
            responsibility_section_list.append(section_resp_lines)

        return responsibility_section_list

    def extract_responsibilities_from_json(self, json_filepath):
        """
        Takes a JSON dict and parses the responsibility section(s)
        Args:
            json_filepath: (dict) GC JSON filepath that will have responsibility sections parsed from it

        Returns:

        """
        json_file_name = json_filepath.split("/")[-1]
        try:
            json_dict = json.load(open(json_filepath, "r"))
            title = json_dict.get("title")
            filename = json_dict.get("filename")
            resp_sections = json_dict.get('sections',{}).get("responsibilities_section",[])
            if not resp_sections:
                self._logger.debug(
                    f"File: {json_file_name} does not have necessary responsibilities_section field, skipping file from results")
                self.files_missing_responsibility_section.add(json_file_name)
        except Exception as e:
            self._logger.error(f"{json_file_name} is missing a necessary field for responsibility parsing and threw Exception: {e}, skipping file from results")
            self.error_files.add(json_file_name)
            return []

        file_responsibility_sections = []
        for resp_section in resp_sections:
            responsibility_section_list = self.parse_responsibility_section(resp_section)
            file_responsibility_sections.extend([resp_line for responsibility_section in responsibility_section_list for resp_line in self.format_responsibility_results(responsibility_section, filename, title)])
        return file_responsibility_sections

    def main(self, files_input_directory, excel_save_filepath=None):
        """
        Main class function that is a wrapper around the responsibility parsing logic. Based on the input directory passed in
        identifies all json's in that directory and iterates over them, extracting responsibilities, and writes the results
        out to excel_save_filepath if supplied
        Args:
            files_input_directory: (str) Directory to the GC JSON's that have had section parsing applied
            excel_save_filepath: (str) File path to the file where the responsibility results should be stored

        Returns:

        """
        parse_files = glob(os.path.join(files_input_directory,"*.json"))
        all_results_list = []
        for parse_file in tqdm(parse_files):
            all_results_list.extend(self.extract_responsibilities_from_json(parse_file))
        self.results_df = pd.DataFrame(all_results_list)

        if excel_save_filepath:
            self._logger.info(f"Saving responsibility data to filepath: {excel_save_filepath}")
            self.save_results_to_excel(excel_save_filepath)

        self._logger.info(f"{len(parse_files)} total files processed")
        self._logger.info(f"{len(self.error_files)} total files errored out/skipped")
        self._logger.info(f"{len(self.files_missing_responsibility_section)} total files missing responsibility_section")
