import json
import platform
from time import time
from dataPipelines.gc_covid_pipeline import COVIDDocument
from pathlib import Path
import resource
import click
from .COVIDDocument import Issuance


@click.group()
def cli():
    pass


@cli.command(name="json-to-pdf")
@click.option(
    '-s',
    '--source',
    help='A source directory to be processed.',
    type=click.Path(resolve_path=True, exists=True),
)
@click.option(
    '-i',
    '--ignore-files',
    type=str,
)
@click.option(
    '-d',
    '--destination',
    help='Output file path for resulting ',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
)
@click.option(
    '-p',
    '--multiprocess',
    required=False,
    default=-1,
    type=int,
    help="Multiprocessing. If treated like flag, will do max cores available. \
                if treated like option will take integer for number of cores.",
)
@click.option(
    '-z',
    '--memory_percentage',
    required=False,
    default=0.8,
    type=float,
    help="Limited the maximum memory usage.",
)
@click.option(
    '-x',
    '--metadata',
    required=True,
    help='Location of the CSV metadata file',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True)
)

def json_to_pdf_cmd_wrapper(
        source, destination, multiprocess, metadata, ignore_files, memory_percentage
) -> None:
    if platform.system() == "Linux":
        memory_limit(memory_percentage)

    json_to_pdf(source, destination, metadata, ignore_files, multiprocess)


def json_to_pdf(source, destination, metadata, ignore_files, multiprocess=-1) -> None:
    start = time()
    if Path(source).is_file():
        print("Parsing Single Document")
        Issuance(source, destination)
    else:
        COVIDDocument.process_dir(dir_path=source, out_dir=destination, metadata_file=metadata, ignore_files=ignore_files, multiprocess=multiprocess)

    end = time()
    print(f'Total JSON-to-PDF time -- It took {end - start} seconds!')


def memory_limit(memory_percentage: float):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    print("Memory Hard Limit: " + str(hard) + " Soft Limit: " + str(
        soft) + " Maximum of percentage of memory use: " + str(memory_percentage))
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * memory_percentage, hard))


def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    print("____________________ " + str(free_memory) + "____________________")
    return free_memory
