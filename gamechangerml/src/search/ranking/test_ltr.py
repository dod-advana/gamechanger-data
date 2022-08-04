from gamechangerml.src.search.ranking.ltr import LTR
from gamechangerml.src.utilities.user_utils import normalize
import pandas as pd
import numpy as np

ltr = LTR()
judgements = None


def test_read_mappings():
    mappings = ltr.read_mappings()
    assert isinstance(mappings, pd.DataFrame)


def test_generate_judgement_exists():
    judgements = ltr.generate_judgement(ltr.mappings[:10])
    assert isinstance(judgements, pd.DataFrame)


def test_construct_query():
    query = ltr.construct_query("AFI 36-2110.pdf", "veteran")
    actual = {
        "_source": ["filename", "fields"],
        "query": {
            "bool": {
                "filter": [
                    {"terms": {"filename": ["AFI 36-2110.pdf"]}},
                    {
                        "sltr": {
                            "_name": "logged_featureset",
                            "featureset": "doc_features",
                            "params": {"keywords": "veteran"},
                        }
                    },
                ]
            }
        },
        "ext": {
            "ltr_log": {
                "log_specs": {"name": "log_entry1", "named_query": "logged_featureset"}
            }
        },
    }
    assert query == actual


def test_process_ltr_log():
    log = [
        [
            {
                "_index": "gamechanger_20211014",
                "_type": "_doc",
                "_id": "faa5c0e8e4d9dca2f4e05838775c31959e144c0dbfc97b6eaa0c6edc206515d7",
                "_score": 0.0,
                "_source": {"filename": "AFI 17-130.pdf"},
                "fields": {
                    "_ltrlog": [
                        {
                            "log_entry1": [
                                {"name": "title", "value": 2.0},
                                {"name": "keyw_5"},
                                {"name": "textlength", "value": 21.0},
                                {"name": "paragraph", "value": 6.8133063},
                            ]
                        }
                    ]
                },
                "matched_queries": ["logged_featureset"],
            }
        ],
        [
            {
                "_index": "gamechanger_20211014",
                "_type": "_doc",
                "_id": "7ef50e434c0fb42da31d7b720c13614e47640ed0e6e6c59607e2e805bf66b087",
                "_score": 0.0,
                "_source": {"filename": "AFI 99-103.pdf"},
                "fields": {
                    "_ltrlog": [
                        {
                            "log_entry1": [
                                {"name": "title"},
                                {"name": "keyw_5"},
                                {"name": "textlength", "value": 123.0},
                                {"name": "paragraph", "value": 4.470147},
                            ]
                        }
                    ]
                },
                "matched_queries": ["logged_featureset"],
            }
        ],
        [
            {
                "_index": "gamechanger_20211014",
                "_type": "_doc",
                "_id": "b8cc78f957169bf7c3595c171a53aa6fccb1c108b5972a5ee39abe334043bec5",
                "_score": 0.0,
                "_source": {"filename": "AR 25-2.pdf"},
                "fields": {
                    "_ltrlog": [
                        {
                            "log_entry1": [
                                {"name": "title", "value": 2.0},
                                {"name": "keyw_5"},
                                {"name": "textlength", "value": 57.0},
                                {"name": "paragraph", "value": 7.5755434},
                            ]
                        }
                    ]
                },
                "matched_queries": ["logged_featureset"],
            }
        ],
        [
            {
                "_index": "gamechanger_20211014",
                "_type": "_doc",
                "_id": "43d5a144894034d8beb8a83e3d1809310de1c8bcf8a1446838637d2e27ee707c",
                "_score": 0.0,
                "_source": {"filename": "ATP 6-01.1.pdf"},
                "fields": {
                    "_ltrlog": [
                        {
                            "log_entry1": [
                                {"name": "title"},
                                {"name": "keyw_5"},
                                {"name": "textlength", "value": 146.0},
                                {"name": "paragraph", "value": 2.7437596},
                            ]
                        }
                    ]
                },
                "matched_queries": ["logged_featureset"],
            }
        ],
    ]
    log = ltr.process_ltr_log(log)
    print(log)
    expected = [
        [2.0, 0, 21.0, 6.8133063],
        [0, 0, 123.0, 4.470147],
        [2.0, 0, 57.0, 7.5755434],
        [0, 0, 146.0, 2.7437596],
    ]

    assert np.array_equal(expected, log)


def test_normalize():
    norm = normalize(np.array([1, 3, 4, 5]))
    assert np.array_equal(
        norm.tolist(), [0.0, 2.7304247779439415, 3.4454124645871445, 4.0]
    )
