def make_query_one_doc(query, docid):
    """Make a query for ES that will search one doc for the best matching paragraphs."""

    true = True
    false = False
    
    search_query = {
        "_source": {
            "includes": ["pagerank_r", "kw_doc_score_r", "orgs_rs", "topics_rs"]
        },
        "stored_fields": [
            "filename",
            "title",
            "page_count",
            "doc_type",
            "doc_num",
            "ref_list",
            "id",
            "summary_30",
            "keyw_5",
            "p_text",
            "type",
            "p_page",
            "display_title_s",
            "display_org_s",
            "display_doc_type_s",
            "is_revoked_b",
            "access_timestamp_dt",
            "publication_date_dt",
            "crawler_used_s",
        ],
        "from": 0,
        "size": 50,
        "track_total_hits": true,
        "query": {
            "bool": {
                "must": [
                    {"match": {"id": docid}},
                    {
                        "nested": {
                            "path": "paragraphs",
                            "inner_hits": {
                                "_source": false,
                                "stored_fields": [
                                    "paragraphs.page_num_i",
                                    "paragraphs.filename",
                                    "paragraphs.par_raw_text_t",
                                ],
                                "from": 0,
                                "size": 5,
                                "highlight": {
                                    "fields": {
                                        "paragraphs.filename.search": {
                                            "number_of_fragments": 0
                                        },
                                        "paragraphs.par_raw_text_t": {
                                            "fragment_size": 200,
                                            "number_of_fragments": 1,
                                        },
                                    },
                                    "fragmenter": "span",
                                },
                            },
                            "query": {
                                "bool": {
                                    "should": [
                                        {
                                            "wildcard": {
                                                "paragraphs.filename.search": {
                                                    "value": query,
                                                    "boost": 15,
                                                }
                                            }
                                        },
                                        {
                                            "query_string": {
                                                "query": query,
                                                "default_field": "paragraphs.par_raw_text_t",
                                                "default_operator": "AND",
                                                "fuzzy_max_expansions": 100,
                                                "fuzziness": "AUTO",
                                            }
                                        },
                                    ]
                                }
                            },
                        }
                    },
                ],
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "keyw_5^2",
                                "id^2",
                                "summary_30",
                                "paragraphs.par_raw_text_t",
                            ],
                            "operator": "or",
                        }
                    },
                    {"rank_feature": {"field": "pagerank_r", "boost": 0.5}},
                    {"rank_feature": {"field": "kw_doc_score_r", "boost": 0.1}},
                ],
            }
        },
    }

    return search_query

def make_query(query):
    """Make a query for ES that will search any docs for matching paragraphs."""

    true = True
    false = False
    
    search_query = {
        "_source": {
            "includes": ["pagerank_r", "kw_doc_score_r", "orgs_rs", "topics_rs"]
        },
        "stored_fields": [
            "filename",
            "title",
            "page_count",
            "doc_type",
            "doc_num",
            "ref_list",
            "id",
            "summary_30",
            "keyw_5",
            "p_text",
            "type",
            "p_page",
            "display_title_s",
            "display_org_s",
            "display_doc_type_s",
            "is_revoked_b",
            "access_timestamp_dt",
            "publication_date_dt",
            "crawler_used_s",
        ],
        "from": 0,
        "size": 50,
        "track_total_hits": true,
        "query": {
            "bool": {
                "must": [
                    {
                        "nested": {
                            "path": "paragraphs",
                            "inner_hits": {
                                "_source": false,
                                "stored_fields": [
                                    "paragraphs.page_num_i",
                                    "paragraphs.filename",
                                    "paragraphs.par_raw_text_t",
                                ],
                                "from": 0,
                                "size": 5,
                                "highlight": {
                                    "fields": {
                                        "paragraphs.filename.search": {
                                            "number_of_fragments": 0
                                        },
                                        "paragraphs.par_raw_text_t": {
                                            "fragment_size": 200,
                                            "number_of_fragments": 1,
                                        },
                                    },
                                    "fragmenter": "span",
                                },
                            },
                            "query": {
                                "bool": {
                                    "should": [
                                        {
                                            "wildcard": {
                                                "paragraphs.filename.search": {
                                                    "value": query,
                                                    "boost": 15,
                                                }
                                            }
                                        },
                                        {
                                            "query_string": {
                                                "query": query,
                                                "default_field": "paragraphs.par_raw_text_t",
                                                "default_operator": "AND",
                                                "fuzzy_max_expansions": 100,
                                                "fuzziness": "AUTO",
                                            }
                                        },
                                    ]
                                }
                            },
                        }
                    },
                ],
                "should": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": [
                                "keyw_5^2",
                                "id^2",
                                "summary_30",
                                "paragraphs.par_raw_text_t",
                            ],
                            "operator": "or",
                        }
                    },
                    {"rank_feature": {"field": "pagerank_r", "boost": 0.5}},
                    {"rank_feature": {"field": "kw_doc_score_r", "boost": 0.1}},
                ],
            }
        },
    }

    return search_query
