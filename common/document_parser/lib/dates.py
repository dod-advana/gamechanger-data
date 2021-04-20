
"""
This module contains functions for date extractions
"""

import re
import datetime

PAT_DAY_MONTH_YEAR = r"(\d{1,2}\s*(?:january|february|march|april|may|june|july|august|september|october|november|december)\s*,*\s*\d{4})"
PAT_DAY_MONTH_YEAR_SHORT = r"(\d{1,2}\s*(?:jan\.?|feb\.?|mar\.?|apr\.?|may\.?|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)\s*,*\s*\d{4})"
PAT_MONTH_DAY_YEAR = r"((?:january|february|march|april|may|june|july|august|september|october|november|december)\s*\d{1,2}\s*,*\s*\d{4})"
PAT_MONTH_DAY_YEAR_SHORT = r"((?:jan\.?|feb\.?|mar\.?|apr\.?|may\.?|jun\.?|jul\.?|aug\.?|sep\.?|sept\.?|oct\.?|nov\.?|dec\.?)\s*\d{1,2}\s*,*\s*\d{4})"


def extract_d_B_Y(text: str):
    """
    Function to extract date from text
    Args:
        text: date to be extracted

    Returns: extracted date in form of list

    """
    date_list = []
    m_comp = re.compile(PAT_DAY_MONTH_YEAR, re.IGNORECASE)
    all_m = m_comp.findall(text)

    for m_date in all_m:
        simp_str = ' '.join(m_date.replace(",", "").replace(".", "").split())
        try:
            date_time_obj = datetime.datetime.strptime(simp_str, '%d %B %Y')
            date_list.append(date_time_obj)
        except ValueError:
            print("Datetime had an issue extracting Date for " + str(simp_str))

    return date_list


def extract_d_B_Y_short(text: str):
    """
    Function to extract date from text
    Args:
        text: date to be extracted

    Returns: extracted date in form of list

    """
    date_list = []
    m_comp = re.compile(PAT_DAY_MONTH_YEAR_SHORT, re.IGNORECASE)
    all_m = m_comp.findall(text)

    for m_date in all_m:
        simp_str = ' '.join(
            m_date.replace(",", "")
            .replace(".", "")
            .lower()
            .replace("sept", "sep")
            .split()
        )
        try:
            date_time_obj = datetime.datetime.strptime(simp_str, '%d %b %Y')
            date_list.append(date_time_obj)
        except ValueError:
            print("Datetime had an issue extracting Date for " + str(simp_str))

    return date_list


def extract_B_d_Y(text: str):
    """
    Function to extract date from text
    Args:
        text: date to be extracted

    Returns: extracted date in form of list

    """
    date_list = []
    m_comp = re.compile(PAT_MONTH_DAY_YEAR, re.IGNORECASE)
    all_m = m_comp.findall(text)

    for m_date in all_m:
        simp_str = ' '.join(m_date.replace(",", "").replace(".", "").split())
        try:
            date_time_obj = datetime.datetime.strptime(simp_str, '%B %d %Y')
            date_list.append(date_time_obj)
        except ValueError:
            print("Datetime had an issue extracting Date for " + str(simp_str))

    return date_list


def extract_B_d_Y_short(text: str):
    """
    Function to extract date from text
    Args:
        text: date to be extracted

    Returns: extracted date in form of list

    """
    date_list = []
    m_comp = re.compile(PAT_MONTH_DAY_YEAR_SHORT, re.IGNORECASE)
    all_m = m_comp.findall(text)

    for m_date in all_m:
        simp_str = ' '.join(
            m_date.replace(",", "")
            .replace(".", "")
            .lower()
            .replace("sept", "sep")
            .split()
        )
        try:
            date_time_obj = datetime.datetime.strptime(simp_str, '%b %d %Y')
            date_list.append(date_time_obj)
        except ValueError:
            print("Datetime had an issue extracting Date for " + str(simp_str))

    return date_list


def dates_to_list(text: str):
    """
    Takes as an input a string of any lenght and outputs a list of datetime objects
    that were found in the string

    Formats currently supported:
    %B %d %Y
    %d %B %Y

    Examples:
    31 september 1998
    31 August, 2000
    August 31, 1984

     Args:
        text: date to be extracted

    Returns: extracted date in form of list

    """

    date_list = []

    date_list += extract_d_B_Y(text)
    date_list += extract_B_d_Y_short(text)
    date_list += extract_B_d_Y(text)
    date_list += extract_B_d_Y_short(text)

    return date_list


def add_dates_list(doc_dict):
    doc_dict["date_list"] = dates_to_list(doc_dict["text"])
    doc_dict["date_list"] = [str(d) for d in doc_dict["date_list"]]
    return doc_dict


def process(doc_dict):
    dates_dict = add_dates_list(doc_dict)
    return dates_dict
