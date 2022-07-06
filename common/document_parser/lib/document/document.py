from syntok.segmenter import process

from gamechangerml.src.utilities.text_utils import utf8_pass

from .field_names import FieldNames
from .utils.dod_text import normalize_dod


class Document:
    def __init__(self, doc_dict):
        """
        Args:
            doc_dict (dict): Dictionary representation of a document.
        """
        self.doc_dict = doc_dict

    def get_field(self, field_name):
        """Return the value of a field from the object's doc_dict.

        Args:
            field_name (str): Field name to get the value of.

        Returns:
            unknown: The value of the field if it exists. Otherwise, None
        """
        return self.doc_dict.get(field_name)

    def get_page(self, page_num):
        """Get a page from the document.

        Args:
            page_num (int): Page number

        Returns:
            dict or None: Dictionary representation of the page if it exists. 
                Otherwise, None.
        """
        pages = self.get_field(FieldNames.PAGES)
        if pages is not None and page_num < len(pages):
            return pages[page_num]
        else:
            return None

    def get_page_raw_text(self, page_num):
        """Get the raw text of a page.

        Args:
            page_num (int): Page number

        Returns:
            str or None: Raw text of the page if it exists. Otherwise, None.
        """
        page = self.get_page(page_num)
        if page is None:
            return None
        else:
            return page.get(FieldNames.PAGE_RAW_TEXT)

    def set_field(self, field_name, value):
        """Set the value of a field in the object's doc_dict.

        Args:
            field_name (str): Field name
            value (unknown): Value to set 
        """
        self.doc_dict[field_name] = value

    def set_paragraph_entities(self, par_dict, entities):
        """Set the entities value for a paragraph.

        Args:
            par_dict (dict): Dictionary representation of the paragraph
            entities (dict): Dictionary such that keys (str) are entity types 
                and values (list of str) are entities of the different entity 
                types.
        """
        par_dict[FieldNames.ENTITIES] = entities

    def make_paragraph_dicts(self):
        """Split the document into dictionary representations of its paragraphs.

        Each dict will have the following keys and values:
            FieldNames.TYPE (str): str
            FieldNames.FILENAME (str): str
            FieldNames.PAR_INC_COUNT: int
            FieldNames.ID: str
            FieldNames.PAR_COUNT: int
            FieldNames.PAGE_NUM: int
            FieldNames.PAR_RAW_TEXT: str
            FieldNames.ENTITIES: empty list (see entities.py for entity extraction)

        Returns:
            list of dict
        """
        par_dicts = []
        pages = self.get_field(FieldNames.PAGES)
        if pages is None:
            return par_dicts
        filename = self.get_field(FieldNames.FILENAME)
        if filename is None:
            filename = ""

        for page_num, _ in enumerate(pages):
            page_text = self.get_page_raw_text(page_num)

            for par_num, tokens in enumerate(process(page_text)):
                par_text = Document.tokens_to_str(tokens)
                entities = []
                par_count = self.get_field(FieldNames.PAR_COUNT)
                if par_count is None:
                    par_count = 0
                par_dicts.append(
                    {
                        FieldNames.TYPE: "paragraph",
                        FieldNames.FILENAME: filename,
                        FieldNames.PAR_INC_COUNT: par_count,
                        FieldNames.ID: self.make_paragraph_id(
                            filename, par_count
                        ),
                        FieldNames.PAR_COUNT: par_num,
                        FieldNames.PAGE_NUM: page_num,
                        FieldNames.PAR_RAW_TEXT: utf8_pass(
                            normalize_dod(par_text)
                        ),
                        FieldNames.ENTITIES: entities,
                    }
                )
                # TODO: par_count_i was 0 for all paragraphs? see if adding if block change fixed it
                self.set_field(FieldNames.PAR_COUNT, par_count + 1)

        return par_dicts

    def make_paragraph_id(self, filename, par_count_i):
        """Make the "id" field for a paragraph.

        Args:
            filename (str): File name of the document that the paragraph is from.
            par_count_i (int): TODO

        Returns:
            str
        """
        if filename is None:
            filename = ""
        if par_count_i is None:
            par_count_i = ""

        return f"{filename}_{str(par_count_i)}"

    @staticmethod
    def tokens_to_str(tokens):
        """Convert tokens to strings.

        Also removes whitespace formatting (e.g., newlines).

        Args:
            tokens (list of syntok.tokenizer.Token) TODO check input type

        Returns:
            str
        """
        return " ".join(
            [
                " ".join([token.spacing + token.value for token in sentence])
                for sentence in tokens
            ]
        )

