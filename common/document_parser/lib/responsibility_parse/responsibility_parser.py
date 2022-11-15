from common.document_parser.lib import entities
from glob import glob
from tqdm import tqdm
import json
import os
import pandas as pd
import re
from nltk.corpus import stopwords
import string

stopwords = stopwords.words('english')
# gamechanger-data imports
from common.document_parser.cli import get_default_logger
from common.document_parser.lib.document import FieldNames
punctuation_less_period_parentheses = set(string.punctuation).difference({".", "(", ")"})

mid_line_numbering_regex = re.compile("^((?!(Table|Figure|Tab\.|Fig\.)\s1\.\s).)*$", flags=re.VERBOSE)
entity_acronym_regex = re.compile("[^\(]*(\([A-Z\w\s\&\)]{2,10}\))")
start_line_numbering_regex = re.compile("^([a-z]{1,2}\.|"
                                        "\([a-z]{1,2}\)|"
                                        "\(\d{1,2}\)|"
                                        "\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.*|"
                                        "\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,2}\.*)$",
                                        flags=re.VERBOSE)


class ResponsibilityParser:
    def __init__(self):
        self._logger = get_default_logger()
        self.results_df = pd.DataFrame()
        self.error_files = set()
        self.files_missing_responsibility_section = set()
        # this is a character that is (sometimes) used at the end of the responsibility role line and is used as part of
        # the inclusion criteria logic
        self.new_role_find_character = ":"
        self.role_title_words = ["director", "manager", "secretar", "head", "chairman", "chairperson", "commander"]
        self.pre_new_role_find_character_words = ["shall", "will", "must", "responsible for",
                                                  "responsible for the following", "ensure"]
        self.new_role_key_words = ["shall", "establish", "provide", "responsible for"]
        self.break_strings = ["GLOSSARY", "Glossary", "ACRONYMS", "REFERENCES", "SUMMARY OF CHANGE",
                              "Summary of Change",
                              "Abbreviations and Acronyms", "............................"]

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
        # the formats of the numbering are either 1./a. or (1)/(a). Any text with uppercase (such as U.S., or JS.)
        # should not be considered numbering
        text = text.strip()
        space_count = text.count(" ")
        if space_count == 0:
            numbering = text
            text_no_numbering = ""
        elif space_count == 1:
            try:
                numbering, text_no_numbering = text.split(" ", 1)
            except:
                numbering = text
                text_no_numbering = ""
        else:
            numbering, text_no_numbering = text.split(" ", 1)

        if start_line_numbering_regex.search(numbering):
            # items such as "(b), blah bla" are an edge case here (and is connected to the previous line such as "reference (b), bla bla"
            if not numbering.endswith(","):
                return numbering.strip(), text_no_numbering.strip()
            # if there is no spaces/text other than the numbering (such as (b).) usually means that this is a continuation
            # of a previous line
        return "", text

    @staticmethod
    def parse_entities(text):
        """
        Utility function used to extract out entities found within the responsibility line and return those as a
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
                        "responsibilityEntities": ";".join(self.parse_entities(resp_body_text)),
                        "status": "active"
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
                    "responsibilityEntities": "",
                    "status": "active"
                }
            )
        return resp_results_list

    @staticmethod
    def is_role_acronym_defined(text):
        if entity_acronym_regex.search(text):
            return True
        else:
            return False

    def extract_lookahead_text(self, curr_ind, curr_line_text, resp_section):
        try:
            while True:
                lookahead_line = resp_section[curr_ind + 1].replace("\t", "").strip()
                lookahead_numbering, lookahead_text = self.extract_numbering(lookahead_line)
                if not lookahead_numbering:
                    curr_line_text += f" {lookahead_text}"
                    resp_section.pop(curr_ind + 1)
                else:
                    break
        except:
            pass
        return curr_line_text

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
                return self.new_role_find_character.join(
                    split_text[:i + 1]).strip() + ":", self.new_role_find_character.join(
                    split_text[i + 1:]).strip()
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
            self.results_df.to_excel(output_filepath, index=False, engine='openpyxl')
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
            (List of Lists) Containing all the responsibility lines (inner most list) for each role being assigned
            responsibilities in the document

        """
        responsibility_section_list = []
        # remove all of the empty lines in the resp_section and split the text into lines
        resp_section = [line.replace("\t", "").strip() for line in resp_section.split("\n") if line.strip()]
        section_resp_lines = []
        multiple_roles_present = True
        # This metadata is used to find the characteristics of numbering which denotes a new role. I.e., these are special
        # numbering in each doc where another role will begin being assigned responsibilities. e.g.,
        # 2. Director, DIA shall:
        # ...
        # 3. Director, DLA shall:
        # the 2. and 3. numbering is "profiled" using this variable so that the algorithm is able to identify that anytime
        # numbering comes up with 1 digit and 1 period, a new role is being assigned the responsibility
        new_role_start_metadata = {
            "n_periods": 0,
            "n_parenthesis": 0,
            "n_numbers": 0,
            "n_letters": 0,
        }
        current_role_numbering = ""
        next_numbering_is_role = False
        for i, resp_line in enumerate(resp_section):
            if any(term in resp_line for term in self.break_strings):
                break

            ## looks ahead until next numbering occurs to pull all text for a given numbering into the "line_text" var
            resp_line = self.extract_lookahead_text(curr_ind=i, curr_line_text=resp_line,
                                                    resp_section=resp_section)
            numbering, line_text = self.extract_numbering(resp_line)
            if self.new_role_find_character in resp_line:
                resp_line, next_line = self.split_text_with_role_midline(resp_line)
                if next_line:
                    resp_section.insert(i + 1, next_line)
            # Some entities are not within our entities gold standard list, so this is a way of identifying roles that
            # are being mentioned (if they have an acronym defined) and are being assigned responsibilities
            if section_resp_lines == []:
                if any(term in resp_line for term in self.break_strings):
                    break

                entities_found_list = self.parse_entities(resp_line)
                role_acronym_found = self.is_role_acronym_defined(resp_line)
                # capture any cases where the intro text for the responsibitlies section incorporates a role's responsibilites
                # but skip examples such as `and in addition to the responsibilities in Paragraph 2..` (all lowercase)
                if any(word in resp_line for word in ["RESPONSIBILITIES", "Responsibilities"]):
                    # if there is a line with new role numbering in the middle of the sentence and it is not something like
                    # `Table 1.`, a break should be made and the new role should be added as a new line in resp_section
                    if " 1. " in resp_line and mid_line_numbering_regex.search(resp_line):
                        resp_section.insert(i + 1, " 1. " + resp_line.split(" 1. ", 1)[1])
                        # some sections have `1. Overview to start the responsibilties section, and these need to be bypassed
                        if "1. Overview" not in resp_line:
                            next_numbering_is_role = True
                    elif " a. " in resp_line:
                        resp_section.insert(i + 1, " a. " + resp_line.split(" a. ", 1)[1])
                        next_numbering_is_role = True
                    elif entities_found_list:
                        section_resp_lines.append(resp_line)
                        new_role_start_metadata = {
                            "n_periods": numbering.count("."),
                            "n_parenthesis": numbering.count(")"),
                            "n_numbers": sum(c.isdigit() for c in numbering),
                            "n_letters": sum(c.isalpha() for c in numbering),
                        }
                    continue
                if numbering:
                    # for lines such as 5. RESPONSIBILITIES AND FUNCTIONS.  The Director, PFPA: - there is only one role being
                    # assigned responsibilities in this document, and we need to capture out the `The Director, PFPA:` part

                    # look for lines like `... shall:` or `... is responsible for:`
                    if next_numbering_is_role or \
                            any(resp_line.endswith(pre_new_role_find_character_word + self.new_role_find_character) for
                                pre_new_role_find_character_word in self.pre_new_role_find_character_words) or \
                            (
                                    entities_found_list or role_acronym_found or any(
                                word in resp_line for word in self.new_role_key_words)
                            ):
                        new_role_start_metadata = {
                            "n_periods": numbering.count("."),
                            "n_parenthesis": numbering.count(")"),
                            "n_numbers": sum(c.isdigit() for c in numbering),
                            "n_letters": sum(c.isalpha() for c in numbering),
                        }
                        section_resp_lines.append(resp_line)
                        # if there are any entities found or if any new role keywords are present in the line
                else:
                    # determine whether there is a free text line/paragraph at the beginning of the responsibility section to add
                    # It is infrequently the case that the first role looks something like:
                    # RESPONSIBILITIES 1. DIRECTOR, DIA. In this case the numbering is not captured out using the numbering
                    # logic, and this is edge case logic to find these instances
                    if " 1. " in resp_line:
                        numbering = "1."
                        section_resp_lines.append(f"{numbering}{resp_line.split(numbering)[-1]}")
                        new_role_start_metadata = {
                            "n_periods": 1,
                            "n_parenthesis": 0,
                            "n_numbers": 1,
                            "n_letters": 0,
                        }

            # determine whether the current line (w/o any numbering/punctuation) is a continuation of an existing line
            # or a new line that should be captured as a new line
            else:
                if numbering:
                    # in some cases, there are junk sections before (inside the overall responsibility section) which have
                    # matched the logic above and acted like responsibilities, however we want to clear out the cache and start
                    # assigning responsibilities from the current line
                    if line_text.upper().strip() == "RESPONSIBILITIES":
                        section_resp_lines = []
                        new_role_start_metadata = {
                            "n_periods": 0,
                            "n_parenthesis": 0,
                            "n_numbers": 0,
                            "n_letters": 0,
                        }
                        next_numbering_is_role = True
                        continue

                    # example of this edge case (the l. acts as a new numbering)
                    # (9) Conduct inquiries, inspections, and investigations as directed by
                    # the DJS or CJCS using the procedures and guidance IAW references a through
                    # l.
                    # (10) Provide assistance to the CCMD IG offices as requested.
                    #
                    # if there is no "text" for the line, and the next line has numbering, this is a continuation of the last
                    # line
                    if not line_text.strip():
                        try:
                            next_line_numbering, next_line_text = self.extract_numbering(resp_section[i + 1])
                            if next_line_numbering:
                                section_resp_lines[-1] += f" {resp_line}"
                                continue
                        except:
                            section_resp_lines[-1] += f" {resp_line}"
                            continue

                    # A new role is being assigned a set of responsibilities, so capture this as a new grouping
                    if new_role_start_metadata["n_periods"] == numbering.count(".") and \
                            new_role_start_metadata["n_parenthesis"] == numbering.count(")") and \
                            new_role_start_metadata["n_numbers"] in [sum(c.isdigit() for c in numbering) - 1,
                                                                     sum(c.isdigit() for c in numbering)] and \
                            new_role_start_metadata["n_letters"] <= sum(c.isalpha() for c in numbering):

                        # if multiple different roles are not present, but we have a numbering that is similar to the
                        # numbering that assigned the role, this means there is typically an issue with the section parser
                        # and we should break (rather than continue adding "roles" that are not actually roles)
                        if not multiple_roles_present:
                            break

                        # If section_resp_lines already has information in it (i.e., a prior role has responsibility lines,
                        # then append this to responsibility_section_list and start fresh with a new section_resp_lines list.
                        if section_resp_lines:
                            responsibility_section_list.append(section_resp_lines)
                            section_resp_lines = []
                    section_resp_lines.append(resp_line)
                else:
                    # if the previous line ended in punctuation, then add this text as a new line
                    if section_resp_lines[-1].strip().endswith(self.new_role_find_character):
                        section_resp_lines.append(resp_line)
                    # no punctuation at end of previous line, so this line is a continuation of the previous line of text
                    else:
                        section_resp_lines[-1] += f" {resp_line}"

        if section_resp_lines:
            responsibility_section_list.append(section_resp_lines)

        return responsibility_section_list

    def extract_responsibilities_from_json(self, json_filepath):
        """
        Takes a JSON dict and parses the responsibility section(s)
        Args:
            json_filepath: (str) GC JSON filepath that will have responsibility sections parsed from it

        Returns:
            (List of Dicts) Containing all the responsibility records (each dict is a unique record) for the JSON file
            that has been parsed. e.g.:
            file_responsibility_sections = [
                                            {'filename': 'DoDI 5000.94.pdf',
                                            'documentTitle': 'Use of Robotic Systems for Manufacturing and Sustainment in the DoD',
                                            'organizationPersonnelNumbering': '2.1.',
                                            'organizationPersonnelText': ' UNDER SECRETARY OF DEFENSE FOR ACQUISITION AND SUSTAINMENT (USD(A&S)). The USD(A&S):',
                                            'organizationPersonnelEntities': 'USD(A&S);Under Secretary of Defense for Acquisition and Sustainment',
                                            'responsibilityNumbering': 'a.',
                                            'responsibilityText': ' Establishes, maintains, and monitors the implementation of policy for the use of robotic systems for manufacturing and sustainment in the DoD.',
                                            'responsibilityEntities': 'DoD'},
                                            ...
                                            ]

        """
        json_file_name = json_filepath.split("/")[-1]
        try:
            with open(json_filepath, "r") as f:
                json_dict = json.load(f)
            title = json_dict.get(FieldNames.TITLE)
            filename = json_dict.get(FieldNames.FILENAME)
            resp_sections = json_dict.get(FieldNames.SECTIONS, {}).get(FieldNames.RESPONSIBILITIES_SECTION, [])
            if not resp_sections:
                self._logger.debug(
                    f"File: {json_file_name} does not have necessary responsibilities_section field, skipping file from results")
                self.files_missing_responsibility_section.add(json_file_name)
        except Exception as e:
            self._logger.error(
                f"{json_file_name} is missing a necessary field for responsibility parsing and threw Exception: {e}, skipping file from results")
            self.error_files.add(json_file_name)
            return []

        file_responsibility_sections = []
        for resp_section in resp_sections:
            responsibility_section_list = self.parse_responsibility_section(resp_section)
            file_responsibility_sections.extend(
                [resp_line for responsibility_section in responsibility_section_list for resp_line in
                 self.format_responsibility_results(responsibility_section, filename, title)])
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
        self._logger.info(f"Attempting to parse files_input_directory")
        parse_files = glob(os.path.join(files_input_directory, "*.json"))
        self._logger.info(f"{len(parse_files)} total files found in directory")
        all_results_list = []

        for parse_file in tqdm(parse_files):
            all_results_list.extend(self.extract_responsibilities_from_json(parse_file))
        self.results_df = pd.concat([self.results_df, pd.DataFrame(all_results_list)])

        if excel_save_filepath:
            self._logger.info(f"Saving responsibility data to filepath: {excel_save_filepath}")
            self.save_results_to_excel(excel_save_filepath)

        self._logger.info(f"{len(parse_files)} total files processed")
        self._logger.info(f"{len(self.error_files)} total files errored out/skipped")
        self._logger.info(
            f"{len(self.files_missing_responsibility_section)} total files missing responsibility_section")
