import os
from elasticsearch import helpers, Elasticsearch
from pathlib import Path
import json
import hashlib
import re
import traceback
from .config import Config
import json
import typing as t
from configuration import RENDERED_DIR
import pandas as pd
from datetime import datetime

def clean_string(string):

    return " ".join(
        [i.lstrip("\n").strip().lstrip().replace('"',"'").replace("'", "\'")
         for i in string.split(" ")]
    )


class ElasticsearchPublisher:
    def __init__(
        self,
        ingest_dir,
        index_name,
        host,
        port,
        mapping_file,
        alias,
        username,
        password,
        environment,
    ):
        self.ingest_dir = ingest_dir
        self.index_name = index_name
        self.host = host
        self.port = port
        self.mapping_file = mapping_file
        self.alias = alias
        if "docker" == environment:
            self.es = Elasticsearch(
                [
                    {
                        "host": self.host,
                        "port": self.port,
                        "http_compress": True,
                        "timeout": 20000,
                    }
                ]
            )
        elif "dev" == environment:
            self.es = Elasticsearch(
                [
                    {
                        "host": self.host,
                        "port": self.port,
                        "http_compress": True,
                        "timeout": 20000,
                    }
                ],
                use_ssl=True,
            )
        else:
            self.es = Elasticsearch(
                [
                    {
                        "host": self.host,
                        "port": self.port,
                        "http_compress": True,
                        "timeout": 20000,
                    }
                ],
                http_auth=(str(username), str(password)),
                use_ssl=True,
            )

    def get_jdicts(self):
        for f in Path(self.ingest_dir).glob("*.json"):
            filename = re.sub("\.json", "", os.path.basename(f))
            print(f"ES inserting {filename}")
            # record_id = uuid.uuid1()
            record_id = hashlib.sha256(filename.encode())
            with open(f, "r", encoding="utf-8") as file:
                data = file.read()
                json_data = json.loads(data)
                if "text" in json_data:
                    del json_data["text"]
                if "pages" in json_data:
                    del json_data["pages"]
                if "raw_text" in json_data:
                    del json_data["raw_text"]
                json_data["_id"] = record_id.hexdigest()
                # json_data['_id'] = record_id
                yield json_data

    def get_actions(self, json_dicts):
        for json_dict in json_dicts:
            yield dict(_op_type="index", _index=self.index_name, **json_dict)

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
                queue_size=1,
            ):
                if not success:
                    error_count += 1
                    print("Doc failed", info)
                else:
                    count_success += 1
        except UnicodeEncodeError as e:
            print(e)
            print(
                "------------------  Failed to index files. --------------------------"
            )

        # results = queue.deque(load_gen, maxlen=0)
        print("Number of Successfully index: " + str(count_success))
        print("Number of Failed index: " + str(error_count))
        print("Finished indexing json files")

    def create_index(self):
        print("Starting to create new Schema")
        # TODO: Change how ES config is handled to support multiple index types avoid the need for config init
        index_config=json.loads(Path(self.mapping_file).read_text())
        if 'index' in index_config:
            index_config=index_config['index']

        if not self.es.indices.exists(self.index_name):
            response = self.es.indices.create(
                index=self.index_name,
                body=index_config
            )
            if "acknowledged" in response:
                if response["acknowledged"]:
                    print("INDEX MAPPING SUCCESS FOR INDEX:",
                          response["index"])
            elif "error" in response:
                print("ERROR:", response["error"]["root_cause"])
                print("TYPE:", response["error"]["type"])
            print("\nresponse:", response)
        else:
            print("Index already exist")

    def update_alias(self):
        print("Update Alias")
        try:
            if self.es.indices.exists_alias(name=self.alias):
                print("******** Delete old alias ******** ")
                for key in self.es.indices.get_alias(name=self.alias):
                    for alias in (
                        self.es.indices.get_alias(name=self.alias)
                        .get(key)
                        .get("aliases")
                    ):
                        self.es.indices.delete_alias(
                            index=key, name=alias, ignore=[404]
                        )
            response = self.es.indices.put_alias(
                index=self.index_name, name=self.alias)
            print(response)
        except Exception:
            traceback.print_exc()

    def delete_record(self, records: list):
        if self.es.indices.exists(self.index_name):
            for record in records:

                filename = re.sub(".xml.json|.json", "", record.strip())
                # record_id = hashlib.md5(filename.encode())
                record_id = hashlib.sha256(filename.encode())
                if self.es.exists(self.index_name, id=record_id.hexdigest()):
                    self.es.delete(self.index_name, id=record_id.hexdigest())
                    print("Deleted from ES: " + record_id.hexdigest())
                else:
                    print("Missing: " + record_id.hexdigest() + "  " + filename)


