def query(search_text,query_type=None):
    standard_query ={
      "_source": {
        "includes": [
          "pagerank_r",
          "kw_doc_score_r"
        ]
      },
      "stored_fields": [
        "filename",
        "title",
        "id",
        "summary_30",
        "keyw_5",
        "p_text",
        "type",
        "p_page",
        "display_title_s",
        "is_revoked_b",
        "access_timestamp_dt",
        "publication_date_dt",
        "crawler_used_s"
      ],
      "from": 0,
      "size": 500,
      "track_total_hits": True,
      "aggs": {
        "doc_type_aggs": {
          "terms": {
            "field": "display_doc_type_s",
            "size": 10000
          }
        },
        "doc_org_aggs": {
          "terms": {
            "field": "display_org_s",
            "size": 10000
          }
        }
      },
      "query": {
        "bool": {
          "must": [],
          "should": [
            {
              "nested": {
                "path": "paragraphs",
                "inner_hits": {
                  "_source": "false",
                  "from": 0,
                  "size": 5,
                  "highlight": {
                    "fields": {
                      "paragraphs.par_raw_text_t.gc_english": {
                        "fragment_size": 400,
                        "number_of_fragments": 1,
                        "type": "plain"
                      }
                    },
                    "fragmenter": "span"
                  }
                },
                "query": {
                  "bool": {
                    "should": [
                      {
                        "query_string": {
                          "query": "Defense Intelligence Agency",
                          "default_field": "paragraphs.par_raw_text_t.gc_english",
                          "default_operator": "AND",
                          "fuzzy_max_expansions": 1000,
                          "fuzziness": "AUTO",
                          "analyzer": "gc_english"
                        }
                      }
                    ]
                  }
                }
              }
            },
            {
              "multi_match": {
                "query": "Defense Intelligence Agency",
                "fields": [
                  "title.search",
                  "filename.search"
                ],
                "type": "phrase"
              }
            },
            {
              "wildcard": {
                "keyw_5": {
                  "value": "*Defense Intelligence Agency*"
                }
              }
            },
            {
              "wildcard": {
                "title.search": {
                  "value": "*Defense Intelligence Agency*",
                  "boost": 4
                }
              }
            },
            {
              "wildcard": {
                "filename.search": {
                  "value": "*Defense Intelligence Agency*",
                  "boost": 4
                }
              }
            }
          ],
          "minimum_should_match": 1,
          "filter": [
            {
              "term": {
                "is_revoked_b": "false"
              }
            }
          ]
        }
      },
      "highlight": {
        "fields": {
          "title.search": {},
          "keyw_5": {},
          "id": {},
          "filename.search": {}
        },
        "fragmenter": "simple",
        "type": "unified",
        "boundary_scanner": "word"
      },
      "sort": [
        {
          "_score": {
            "order": "desc"
          }
        }
      ]
    } 
    if query_type == "no_agg":
        standard_query.pop("aggs")
    if query_type == "no_highlight":
        standard_query.pop("highlight")
        standard_query['query']['bool']['should'][0]['nested']['inner_hits'] ={}
    return standard_query
