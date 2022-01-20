import json
import os
from datetime import datetime as dt
from pathlib import Path
from typing import Union

from dataPipelines.gc_db_utils.orch.models import CrawlerStatusEntry, Publication, VersionedDoc
from dataPipelines.gc_neo4j_publisher.neo4j_publisher import process_query

from .config import Config


class CrawlerStatusTracker:

    def __init__(self, input_json: Union[str, os.PathLike]):
        self._input_json = input_json
        self._input_doc_names = set()
        self._input_docs_revoked_by_crawler = set()
        self._crawlers_downloaded = set()
        self._dbs_initiated = False

    def _set_input_lists(self):
        input_json_path = Path(self._input_json)
        with input_json_path.open(mode="r") as f:
            for json_str in f:
                if json_str.isspace():
                    continue
                else:
                    try:
                        j_data = json.loads(json_str)
                    except json.decoder.JSONDecodeError:
                        print("Encountered JSON decode error while parsing crawler output.")
                        continue
                    self._input_doc_names.add(j_data["doc_name"])
                    self._crawlers_downloaded.add(j_data["crawler_used"])
                    if j_data.get("is_revoked", False):
                        self._input_docs_revoked_by_crawler.add(j_data["doc_name"])
                    
    def update_crawler_status(self, status: str, timestamp:dt.timestamp, update_db:bool):
        if not self._dbs_initiated:
            Config.connection_helper.init_dbs()
            self._dbs_initiated = True
        if not self._crawlers_downloaded:
            self._set_input_lists()
        formatted_timestamp = dt.strftime(timestamp, '%Y-%m-%dT%H:%M:%S')

        if update_db:
            with Config.connection_helper.orch_db_session_scope('rw') as session:
                for crawler in self._crawlers_downloaded:
                    status_entry = CrawlerStatusEntry.create(status=status,
                                                             crawler_name=crawler,
                                                             datetime=formatted_timestamp)
                    session.add(status_entry)

    def _revoke_documents(self, update_db:bool):
        with Config.connection_helper.orch_db_session_scope('rw') as session:
            db_revoked = session.query(Publication.name, VersionedDoc.json_metadata). \
                join(VersionedDoc, Publication.name == VersionedDoc.name). \
                filter(Publication.is_revoked == True).all()
            db_current = session.query(Publication.name, VersionedDoc.json_metadata). \
                join(VersionedDoc, Publication.name == VersionedDoc.name). \
                filter(Publication.is_revoked == False).all()
            # extract crawler_used from metadata and de-dup the list
            db_revoked_list = list(
                set(
                    [(name, json.loads(j)["crawler_used"])
                        if isinstance(j,str)
                        else (name,j["crawler_used"])
                        for (name, j) in db_revoked]))
            db_current_list = list(
                set(
                    [(name, json.loads(j)["crawler_used"])
                     if isinstance(j,str) else (name, j["crawler_used"])
                     for (name, j) in db_current]))
            for (doc, crawler) in db_current_list:
                if (
                    # we revoke if the document is now missing in the new ingest set ...
                    (
                        doc not in self._input_doc_names
                        and crawler in self._crawlers_downloaded
                        and crawler != "legislation_pubs"   # ??
                    )
                    # ... or if the document was explicitely set as revoked by the crawler
                    or doc in self._input_docs_revoked_by_crawler
                ):
                    print("Publication " + doc + " is now revoked")
                    if update_db:
                        print("Updating DB to reflect " + doc + " is revoked")
                        pub = session.query(Publication).filter_by(name=doc).one()
                        pub.is_revoked = True
            for (doc, crawler) in db_revoked_list:
                # anything present in the new ingest set (that was not set as revoked by the crawler)
                # will now be un-revoked
                if doc in self._input_doc_names and crawler in self._crawlers_downloaded:
                    print("Publication " + doc + " is no longer revoked")
                    if update_db:
                        print("Updating DB to reflect " + doc + " is no longer revoked")
                        pub = session.query(Publication).filter_by(name=doc).one()
                        pub.is_revoked = False

    def _get_revoked_documents(self):
        with Config.connection_helper.orch_db_session_scope('rw') as session:
            db_revoked = session.query(Publication.name).\
                filter(Publication.is_revoked == True).all()
            db_revocations =list(set([name for (name,) in db_revoked]))
            return db_revocations

    def _get_non_revoked_documents(self):
        with Config.connection_helper.orch_db_session_scope('rw') as session:
            db_non_revoked = session.query(Publication.name).\
                filter(Publication.is_revoked == False).all()
            db_non_revocations =list(set([name for (name,) in db_non_revoked]))
            return db_non_revocations

# TODO fix "PDF" addition here. Add html
    def _update_revocations_es(self, doc_name_list, index_name:str):

        for doc in doc_name_list:
            print(
                "Updating Elasticsearch to reflect " + doc + " is revocation status has changed to " + str(True))
            update_body = {
                "query": {
                    "term": {
                        "filename": doc + ".pdf"
                    }
                },
                "script": {
                    "source": "ctx._source.is_revoked_b = params.is_revoked_b",
                    "lang": "painless",
                    "params": {
                        "is_revoked_b": True
                    }
                }
            }
            Config.connection_helper.es_client.update_by_query(index=index_name, body=update_body)

    def _update_revocations_neo4j(self, revoked_docs, non_revoked_docs):
        for doc in revoked_docs:
            process_query(
                "MERGE (a:Document {name: \"" + doc + "\"}) SET a.is_revoked_b = true"
            )
        for doc in non_revoked_docs:
            process_query(
                "MERGE (a:Document {name: \"" + doc + "\"}) SET a.is_revoked_b = false"
            )

    def handle_revocations(self, index_name: str, update_es: bool, update_db: bool, update_neo4j: bool):
        if not self._dbs_initiated:
            Config.connection_helper.init_dbs()
            self._dbs_initiated = True

        if not self._crawlers_downloaded and self._input_json:
            self._set_input_lists()

        if self._input_json and Path(self._input_json).resolve():
            self._revoke_documents(update_db=update_db)

        docs_to_be_revoked = self._get_revoked_documents()
        if update_es:
            self._update_revocations_es(doc_name_list=docs_to_be_revoked, index_name=index_name)

        non_revoked_docs = self._get_non_revoked_documents()
        if update_neo4j:
            self._update_revocations_neo4j(revoked_docs=docs_to_be_revoked, non_revoked_docs=non_revoked_docs)
