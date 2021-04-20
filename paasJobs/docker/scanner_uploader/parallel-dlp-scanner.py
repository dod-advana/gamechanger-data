import subprocess as sub
from concurrent.futures.process import ProcessPoolExecutor
from pathlib import Path
import typing as t
import multiprocessing as mp
import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cores", help="num of cores for scanner to use, default is max",type=int, default=mp.cpu_count())
    parser.add_argument("--scanner-path", help="path of dlp scanner", type=str, default="/srv/dlp-scanner/dlp-scanner.sh")
    parser.add_argument("--input-path", help="directory or file to scan", type=str)

    return parser.parse_args()


def run_scanner(script_path: t.Union[str,Path], input_path: t.Union[str, Path]) -> bool:
    """

    :param script_path: path to dlp scanner
    :param input_file: path to input file to scan
    """
    try:
        input_path = Path(input_path).resolve()
        script_path = Path(script_path).resolve()
        completed_process = sub.run([
            '/bin/bash',
            str(script_path),
            str(input_path)
        ])
        return completed_process.returncode == 0
    except:
        return False



def _starmap_run_scanner(args):
    run_scanner(*args)

def process_dir(script_path: t.Union[str,Path], input_path: t.Union[str, Path], cores: int):
    """

    :param script_path: path to scanner function
    :param input_path: files or directory of files to scan
    :param cores: num cores for parallel processing

    """
    # parallelize dlp scanner using map; map takes chunk 1 default begins new process when pid is free
    input_path = Path(input_path).resolve()
    script_path = Path(script_path).resolve()
    total_count = len([p for p in input_path.iterdir() if p.is_file()])
    good = 0
    bad = 0

    def report_progress(result):
        nonlocal good
        nonlocal bad
        good += 1 if result else 0
        bad += 1 if not result else 0
        print(f"[JOB INFO] PROGRESS:{good + bad}/{total_count}")

    with ProcessPoolExecutor(max_workers=cores) as pp:
        results = pp.map(_starmap_run_scanner, ((script_path, p) for p in input_path.iterdir() if p.is_file() and p.name != 'manifest.json'))
        for r in results:
            report_progress(r)

    # process manifest json last to signify upload is over
    if Path(input_path, 'manifest.json').is_file():
        manifest_result = run_scanner(script_path, Path(input_path, 'manifest.json'))
        report_progress(manifest_result)


if __name__=="__main__":

    args = parse_args()

    if Path(args.input_path).is_dir():
        process_dir(args.scanner_path, args.input_path, args.cores)
    else:
        run_scanner(args.scanner_path, args.input_path)

