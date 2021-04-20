from dataPipelines.gc_crawler.data_model import Document, DownloadableItem


def test_instantiating_doc_object():
    """Testing syntax for creating a Document instance"""

    versioning_fields = dict(edition=6, series=10, pub_name="some_pub")

    pub = Document(
        doc_name="Some Pub, 3rd Edition",
        doc_title="Some Pub, 3rd Edition",
        doc_type="some_doc_type",
        doc_num="1",
        source_page_url="https://example.gov/our_pubs.html",
        version_hash_raw_data=versioning_fields,
        cac_login_required=False,
        publication_date=None,
        crawler_used='dummy',
        downloadable_items=[
            DownloadableItem(
                doc_type='pdf',
                web_url='https://example.local/pub_dist/some_pub_20200404_pdf.zip',
                compression_type='zip',
            ),
            DownloadableItem(
                doc_type='xml',
                web_url='https://example.local/pub_dist/some_pub_20200404_xml.zip',
                compression_type='zip',
            ),
        ],
    )

    assert pub
