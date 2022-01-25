import json
import os
from datetime import datetime as dt
from pathlib import Path
from typing import Union

from sqlalchemy import func

from dataPipelines.gc_db_utils.orch.models import CrawlerStatusEntry, Publication, VersionedDoc
from dataPipelines.gc_neo4j_publisher.neo4j_publisher import process_query

from .config import Config


class CrawlerStatusTracker:

    def __init__(self, input_json: Union[str, os.PathLike]):
        self._input_json = input_json
        self._input_doc_names = set()
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

    def _revoke_documents(self, update_db: bool):
        with Config.connection_helper.orch_db_session_scope('rw') as session:

            # The following query should generate SQL to pull the publication and latest 
            # versioned document that is equivalent to:
            #
            # SELECT p.name, p.is_revoked, v.json_metadata
            # FROM publications AS p
            # JOIN versioned_docs AS v 
            # ON p.id = v.pub_id
            # JOIN (
            #     SELECT pub_id, MAX(batch_timestamp) AS max_timestamp
            #     FROM versioned_docs
            #     GROUP BY pub_id
            # ) AS vmax
            # ON v.pub_id = vmax.pub_id AND v.batch_timestamp = vmax.max_timestamp

            recent_subq = session.query(
                VersionedDoc.pub_id,
                func.max(VersionedDoc.batch_timestamp).label('max_timestamp')
            ).group_by(VersionedDoc.pub_id).subquery()

            publications_query = session.query(
                Publication.id,
                Publication.name,
                Publication.is_revoked,
                VersionedDoc.json_metadata
            ).join(
                VersionedDoc,
                Publication.id == VersionedDoc.pub_id
            ).join(
                recent_subq,
                (VersionedDoc.pub_id == recent_subq.c.pub_id) &
                (VersionedDoc.batch_timestamp == recent_subq.c.max_timestamp)
            )

            for doc_id, doc_name, doc_is_revoked, doc_json_metadata in publications_query.yield_per(10000):
                # work around the fact that some json data is incorrectly stored in the database json column as
                # json encoded strings -- i.e. `"{\"a\": \"b\"}"` instead of `{"a": "b"}`
                if isinstance(doc_json_metadata, str):
                    doc_json_metadata = json.loads(doc_json_metadata)

                crawler_used = doc_json_metadata['crawler_used']

                # not sure why this logic exists to ignore 'legislation_pubs' crawler...
                if crawler_used == 'legislation_pubs':
                    continue

                # skip doc if not in the crawler set we are interested in
                if crawler_used not in self._crawlers_downloaded:
                    continue

                meta_is_revoked = doc_json_metadata.get('is_revoked', False)

                # doc is considered revoked if marked as such by the crawler ...
                if meta_is_revoked:
                    updated_is_revoked = True
                else:  # ... otherwise doc is considered revoked if missing from the new input document set
                    updated_is_revoked = doc_name not in self._input_doc_names

                if updated_is_revoked != doc_is_revoked:
                    print(f'Publication {doc_name} is {"now" if updated_is_revoked else "no longer"} revoked')
                    if update_db:
                        print(f'Updating DB to reflect {doc_name} is{" " if updated_is_revoked else " not "}revoked')
                        session.query(Publication).filter_by(id=doc_id).update({'is_revoked': updated_is_revoked})

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
