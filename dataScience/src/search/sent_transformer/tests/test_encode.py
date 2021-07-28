import logging
import os
import pytest

logger = logging.getLogger(__name__)


def test_sent_encode(sent_encoder, sent_dirs, index_files):
    """
    Test for encoding a corpus folder
    """
    data_dir, data_dir_2, index_dir = sent_dirs
    sent_encoder.index_documents(data_dir, index_dir, overwrite=True)

    for file in index_files:
        fpath = os.path.join(index_dir, file)
        assert os.path.isfile(fpath)

    embedder_ids = sent_encoder.embedder.config["ids"]

    assert len(embedder_ids) == 145


def test_sent_merge(sent_encoder, sent_dirs, index_files):
    """
    Test for encoding new documents
    """
    data_dir, data_dir_2, index_dir = sent_dirs
    sent_encoder.index_documents(data_dir_2, index_dir)

    for file in index_files:
        fpath = os.path.join(index_dir, file)
        assert os.path.isfile(fpath)

    embedder_ids = sent_encoder.embedder.config["ids"]

    assert len(embedder_ids) == 271
