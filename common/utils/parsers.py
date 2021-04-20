import typing as t
import datetime
import pandas


def parse_timestamp(ts: t.Union[str, datetime.datetime], raise_parse_error: bool = False) -> t.Optional[datetime.datetime]:
    """Parse date/timestamp with no particular format
    :param ts: date/timestamp string
    :return: datetime.datetime if parsing was successful, else None
    """
    def _parse(ts):
        if isinstance(ts, datetime.datetime):
            return ts

        try:
            ts = pandas.to_datetime(ts).to_pydatetime()
            if str(ts) == 'NaT':
                return None
            else:
                return ts
        except:
            return None

    parsed_ts = _parse(ts)
    if parsed_ts is None and raise_parse_error:
        raise ValueError(f"Invalid timestamp: '{ts!r}'")
    else:
        return parsed_ts


def parse_formatted_timestamp(ts_str: str, fmt_str: str) -> t.Optional[datetime.datetime]:
    """Parse datetime from given string according to given format
    :param ts_str: timestamp string
    :param fmt_str: timestamp format
    :return: datetime.datetime if parsing was successful, else None
    """
    try:
        return datetime.datetime.strptime(ts_str, fmt_str)
    except:
        return None
