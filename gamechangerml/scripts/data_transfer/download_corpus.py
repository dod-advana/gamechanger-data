"""Script to download the data corpus from S3.

Usage Example:
    python gamechangerml/scripts/data_transfer/download_corpus.py -c "corpus_20200909"

Options:
    -c: Directory in S3 that contains the corpus
"""

from gamechangerml.src.data_transfer import download_corpus_s3
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser(description="Downloads Corpus")
    parser.add_argument("-c", dest="corpus", help="S3 corpus location")
    args = parser.parse_args()
    corpus = args.corpus
    download_corpus_s3(corpus)
