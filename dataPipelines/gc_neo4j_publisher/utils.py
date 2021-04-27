import typing as t
from .config import Config
import multiprocessing as mp

from tqdm import tqdm
from .neo4j_publisher import Neo4jPublisher
import os
import sys
import math
from pathlib import Path
import pandas as pd
from dataPipelines.gc_neo4j_publisher import wiki_utils as wu
import json


def only_write_infobox(csv_file_path, infobox_dir):
    # write out infobox.json in common/data/infobox
    if not os.path.exists(infobox_dir):
        os.makedirs(infobox_dir)

    # read in csv in common/data/infobox
    if not os.path.exists(csv_file_path):
        print("ERROR: csv file {0} does not exist!".format(csv_file_path))
        return

    ent_file_untrimmed = pd.read_csv(csv_file_path, na_filter=False)
    ent_file = ent_file_untrimmed.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    ents = list(set(ent_file['Tokens'].tolist()))

    print('Reading in {0} files'.format(len(ents)))

    for i, ent in enumerate(ents):
        if i % 10 == 0:
            print('Reading in file {0} of {1}'.format(i, len(ents)))
        info = wu.get_infobox_info(ent)
        # write out json
        filename = infobox_dir + '/' + ent + '_infobox.json'
        with open(filename, 'w') as f:
            json.dump(info, f)

    print('Done')


