import subprocess as sub
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path
import typing as t
import multiprocessing as mp
import sys
import argparse
import hashlib


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cores", help="num of cores for scanner to use, default is max",type=int, default=mp.cpu_count())
    parser.add_argument("--scanner-path", help="path of dlp scanner", type=str, default="/srv/dlp-scanner/dlp-scanner.sh")
    parser.add_argument("--input-path", help="directory or file to scan", type=str)

    return parser.parse_args()

def calculate_md5(filepath:str)->str:
    with open(filepath, "rb") as f:
        file_hash = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            file_hash.update(chunk)
            chunk = f.read(8192)

        return file_hash.hexdigest()


if __name__=="__main__":

    args = parse_args()



