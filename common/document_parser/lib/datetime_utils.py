from datetime import datetime
from common.utils.parsers import parse_timestamp


def get_publication_date(doc_dict):
    try:
        parsed_date = parse_timestamp(doc_dict.get("publication_date", None))
        if parsed_date:
            return datetime.strftime(parsed_date, '%Y-%m-%dT%H:%M:%S')
    except:
        return ""

def get_access_timestamp(doc_dict):
    try:
        parsed_date = parse_timestamp(doc_dict.get("access_timestamp", None))
        if parsed_date:
            return datetime.strftime(parsed_date, '%Y-%m-%dT%H:%M:%S')
    except:
        return ""