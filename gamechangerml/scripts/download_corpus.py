from gamechangerml.src.utilities.utils import get_s3_corpus
import argparse

"""
use:
    python gamechangerml/scripts/download_corpus.py -c "corpus_20200909"
Options:
    -c: corpus in S3 location
"""
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Downloads Corpus")
    parser.add_argument("-c", dest="corpus", help="S3 corpus location")
    args = parser.parse_args()
    corpus = args.corpus
    get_s3_corpus(corpus)
