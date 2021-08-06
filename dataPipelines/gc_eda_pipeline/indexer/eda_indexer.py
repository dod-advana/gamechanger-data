from dataPipelines.gc_elasticsearch_publisher.gc_elasticsearch_publisher import ConfiguredElasticsearchPublisher
from pathlib import Path
import typing as t
from elasticsearch import ElasticsearchException, TransportError, helpers
import time
import traceback
import hashlib
import json
import re
import os


class EDSConfiguredElasticsearchPublisher(ConfiguredElasticsearchPublisher):

    def __init__(self, ingest_dir: t.Union[str, Path], index_name: str,
                 mapping_file: t.Optional[t.Union[str, Path]] = None, alias: t.Optional[str] = None):

        super().__init__(ingest_dir=ingest_dir, index_name=index_name, mapping_file=mapping_file, alias=alias)

    def get_jdicts(self):
        for f in Path(self.ingest_dir).glob("*.json"):
            filename = re.sub('\.json', '', os.path.basename(f))
            # print(f"ES inserting {filename}")
            with open(f, 'r', encoding="utf-8") as file:
                data = file.read()
                json_data = json.loads(data)
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
                yield json_data

    def index_jsons(self):
        print("Starting to indexing json files")
        count_success, error_count = 0, 0
        try:
            for success, info in helpers.parallel_bulk(
                    client=self.es,
                    actions=self.get_actions(self.get_jdicts()),
                    thread_count=90,
                    chunk_size=1000,
                    raise_on_exception=False,
                    queue_size=100
            ):
                if not success:
                    error_count += 1
                    print('Doc failed', info)
                else:
                    count_success += 1
        except UnicodeEncodeError as e:
            print(e)
            print("------------------  Failed to index files. --------------------------")

    def index_data(self, data_json: dict, record_id: str):
        record_id_encode = hashlib.sha256(record_id.encode()).hexdigest()
        # print("___-------------------------")
        # print(f"data_json  {type(data_json)}")
        # print("___-------------------------")
        # data_json["_id"] = record_id_encode
        json_data = data_json
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
                response = self.es.index(index=self.index_name, id=record_id_encode, body=json_data)
                return True
            except TransportError as te:
                print(te)
                error_message = f"\nFailed -- Unexpected Elasticsearch Transport Exception: {record_id}\n"
                time.sleep(1)
                counter = counter + 1
            except ElasticsearchException as ee:
                error_message = f"\nFailed -- Unexpected Elasticsearch Exception:  {record_id} \n"
                time.sleep(1)
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

    # def search_scroll(self, index: str, body: str):
    #     response = self.es.search(index=index, body=body, scro)

    def count(self, index: str, body: str):
        response = self.es.count(index=index, body=body)
        return response

    def exists(self, id: str) -> bool:
        return self.es.exists(index=self.index_name, id=id)

    def ping(self):
        return self.es.ping

    def update_settings(self):
        a = self.es.indices.get_settings(index=self.index_name)
        print(a)

    def client_info(self):
        return self.es.info()

    def es(self):
        return self.es()


