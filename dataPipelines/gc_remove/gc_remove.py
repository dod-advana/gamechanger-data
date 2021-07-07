from pathlib import Path
import json
from .config import Config
from dataPipelines.gc_db_utils.orch.models import Publication, VersionedDoc, CrawlerStatusEntry
from datetime import datetime as dt
import typing as t
from dataPipelines.gc_neo4j_publisher.neo4j_publisher import process_query

class RemoveFromCorpus:

    def __init__(self, input_json: t.Union[str,Path],
                 index_name: str,
                 load_archive_base_prefix: str,
                 bucket_name: str = Config.s3_bucket ):
        self.input_json = input_json
        self.index_name = index_name
        self.load_archive_base_prefix = load_archive_base_prefix
        self.bucket_name = bucket_name


    def remove_from_s3(self):


    def remove_from_postgres(self, doc: t.Dict):


    def remove_from_neo4j(self, doc: t.Dict):



    def remove_from_elasticsearch(self, doc: t.Dict):


    def remove(self):
        self.input_json
        for doc in self.input_json:
            doc_dict=json.loads(doc)
            self.remove_from_s3(doc_dict)
            self.remove_from_postgres(doc_dict)
            self.remove_from_neo4j(doc_dict)
            self.remove_from_elasticsearch(doc_dict)
