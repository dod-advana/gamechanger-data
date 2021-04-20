from pathlib import Path
from typing import Union, Iterable, Generator

import zipfile
import hashlib
import shutil
from typing import List
import os


def pad_empty_file(file_path: Union[str, Path]) -> None:
    """Adds space to an otherwise empty file for compatibility purposes
    :param file_path: path to a potentially empty file
    :returns: Nothing - adds UTF8 newline to a file if it was empty beforehand
    """
    file_path = Path(file_path).resolve()
    if os.stat(str(file_path)).st_size == 0:
        with file_path.open(mode='a') as f:
            f.write('\n')

def get_available_path(desired_path: Union[str, Path]) -> Path:
    """Given desired path, returns one that uses desired path as prefix but won't overwrite existing files
    :param desired_path: proposed file/dir path
    :returns: available file/dir path
    """
    original_path = Path(desired_path)
    base_dir = Path(original_path).parent
    base_ext = original_path.suffix
    base_name = original_path.name[
        : (-len(base_ext) if original_path.is_file() else None)
    ]

    if not base_dir.is_dir():
        raise ValueError(f"Base dir for path does not exist: {base_dir.absolute()}")

    def suffix_generator() -> Generator[str, None, None]:
        base = "dup"
        counter = 1
        while True:
            yield f"{base}{counter}"
            counter += 1

    path_candidate = Path(desired_path)
    suffixes = suffix_generator()

    _sanity_check_limit = (
        100_000  # to avoid infinite loops if there are issues with file cleanup
    )
    while True:
        if path_candidate.exists():
            new_suffix = next(suffixes)
            new_filename = f"{base_name}_{new_suffix}{base_ext}"
            path_candidate = Path(base_dir, new_filename)
        else:
            break
        if _sanity_check_limit <= 0:
            raise RuntimeError(
                "File name generator exceeded sensible number of retries."
            )
        _sanity_check_limit -= 1

    return path_candidate.resolve()


def iter_all_files(dir_path: Union[Path, str], recursive: bool = True) -> Iterable[Path]:
    """Iterate over all files in dir tree
    :param dir_path: path to directory where the files are located
    :param recursive: whether to return files for entire dir tree

    :returns: iterable of file pathlib.Path objects in the dir tree
    """
    _dir_path = Path(dir_path)
    if not _dir_path.is_dir():
        raise ValueError(f"Got invalid dir_path: {_dir_path}")

    if recursive:
        for file in filter(lambda p: p.is_file(), _dir_path.rglob("*")):
            yield file
    else:
        for file in filter(lambda p: p.is_file(), _dir_path.glob("*")):
            yield file


def md5_for_file(file_path: Union[Path, str], block_size: int = 8192) -> str:
    """Get md5 hex digest for a file.
    :param file_path: Path to input file
    :param block_size: Input block size. Should be multiple of 128 bytes.

    :returns: md5 hex digest
    """

    _path = Path(file_path)
    if not _path.is_file():
        raise ValueError(f"Provided file path is invalid: {file_path}")

    if not (block_size >= 0 and not block_size % 128):
        raise ValueError(f"Provided block_size is invalid: {block_size}")

    md5 = hashlib.md5()
    with open(_path, 'rb') as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)

    return md5.hexdigest()


def unzip_all(zip_file: Union[Path, str], output_dir: str) -> List[Path]:
    """ Unzip all items in the input file and place them inside output_dir
    :param zip_file: path to zip file
    :param output_dir: path to desired output directory

    :return: flat list of files unzipped to the output_dir
    """

    input_file_path = Path(zip_file).resolve()
    output_dir_path = Path(output_dir).resolve()

    if not input_file_path.is_file():
        raise ValueError(f"Given zip_file is invalid: {zip_file}")
    if not output_dir_path.is_dir():
        raise ValueError(f"Given output_dir is invalid: {output_dir}")

    if any(output_dir_path.iterdir()):
        output_dir_path = get_available_path(output_dir_path)

    def unzip_nested(zip_path: Path, dir_path: Path) -> None:
        with zipfile.ZipFile(Path(zip_path).absolute()) as zip_ref:
            zip_ref.extractall(dir_path)

        for path in iter_all_files(dir_path):
            if path.suffix == ".zip":
                new_output_dir = Path(get_available_path(Path(dir_path, "tmp_unzip")))
                new_output_dir.mkdir()
                unzip_nested(path.absolute(), new_output_dir.absolute())
                path.unlink()

    unzip_nested(input_file_path, output_dir_path)
    unzipped_file_paths = list(iter_all_files(output_dir_path))

    return unzipped_file_paths


def safe_move_file(file_path: Union[Path, str], output_path: Union[Path, str], copy: bool = False) -> Path:
    """Safely moves/copies file to given directory
    by changing file suffix (sans extension) to avoid collisions, if necessary

    :param file_path: Source file, must exist
    :param output_path: Destination directory, must exist
    :param copy: Flag to perform copy instead of move
    :return: Path to moved/copied file location
    """
    _file_path = Path(file_path).resolve()
    _output_path = Path(output_path).resolve()

    desired_path = Path(_output_path, _file_path.name) if _output_path.is_dir() else _output_path
    available_dest_path = Path(get_available_path(desired_path))

    if not _file_path.is_file():
        raise ValueError(f"Given path is not a file: {_file_path!s}")
    if (not available_dest_path.parent.is_dir()) or (available_dest_path.is_file() and available_dest_path.exists()):
        raise ValueError(f"Given path parent is not a directory or is a file that already exists: {available_dest_path!s}")

    if copy:
        shutil.copy(_file_path, available_dest_path)  # type: ignore
    else:
        shutil.move(_file_path, available_dest_path)  # type: ignore

    return available_dest_path


def purge_dir(dir_path):
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))