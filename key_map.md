# GAMECHANGER DATA FIELDNAMES MAP

## Sources of fields in document json
- document filename
- metadata from scraping
- document text
- statically tagged e.g. pages[] each "type":"page"
- orchestration db

### EXAMPLE METADATA FILE KEYS
```
doc_name
doc_title
doc_num
doc_type
display_doc_type
publication_date
cac_login_required
crawler_used
downloadable_items : [
  {
    doc_type,
    download_url,
    compression_type
  }
]
source_page_url
source_fqdn
download_url
version_hash_raw_data : { - each crawler has different fields here
  publication_date,
  download_url
}
version_hash
display_org
data_source
source_title
display_source
display_title
file_ext
is_revoked
access_timestamp
```

## DERIVED FROM FILENAME
 ``` 
  filename
  id
  group_s
  doc_type - from filename if not in metadata
  doc_num
  pages[] each page dict: filename - uses top level filename
  pages[] each page dict: id - uses top level filename
  paragraphs[] each paragraph dict: filename - uses top level filename
  paragraphs[] each paragraph dict: id - uses top level filename
  pop_score - uses top level filename as an id
  pagerank_r - uses top level filename as an id
```


## FROM METADATA
- some fields renamed with _s, _dt etc for the type
- some will have defaults using a static string or derived from filename if missing in metadata
```
  title - renamed from metadata doc_title
  doc_type
  file_ext_s
  file_ext_s
  display_doc_type_s
  display_title
  display_title_s
  display_org_s
  source_title_s
  display_source_s
  access_timestamp_dt
  publication_date_dt
  doc_name
  crawler_used_s
  source_fqdn_s
  source_page_url_s
  cac_login_required_b
  download_url_s
  version_hash_s
```

## FROM DOCUMENT TEXT PARSING
```
  par_count_i
  text
  raw_text
  page_count
  keyw_5 - added in handle_pages for some reason, uses page text, enrichment filters down
  pages[]
    type - statically added
    p_text
    p_raw_text
    p_name
    id - doc filename + page_num from iterating pages

  paragraphs[]
    type - statically added
    par_inc_count
    par_count_i
    page_num_i
    par_raw_text_t
    id - doc filename + par_count_i
```

## ENRICHMENT - DERIVED FROM PARSED (Text, Pages, Paragraphs)
```
  entities[] - paragraphs -> par_raw_text_t
  top_entities_t
  ref_list
  topics_s
  summary_30 - should use text, currently unused
  word_count
  sections[] - doc_type (may be from metadata) and text used to determine section parser
```

## ENRICHMENT - DERIVED FROM METADATA, ADDED FROM DB QUERY
```
  original_ingest_date - public.versioned_docs where json_metadata->>'doc_name'
  current_ingest_date - public.versioned_docs where json_metadata->>'doc_name'
  crawler_display_name - public.crawler_info where crawler = '{doc_dict['crawler_used_s']}'
```

## STATICALLY ADDED
```
  abbreviations_n
  init_date
  change_date
  author
  signature
  subject
  classification - !Exception is amhs parser calculates something here
  is_revoked_b
  pages[] type
  paragraphs[] type
```










