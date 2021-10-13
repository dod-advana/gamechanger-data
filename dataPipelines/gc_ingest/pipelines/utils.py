import sys
import typing
from pathlib import Path


def announce(text: str, *rest):
    print(f"#### PIPELINE INFO #### {text}" +
          " ".join([str(i) for i in rest]), file=sys.stderr)


def get_filepath_from_dir(dir_path: typing.Union[Path, str], full_filepath: typing.Union[Path, str]) -> str:
    filepath_str = str(full_filepath)
    _, __, doc_filepath = filepath_str.partition(str(dir_path))
    return doc_filepath