class Neo4jJobManager:
    def __init__(self):
        """Manages neo4j update job"""
        pass

    @staticmethod
    def listener(q: mp.Queue, total: int) -> None:
        pbar = tqdm(total=total)
        for item in iter(q.get, None):
            pbar.update()

    @staticmethod
    def process_files(files: t.List[str], file_dir: str, q: mp.Queue, publisher: Neo4jPublisher) -> None:
        publisher.process_dir(files, file_dir, q)

    @staticmethod
    def get_chunks(lst: t.List[t.Any], n: int) -> t.Iterable[t.List[t.Any]]:
        """Yield <n> successive chunks from the <lst>."""
        if n >= len(lst):
            yield from ([e] for e in lst)

        max_chunk_size = math.ceil(len(lst) / n)
        min_chunk_size = math.floor(len(lst) / n)

        chunk_start = 0
        chunk_end = min_chunk_size

        for i in range(n):
            yield lst[chunk_start:chunk_end]
            chunk_start = chunk_end
            chunk_end = chunk_start + (max_chunk_size if i == n - 2 else min_chunk_size)

    def run_update(self, source: t.Union[str, Path],
                   clear: bool,
                   max_threads: int,
                   scrape_wiki: bool,
                   without_web_scraping: bool,
                   infobox_dir: t.Union[str, Path]) -> None:
        """Run Neo4j Update Job
        :param source: Path to source directory
        :param clear: Clear out all old entities first (care, can stall db if not enough RAM)
        :param max_threads: max threads to use
        :param scrape_wiki: whether to scrape the wiki when running the update
        :param without_web_scraping: designates if being run in environment without internet access
        :param infobox_dir: where the infobox jsons are saved if no web scraping
        """
        source = str(Path(source).resolve())
        max_theoretical_threads = mp.cpu_count() - 1 if mp.cpu_count() - 1 > 0 else 1
        max_threads = max_theoretical_threads if max_threads <= 0 else max_threads

        file_dir = source
        files = os.listdir(file_dir)

        if not files:
            print("[INFO] There were no files for neo4j update to process, skipping ...", file=sys.stderr)
            return None

        n = min(max_theoretical_threads, len(files), max_threads)
        file_chunks = list(self.get_chunks(lst=files, n=n))

        with Config.connection_helper.neo4j_session_scope() as session:

            # if clear flag, clear all data
            if clear:
                print("Deleting all entities and relationships ... ", file=sys.stderr)
                session.run("match (n) detach delete n;")

            print("Recreating constraints ... ", file=sys.stderr)
            # first drop constraints
            session.run("DROP CONSTRAINT unique_docs IF EXISTS")
            session.run("DROP CONSTRAINT unique_ents IF EXISTS")
            session.run("DROP CONSTRAINT unique_resps IF EXISTS")
            session.run("DROP CONSTRAINT unique_topics IF EXISTS")

            # next set up a few things to make sure that entities/documents/pubs aren't being inserted more than once.
            session.run("CREATE CONSTRAINT unique_docs IF NOT EXISTS ON (d:Document) ASSERT d.doc_id IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_ents IF NOT EXISTS ON (e:Entity) ASSERT e.name IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_resps IF NOT EXISTS ON (r:Responsibility) ASSERT r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_topics IF NOT EXISTS ON (t:Topic) ASSERT t.name IS UNIQUE")

            # Create indicies
            session.run("CREATE INDEX document_index IF NOT EXISTS FOR (d:Document) ON (d.doc_id, d.ref_name)")
            session.run("CREATE INDEX entity_index IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            session.run("CREATE INDEX topic_index IF NOT EXISTS FOR (t:Topic) ON (t.name)")
            session.run("CREATE INDEX responsibility_index IF NOT EXISTS FOR (r:Responsibility) ON (r.name)")

        publisher = Neo4jPublisher()
        publisher.populate_verified_ents()
        publisher.process_entity_relationships()

        q = mp.Queue()
        proc = mp.Process(target=self.listener, args=(q, len(files)))
        proc.start()
        workers = [mp.Process(target=self.process_files, args=(file_chunks[i], file_dir, q, publisher)) for i in range(n)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()
        q.put(None)
        proc.join()

        if scrape_wiki:
            publisher.process_crowdsourced_ents(without_web_scraping, infobox_dir)

        with Config.connection_helper.neo4j_session_scope() as session:
            # Make Docs not in Corpus from Refs
            print("Finding any REFERENCES to documents we do not currently have and creating a document node for them ... ", file=sys.stderr)
            session.run(
                "MATCH (d:Document) "
                "UNWIND d.ref_list as ref "
                "WITH COLLECT(distinct(ref)) as full_refs_list, COLLECT(distinct(d.ref_name)) as have_refs_list "
                "WITH [n IN full_refs_list WHERE NOT n IN have_refs_list] as needed_refs_list "
                "UNWIND needed_refs_list as ref "
                "MERGE (d:Document {ref_name: ref}) "
                "ON CREATE "
                "  SET d.type = 'UKN_document', "
                "  d.doc_id = 'Unkown' + ref, "
                "  d.keyw_5 = [], "
                "  d.topics = [], "
                "  d.filename = 'Unknown', "
                "  d.title = ref, "
                "  d.display_title_s = ref, "
                "  d.display_org_s = 'Unknown', "
                "  d.display_doc_type_s = 'Unknown', "
                "  d.name = ref, "
                "  d.ref_list = [] "
            )

            # Make ref connections
            print("Looping through documents creating REFERENCES connections to the documents they reference ... ", file=sys.stderr)
            session.run(
                "MATCH (d:Document) "
                "WHERE d.type = 'document' "
                "WITH d.ref_list as ref_list, d "
                "MATCH (d2:Document) "
                "WHERE d2.ref_name IN ref_list AND NOT d = d2 "
                "MERGE (d)-[:REFERENCES]->(d2);"
            )

            # Create Sub Graph
            session.run(
                "call gds.graph.create('sim-graph', ['Document', 'Entity', 'Topic'], ['REFERENCES', 'MENTIONS', 'CONTAINS']);"
            )

            # Create Similarity Links
            print("Creating SIMILARITY connections ... ", file=sys.stderr)
            session.run(
                "CALL gds.nodeSimilarity.stream('sim-graph') " +
                "YIELD node1, node2, similarity " +
                "WITH gds.util.asNode(node1) AS NODE1, gds.util.asNode(node2) AS NODE2, similarity " +
                "MATCH (NODE1) WHERE 'Document' in labels(NODE1) AND NOT NODE1 = NODE2 AND similarity > 0.5 " +
                "MATCH (NODE2) WHERE 'Document' in labels(NODE2) AND NOT NODE2 = NODE1 AND similarity > 0.5 " +
                "MERGE (NODE1)-[:SIMILAR_TO {similarity: similarity}]->(NODE2);"
            )

            # Drop Sub Graph
            session.run(
                "call gds.graph.drop('sim-graph');"
            )

            # delete any entity nodes without a name
            session.run("MATCH (e:Entity {name: ''}) detach delete (e);")

            print('Done', file=sys.stderr)
