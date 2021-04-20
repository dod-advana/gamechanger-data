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
            chunk_end = chunk_start + (max_chunk_size if i == n-2 else min_chunk_size)

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
            session.run("DROP CONSTRAINT unique_pubs IF EXISTS")
            session.run("DROP CONSTRAINT unique_docs IF EXISTS")
            session.run("DROP CONSTRAINT unique_ents IF EXISTS")
            session.run("DROP CONSTRAINT unique_resps IF EXISTS")

            # next set up a few things to make sure that entities/documents/pubs aren't being inserted more than once.
            session.run("CREATE CONSTRAINT unique_pubs IF NOT EXISTS ON (p:Publication) ASSERT p.name IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_docs IF NOT EXISTS ON (d:Document) ASSERT d.doc_id IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_ents IF NOT EXISTS ON (e:Entity) ASSERT e.name IS UNIQUE")
            session.run("CREATE CONSTRAINT unique_resps IF NOT EXISTS ON (r:Responsibility) ASSERT r.name IS UNIQUE")

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
            # delete any entity nodes without a name
            session.run("MATCH (e:Entity {name: ''}) detach delete (e);")

            print('Done', file=sys.stderr)
