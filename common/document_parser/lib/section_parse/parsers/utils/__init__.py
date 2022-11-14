from .shared_utils import (
    next_letter,
    make_pattern_for_uppercase_or_titlecase,
    MONTH_LIST,
    MONTH_ABBREVIATIONS_LIST,
    CAPITAL_ENCLOSURE, 
    DD_MONTHNAME_YYYY,
    remove_pagebreaks,
)
from .dod_utils import (
    PAGEBREAK_DATE_PATTERN,
    find_pagebreak_date,
    is_sentence_continuation,
    is_toc,
    match_section_num,
    next_section_num,
    is_known_section_start,
    starts_with_glossary,
    match_enclosure_num,
    is_subsection_start_for_section_1,
    get_subsection_of_section_1,
    match_alpha_dot,
    match_alpha_single_paren,
    match_alpha_double_parens,
    match_alpha_list_item,
    match_ref_start,
)
from .navy_utils import (
    get_letter_dot_section,
    match_number_hyphenated_section,
    match_number_dot_section,
    APPENDIX_TITLE_PATTERN,
    match_first_appendix_title,
)
