import fitz
from pathlib import Path
from typing import Union


def is_valid_pdf(file: Union[Path, str]) -> bool:
    file_path = Path(file).resolve()

    try:
        fitz.open(file_path)
    except RuntimeError as e:
        if 'no objects found' in e.args:
            return False
    return True