class ConfiguredElasticsearchPublisher(ElasticsearchPublisher):
    """ES Publisher that leverages repo configuration"""

    def __init__(
        self,
        ingest_dir: t.Union[str, Path],
        index_name: str,
        mapping_file: t.Optional[t.Union[str, Path]] = None,
        alias: t.Optional[str] = None,
    ):
        if ingest_dir:
            ingest_dir = str(Path(ingest_dir).resolve())
        mapping_file = str(Path(mapping_file).resolve()
                           ) if mapping_file else None

        super().__init__(
            ingest_dir=ingest_dir,
            index_name=index_name,
            host="localhost",
            port="9999",
            mapping_file=mapping_file,
            alias=alias,
            username="pass",
            password="pass",
            environment="local",
        )

        self.ingest_dir = ingest_dir
        self.index_name = index_name
        if not mapping_file:
            self.mapping_file = str(
                os.path.join(RENDERED_DIR, "elasticsearch", "index.json")
            )
        else:
            self.mapping_file = mapping_file
        self.alias = alias
        self.es = Config.connection_helper.es_client


class ConfiguredEntityPublisher(ConfiguredElasticsearchPublisher):
    """ES Publisher that leverages repo configuration"""

    def __init__(
        self,
        entity_csv_path: t.Union[str, Path],
        index_name: str,
        mapping_file: t.Optional[t.Union[str, Path]] = None,
        alias: t.Optional[str] = None,
    ):

        entity_csv_path = str(Path(entity_csv_path).resolve())
        mapping_file = str(Path(mapping_file).resolve()
                           ) if mapping_file else None

        super().__init__(
            ingest_dir="/data/",
            index_name=index_name,
            mapping_file=mapping_file,
            alias=alias,
        )

        self.entity_csv_path = entity_csv_path
        self.agencies = self.read_agencies()

    def read_agencies(self):

        agencies = pd.read_csv(self.entity_csv_path)
        agencies.fillna("", inplace=True)

        keep_cols = [
            "entity_name",
            "Website",
            "Address",
            "Government_Branch",
            "Parent_Agency",
            "Related_Agency",
            "information"
        ]

        for i in keep_cols:
            agencies[i] = agencies[i].apply(lambda x: clean_string(x))

        agencies["Agency_Aliases"] = agencies["Agency_Aliases"].apply(
            lambda x: x.split(";")
        )

        return agencies

    def get_docs(self):

        docs = []
        for i in self.agencies.index:
            mydict = {}
            mydict["name"] = self.agencies.loc[i, "entity_name"]
            mydict["website"] = self.agencies.loc[i, "Website"]
            mydict["address"] = self.agencies.loc[i, "Address"]
            mydict["government_branch"] = self.agencies.loc[i, "Government_Branch"]
            mydict["parent_agency"] = self.agencies.loc[i, "Parent_Agency"]
            mydict["related_agency"] = self.agencies.loc[i, "Related_Agency"]
            mydict["entity_type"] = self.agencies.loc[i, "entity_type"]
            mydict["crawlers"] = self.agencies.loc[i, "crawlers"]
            mydict["num_mentions"] = self.agencies.loc[i, "num_mentions"]
            mydict["aliases"] = [
                {"name": x} for x in self.agencies.loc[i, "Agency_Aliases"]
            ]
            mydict["information"] = self.agencies.loc[i, "information"]
            mydict["information_source"] = self.agencies.loc[i, "information_source"]
            mydict["information_retrieved"] = self.agencies.loc[i, "information_retrieved"]
            header = {"_index": self.index_name, "_source": mydict}
            docs.append(header)

        return docs

    def index_jsons(self):
        print("Starting to index entities")

        count_success, error_count = 0, 0
        try:
            for success, info in helpers.parallel_bulk(
                client=self.es,
                actions=self.get_docs(),
                thread_count=10,
                chunk_size=1,
                raise_on_exception=False,
                queue_size=1,
            ):
                if not success:
                    error_count += 1
                    print("Doc failed", info)
                else:
                    count_success += 1
        except UnicodeEncodeError as e:
            print(e)
            print(
                "------------------  Failed to index files. --------------------------"
            )

        # results = queue.deque(load_gen, maxlen=0)
        print("Number of Successfully index: " + str(count_success))
        print("Number of Failed index: " + str(error_count))
        print("Finished indexing json files")
