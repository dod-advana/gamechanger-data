from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from pathlib import Path
import typing as t
from elasticsearch import ElasticsearchException, TransportError
import time
import traceback
import hashlib
import json


class EDSConfiguredElasticsearchPublisher(ConfiguredElasticsearchPublisher):

    def __init__(self, ingest_dir: t.Union[str, Path], index_name: str,
                 mapping_file: t.Optional[t.Union[str, Path]] = None, alias: t.Optional[str] = None):

        super().__init__(ingest_dir=ingest_dir, index_name=index_name, mapping_file=mapping_file, alias=alias)

    def index_json(self, path_json: str, record_id: str) -> bool:

        record_id_encode = hashlib.sha256(record_id.encode())
        with open(path_json, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            if 'text' in json_data:
                del json_data['text']
            if 'paragraphs' in json_data:
                del json_data['paragraphs']
            if 'raw_text' in json_data:
                del json_data['raw_text']
            if 'pages' in json_data:
                pages = json_data['pages']
                for page in pages:
                    if 'p_text' in page:
                        del page['p_text']

            is_suc = False
            counter = 0
            error_message = None
            while not is_suc and counter < 10:
                try:
                    error_message = None
                    response = self.es.index(index=self.index_name, id=record_id_encode.hexdigest(), body=json_data)
                    return True
                except TransportError as te:
                    error_message = f"\nFailed -- Unexpected Elasticsearch Transport Exception: {path_json} {record_id} {record_id_encode.hexdigest()}\n"
                    time.sleep(2)
                    counter = counter + 1
                except ElasticsearchException as ee:
                    error_message = f"\nFailed -- Unexpected Elasticsearch Exception: {path_json} {record_id} {record_id_encode.hexdigest()}\n"
                    time.sleep(2)
                    print(ee)
                    counter = counter + 1
            if error_message is not None:
                print(error_message)

            return is_suc

    def insert_record(self, json_record: dict, id_record: str):
        is_suc = False
        counter = 0
        while not is_suc and counter < 10:
            try:
                response = self.es.index(index=self.index_name, id=id_record, body=json_record)
                is_suc = True
            except TransportError as exc:
                counter = counter + 1
                time.sleep(2)
                if counter == 10:
                    traceback.print_exc()
                is_suc = False
        if counter >= 10:
            print(f"Failed to audit record {id_record}")

    def get_by_id(self, id_record: str):
        response = self.es.get(index=self.index_name, id=id_record)
        return response['_source']

    def search(self, index: str, body: str):
        response = self.es.search(index=index, body=body)
        return response

    def count(self, index: str, body: str):
        response = self.es.count(index=index, body=body)
        return response

    def exists(self, id: str) -> bool:
        return self.es.exists(index=self.index_name, id=id)

    def ping(self):
        return self.es.ping