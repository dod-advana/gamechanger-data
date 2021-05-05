import time
from pathlib import Path
import requests
from typing import List, Any, Optional, Union
from .file_utils import get_available_path
from .string_utils import normalize_string
import re
from urllib.parse import urlparse
from .exceptions import UnsupportedFilename, CouldNotDownload
from .config import SUPPORTED_FILE_EXTENSIONS
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
import os



def is_downloadable(url: str) -> bool:
    """Does the url contain a downloadable resource"""
    h = requests.head(url, allow_redirects=True)
    header = h.headers
    content_type = header.get('content-type')
    if content_type:
        if 'text' in content_type.lower():
            return False
        if 'html' in content_type.lower():
            return False 
    return True


def is_supported_filename(filename: str) -> bool:
    """Check if proposed filename is one of those supported by downloader"""
    file_suffix = Path(filename).suffix.lower()

    if not file_suffix:
        return False

    if file_suffix not in SUPPORTED_FILE_EXTENSIONS:
        return False

    return True


def derive_download_filename(resp: requests.Response, request_url: Optional[str] = None) -> str:
    """
    Derives possible filename for downloaded artifact from given url and response
    :param resp: requests.Response from requested url
    :param request_url: the request url
    :return: most suitable filename based on response headers or request url
    """
    filename_from_request_url = normalize_string(Path(urlparse(request_url or '').path).name)
    filename_from_response_url = normalize_string(Path(urlparse(resp.url).path).name)
    filename_from_headers = ""
    filename_of_last_resort = "unknown_file"

    if "Content-Disposition" in resp.headers.keys():
        filename_from_headers = normalize_string(re.findall("filename=(.+)", resp.headers["Content-Disposition"])[0])

    if is_supported_filename(filename_from_headers):
        return filename_from_headers
    elif is_supported_filename(filename_from_response_url):
        return filename_from_response_url
    elif is_supported_filename(filename_from_request_url):
        return filename_from_request_url
    else:
        return filename_of_last_resort


def derive_download_filename_driver(request_url: str, driver_url: Optional[str] = None) -> str:
    """
    Derives possible filename for downloaded artifact from given url and response
    :param request_url: the request url
    :param driver: the driver
    :return: most suitable filename based on current driver url or request url
    """
    filename_from_request_url = Path(urlparse(request_url).path).name.replace("%20", " ")
    filename_from_driver_url = Path(urlparse(driver_url or '').path).name.replace("%20", " ")
    filename_of_last_resort = "unknown_file"

    if is_supported_filename(filename_from_driver_url):
        return filename_from_driver_url
    if is_supported_filename(filename_from_request_url):
        return filename_from_request_url
    else:
        return filename_of_last_resort


def download_file(
    url: str,
    output_dir: Union[str, Path],
    num_retries: int = 2,
    overwrite: bool = False,
    check_first: bool = False,
    timeout_secs: Union[int, float] = 10
) -> Path:
    """Download file at given url to given output directory, preserving file name

    :param url: web url to downloadable resource
    :param output_dir: path to output directory for the download
    :param num_retries: number of times download will retry in case of failure
    :param overwrite: whether downloader should overwrite files with same base names in output dir
    :param check_first: check whether url is downloadable., undesirable if web host could deny HEAD requests
    :param timeout_secs: timeout, in seconds, before receiving first byte of response

    :returns: pathlib.Path of the downloaded file
    :raises: CouldNotDownload
    """
    if check_first:
        is_downloadable(url)

    _output_dir = Path(output_dir)
    if not _output_dir.is_dir():
        raise ValueError("Output dir doesn't exist: {}".format(output_dir))

    local_file_path: Optional[Path] = None
    for retry_attempt in range(int(num_retries)):
        # TODO: Implement actual request throttling through custom request adapter
        try:
            # NOTE the stream=True parameter below
            with requests.get(url, stream=True, timeout=timeout_secs, allow_redirects=True,verify=False) as r:
                r.raise_for_status()

                local_file_path = _output_dir.joinpath(derive_download_filename(resp=r, request_url=url))
                if not overwrite:
                    local_file_path = Path(get_available_path(local_file_path))

                with open(local_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
        except requests.exceptions.ReadTimeout as e:
            print(e)
            print(f"Timed out fetching: {url}")
            continue
        except requests.ConnectionError as e:
            print(e)
            print(f"Connection error while fetching: {url}")
            continue
        except requests.HTTPError as e:
            print(e)
            break
        else:
            break
        finally:
            time.sleep(1 + retry_attempt)

    result = (
        (local_file_path if local_file_path.exists() else None)
        if local_file_path
        else None
    )

    if not result:
        raise CouldNotDownload(url)

    return result


def download_file_with_driver(
        url: str,
        output_dir: str,
        driver: webdriver.Chrome,
        num_retries: int = 2,
        overwrite: bool = False

) -> Path:
    """Download file at given url to given output directory, preserving file name

    :param url: web url to downloadable resource
    :param output_dir: path to output directory for the download
    :param driver: driver used
    :param num_retries: number of times download will retry in case of failure
    :param overwrite: whether downloader should overwrite files with same base names in output dir
    :param timeout_secs: timeout, in seconds, before receiving first byte of response

    :returns: pathlib.Path of the downloaded file
    :raises: CouldNotDownload
    """

    _output_dir = Path(output_dir)
    if not _output_dir.is_dir():
        raise ValueError("Output dir doesn't exist: {}".format(output_dir))

    local_file_path: Optional[Path] = None
    temp_file_path: Optional[Path] = None
    download_file_path: Optional[Path] = None
    for retry_attempt in range(int(num_retries)):

        # TODO: Implement actual request throttling through custom request adapter
        try:

            local_file_path = _output_dir.joinpath(derive_download_filename_driver(request_url=url))
            temp_file_path = get_available_path(local_file_path)
            download_file_path = Path(str(local_file_path)+".crdownload")

            if local_file_path.exists() and overwrite:
                os.rename(local_file_path, temp_file_path)
                print(temp_file_path)

            driver.get(url)

        except WebDriverException as e:
            if overwrite and os.path.isfile(temp_file_path):
                os.rename(temp_file_path, local_file_path)
            print(e)
            print(f"Web Driver Exceptions when fetching: {url}")
            continue
        except TimeoutException as e:
            if overwrite and os.path.isfile(temp_file_path):
                os.rename(temp_file_path, local_file_path)
            print(e)
            print(f"Timeout fetching: {url}")
            continue
        else:
            break
        finally:
            time.sleep(1 + num_retries)
            while download_file_path.exists():
                time.sleep(2)  # extra wait for download to go through may take a few seconds
            if overwrite:
                if local_file_path.exists():
                    os.remove(temp_file_path)
                else:
                    # download did not occur, return the original file back to its location
                    os.rename(temp_file_path, local_file_path)

            result = (
                (local_file_path if local_file_path.exists() else None)
                if local_file_path
                else None
            )

            if not result:
                raise CouldNotDownload(url)

            return result


def doc_in_manifest(manifest: List[Any], version_hash: str) -> bool:
    """checks if document is in the manifest"""
    flag = False
    if any(d['version_hash'] == version_hash for d in manifest):
        flag = True

    return flag
