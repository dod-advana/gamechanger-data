import logging
import gamechangerml.src.featurization.abbreviation as abbreviation

logger = logging.getLogger(__name__)


def test_expansion_dict():
    check_str = "Article 15 of the Uniform Code of Military Justice UCMJ or pending discharge based on action under the UCMJ are temporarily nondeployable."
    abb_dict = [
        {"abbr_s": "Uniform Code of Military Justice", "description_s": "ucmj"}
    ]
    text, list = abbreviation.expand_abbreviations(check_str)
    assert abb_dict == list


def test_expansion_text():
    check_str = "Article 15 of the Uniform Code of Military Justice UCMJ or pending discharge based on action under the UCMJ are temporarily nondeployable."
    new_str = "Article 15 of the Uniform Code of Military Justice or pending discharge based on action under the Uniform Code of Military Justice are temporarily nondeployable."
    text, list = abbreviation.expand_abbreviations(check_str)
    assert new_str == text


def test_expansion_no_context_1():
    check_str = "DoD"
    expansion = ["Department of Defense"]
    result = abbreviation.expand_abbreviations_no_context(check_str)
    assert expansion == result


def test_expansion_no_context_2():
    check_str = "DOD"
    expansion = ["Department of Defense"]
    result = abbreviation.expand_abbreviations_no_context(check_str)
    assert expansion == result


def test_expansion_no_context_3():
    check_str = "CI"
    expansion = ["counterintelligence"]
    result = abbreviation.expand_abbreviations_no_context(check_str)
    assert expansion == result
