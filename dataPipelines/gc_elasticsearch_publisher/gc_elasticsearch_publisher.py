import os
from elasticsearch import helpers, Elasticsearch,ElasticsearchException,TransportError
from pathlib import Path
import json
import hashlib
import re
import traceback
from .config import Config
import typing as t
from configuration import RENDERED_DIR
import glob



class ElasticsearchPublisher:

    def __init__(self, ingest_dir, index_name, host, port, mapping_file, alias, username, password, environment):
        self.ingest_dir = ingest_dir
        self.index_name = index_name
        self.host = host
        self.port = port
        self.mapping_file = mapping_file
        self.alias = alias
        if "docker" == environment:
            self.es = Elasticsearch([{'host': self.host, 'port': self.port, 'http_compress': True, 'timeout': 20000}])
        elif "dev" == environment:
            self.es = Elasticsearch([{'host': self.host, 'port': self.port, 'http_compress': True, 'timeout': 20000}],
                                    use_ssl=True)
        else:
            self.es = Elasticsearch([{'host': self.host, 'port': self.port, 'http_compress': True, 'timeout': 20000}],
                                    http_auth=(str(username), str(password)), use_ssl=True)

    def get_jdicts(self):
        # for f in Path(self.ingest_dir).glob("*.json"):
        for f in glob.glob(pathname=self.ingest_dir + "/**/*.json", recursive=True):
            filename = re.sub('\.json', '', os.path.basename(f))
            # record_id = uuid.uuid1()
            record_id = hashlib.sha256(filename.encode())
            with open(f, 'r', encoding="utf-8") as file:
                data = file.read()
                json_data = json.loads(data)
                if 'text' in json_data:
                    del json_data['text']
                if 'paragraphs' in json_data:
                    del  json_data['paragraphs']
                if 'raw_text' in json_data:
                    del json_data['raw_text']
                if 'pages' in json_data:
                    pages = json_data['pages']
                    for page in pages:
                        if 'p_text' in page:
                            del page['p_text']
                json_data['_id'] = record_id.hexdigest()
                # json_data['_id'] = record_id
                yield json_data

    def get_actions(self, json_dicts):
        for json_dict in json_dicts:
            yield dict(
                _op_type='index',
                _index=self.index_name,
                **json_dict
            )

    def index_json(self, path_json: str, record_id: str) -> bool:
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
            try:
                response = self.es.index(index=self.index_name, id=record_id.hexdigest(), body=json_data)
                return True
            except TransportError as te:
                print(f"Failed -- Unexpected Elasticsearch Transport Exception: {path_json}  {record_id.hexdigest()}")
                print(te.error)
                print(te.info)
                return False
            except ElasticsearchException as ee:
                print(ee)
                return False


    def index_jsons(self):
        print("Starting to indexing json files")

        count_success, error_count = 0, 0
        try:
            for success, info in helpers.parallel_bulk(
                client=self.es,
                actions=self.get_actions(self.get_jdicts()),
                thread_count=10,
                chunk_size=1,
                raise_on_exception=False,
                queue_size=1
            ):
                if not success:
                    error_count += 1
                    print('Doc failed', info)
                else:
                    count_success += 1
        except UnicodeEncodeError as e:
            print(e)
            print("------------------  Failed to index files. --------------------------")

        # results = queue.deque(load_gen, maxlen=0)
        print("Number of Successfully index: " + str(count_success))
        print("Number of Failed index: " + str(error_count))
        print("Finished indexing json files")

    def create_index(self):
        print("Starting to create new Schema")
        with open(self.mapping_file, 'r') as file:
            mapping_file = file.read()
        if not self.es.indices.exists(self.index_name):
            response = self.es.indices.create(index=self.index_name, body=mapping_file)
            if 'acknowledged' in response:
                if response['acknowledged']:
                    print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])
            elif 'error' in response:
                print("ERROR:", response['error']['root_cause'])
                print("TYPE:", response['error']['type'])
            print('\nresponse:', response)
        else:
            print("Index already exist")

    def update_alias(self):
        print("Update Alias")
        try:
            if self.es.indices.exists_alias(name=self.alias):
                print("******** Delete old alias ******** ")
                for key in self.es.indices.get_alias(name=self.alias):
                    for alias in self.es.indices.get_alias(name=self.alias).get(key).get('aliases'):
                        self.es.indices.delete_alias(index=key, name=alias, ignore=[404])
            response = self.es.indices.put_alias(index=self.index_name, name=self.alias)
            print(response)
        except Exception:
            traceback.print_exc()

    def delete_record(self, records: list):
        if self.es.indices.exists(self.index_name):
            for record in records:

                filename = re.sub('.xml.json|.json', '', record.strip())
                # record_id = hashlib.md5(filename.encode())
                record_id = hashlib.sha256(filename.encode())
                if self.es.exists(self.index_name, id=record_id.hexdigest()):
                    self.es.delete(self.index_name, id=record_id.hexdigest())
                    print("Deleted from ES: " + record_id.hexdigest())
                else:
                    print("Missing: " + record_id.hexdigest() + "  " + filename)

    def insert_record(self, json_record: dict, id: str):
        try:
            response = self.es.index(index=self.index_name, id=id, body=json_record)
            # print(f"Insert Record {id} into ES")
        except Exception:
            traceback.print_exc()

    def get_by_id(self, id: str):
        response = self.es.get(index=self.index_name, id=id)
        return response['_source']

    def exists(self, id: str) -> bool:
        return self.es.exists(index=self.index_name, id=id)

    def ping(self):
        return self.es.ping

class ConfiguredElasticsearchPublisher(ElasticsearchPublisher):
    """ES Publisher that leverages repo configuration"""

    def __init__(self, ingest_dir: t.Union[str, Path], index_name: str, mapping_file: t.Optional[t.Union[str, Path]] = None, alias: t.Optional[str] = None):

        ingest_dir = str(Path(ingest_dir).resolve())
        mapping_file = str(Path(mapping_file).resolve()) if mapping_file else None

        super().__init__(
            ingest_dir=ingest_dir,
            index_name=index_name,
            host="localhost",
            port="9999",
            mapping_file=mapping_file,
            alias=alias,
            username="pass",
            password="pass",
            environment="local"
        )

        self.ingest_dir = ingest_dir
        self.index_name = index_name
        if not mapping_file:
            self.mapping_file = str(os.path.join(RENDERED_DIR, "elasticsearch", "index.json"))
        else:
            self.mapping_file = mapping_file
        self.alias = alias
        self.es = Config.connection_helper.es_client
