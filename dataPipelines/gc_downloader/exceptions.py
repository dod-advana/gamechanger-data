from typing import Union
from pathlib import Path


class UnsupportedFilename(Exception):
    # TODO: remove this
    pass


class ProcessingError(Exception):
    """Something went wrong when processing doc"""
    pass


class CouldNotDownload(ProcessingError):
    """...when file could not be downloaded"""
    def __init__(self, url: str):
        super().__init__(f"Failed to download file from given url: {url}")


class UnsupportedFileType(ProcessingError):
    """...when attempting to process/download files not explicitly supported"""
    def __init__(self, file: Union[Path, str]):
        file_name = Path(file).name
        super().__init__(f"Tried to process a corrupted file: {file_name}")


class CorruptedFile(ProcessingError):
    """...when file was found to be corrupt in validation"""
    def __init__(self, file: Union[Path, str]):
        file_name = Path(file).name
        super().__init__(f"Tried to process a corrupted file: {file_name}")