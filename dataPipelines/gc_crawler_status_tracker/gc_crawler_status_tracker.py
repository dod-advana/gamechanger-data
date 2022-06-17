import json
import os
from contextlib import ExitStack
from datetime import datetime as dt
from pathlib import Path
from typing import Union

from sqlalchemy import case, cast, func, JSON

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
            docs = self._fetch_docs(session=session)

            for doc in docs:
                crawler_used = doc.json_metadata['crawler_used']

                # not sure why this logic exists to ignore 'legislation_pubs' crawler...
                if crawler_used == 'legislation_pubs':
                    continue

                # skip doc if not in the crawler set we are interested in
                if crawler_used not in self._crawlers_downloaded:
                    continue

                meta_is_revoked = doc.json_metadata.get('is_revoked', False)

                # doc is considered revoked if marked as such by the crawler ...
                if meta_is_revoked:
                    now_is_revoked = True
                else:  # ... otherwise doc is considered revoked if missing from the new input document set
                    now_is_revoked = doc.name not in self._input_doc_names

                if now_is_revoked != doc.is_revoked:
                    print(f'Publication {doc.name} is {"now" if now_is_revoked else "no longer"} revoked')
                    if update_db:
                        print(f'Updating DB to reflect {doc.name} is{" " if now_is_revoked else " not "}revoked')
                        session.query(Publication).filter_by(id=doc.id).update({'is_revoked': now_is_revoked})

    def _fetch_docs(self, *, session=None):
        # if not provided with an open session open a new session; the use of an ExitStack context manager to
        # optionally close only a new session could be cleaned up with the nullcontext when moving to Python 3.7+
        exit_stack = ExitStack()
        if not session:
            session_scope = Config.connection_helper.orch_db_session_scope('ro')
            session = exit_stack.enter_context(session_scope)

        with exit_stack:          
            # The following query should generate SQL to pull the publication and latest
            # versioned document which is equivalent to:
            #
            # SELECT p.id, p.name, p.is_revoked, v.filename, v.json_metadata
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
            ).group_by(
                VersionedDoc.pub_id
            ).subquery()

            return session.query(
                Publication.id,
                Publication.name,
                Publication.is_revoked,
                VersionedDoc.filename,
                # work around the fact that some json data is incorrectly stored in the json_metadata column as
                # json encoded strings -- i.e. `"{\"a\": \"b\"}"` instead of `{"a": "b"}` -- by conditionally
                # extracting the string as text and re-parsing as json when a string is stored in the column
                case({'string': cast(VersionedDoc.json_metadata.op('#>>')('{}'), JSON)},
                     else_=VersionedDoc.json_metadata,
                     value=func.json_typeof(VersionedDoc.json_metadata)).label('json_metadata')
            ).join(
                VersionedDoc,
                Publication.id == VersionedDoc.pub_id
            ).join(
                recent_subq,
                ((VersionedDoc.pub_id == recent_subq.c.pub_id)
                 & (VersionedDoc.batch_timestamp == recent_subq.c.max_timestamp))
            ).all()

    def _update_revocations_es(self, docs, index_name:str):
        print(f'Updating Elasticsearch revocation statuses')

        update_body = {
                    "query": {
                        "bool": {
                            "must": [
                                {
                                    "terms": {
                                        "filename": []
                                    }
                                },
                                {
                                    "term": {
                                        "crawler_used_s": ''
                                    }
                                }
                            ]
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
        

        crawler_batched_filenames = {}

        for doc in docs:
            crawler = doc.json_metadata['crawler_used']
            if crawler in crawler_batched_filenames:
                if doc.is_revoked:
                    crawler_batched_filenames[crawler]['revoked'].append(doc.filename)
                else:
                    crawler_batched_filenames[crawler]['unrevoked'].append(doc.filename)
            else:
                if doc.is_revoked:
                    crawler_batched_filenames[crawler]['revoked'] = [doc.filename]
                    crawler_batched_filenames[crawler]['unrevoked'] = []
                else:
                    crawler_batched_filenames[crawler]['revoked'] = []
                    crawler_batched_filenames[crawler]['unrevoked'] = [doc.filename]

        max_updates = 65536


        for crawler in crawler_batched_filenames:
            revoked_filenames = crawler_batched_filenames[crawler]['revoked']
            unrevoked_filenames = crawler_batched_filenames[crawler]['unrevoked']
            # Update revoked files
            # If there are more than the max updates we can make in one update_by_query, loop through and batch process them
            if len(revoked_filenames) > max_updates:
                for i in range(0, len(revoked_filenames), max_updates):
                    update_body['query']['bool']['must'][0]['terms']['filename'] = revoked_filenames[0+i:max_updates+i]
                    Config.connection_helper.es_client.update_by_query(index=index_name, body=update_body)
            else:
                update_body['query']['bool']['must'][0]['terms']['filename'] = revoked_filenames
                Config.connection_helper.es_client.update_by_query(index=index_name, body=update_body)
            
            # Update unrevoked files
            # Same as above chunk but for unrevoked files
            update_body['script']['params']['is_revoked_b'] = False
            if len(unrevoked_filenames) > max_updates:
                for i in range(0, len(unrevoked_filenames), max_updates):
                    update_body['query']['bool']['must'][0]['terms']['filename'] = unrevoked_filenames[0+i:max_updates+i]
                    Config.connection_helper.es_client.update_by_query(index=index_name, body=update_body)
            else:
                update_body['query']['bool']['must'][0]['terms']['filename'] = unrevoked_filenames
                Config.connection_helper.es_client.update_by_query(index=index_name, body=update_body)
    
        
    def _update_revocations_neo4j(self, docs):
        print(f'Updating Neo4j revocation statuses')
        for doc in docs:
            process_query(
                'MATCH (a:Document { name: $name, crawler_used_s: $crawler_used })'
                'SET a.is_revoked_b = $is_revoked',
                name=doc.name,
                crawler_used=doc.json_metadata['crawler_used'],
                is_revoked=doc.is_revoked,
            )

    def handle_revocations(self, index_name: str, update_es: bool, update_db: bool, update_neo4j: bool):
        if not self._dbs_initiated:
            Config.connection_helper.init_dbs()
            self._dbs_initiated = True

        if self._input_json and not self._crawlers_downloaded:
            self._set_input_lists()

        if self._input_json:
            self._revoke_documents(update_db=update_db)

        if update_es or update_neo4j:
            docs = self._fetch_docs()

        if update_es:
            self._update_revocations_es(docs, index_name=index_name)

        if update_neo4j:
            self._update_revocations_neo4j(docs)
