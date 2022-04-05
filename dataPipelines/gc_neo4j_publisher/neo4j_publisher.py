import json
import os
import time
import typing as t
import sys
from pathlib import Path

import pandas as pd
from joblib._multiprocessing_helpers import mp
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

from gamechangerml.src.featurization.abbreviation import expand_abbreviations_no_context
from gamechangerml.src.featurization.responsibilities import get_responsibilities
from dataPipelines.gc_neo4j_publisher.config import Config
from dataPipelines.gc_neo4j_publisher import wiki_utils as wu
from neo4j import exceptions
import common.utils.text_utils as tu
import re
from .config import Config as MainConfig
from functools import lru_cache


@lru_cache(maxsize=None)
def get_abbcount_dict() -> t.Dict[str, t.Any]:
    with open(Config.abbcount_json_path, "r") as file:
        dic = json.load(file)
    return dic


@lru_cache(maxsize=None)
def get_agency_names() -> t.List[str]:
    df = pd.read_csv(Config.agencies_csv_path)
    agencies = list(df['Agency_Name'])
    agencies = [x.lower() for x in agencies]
    return agencies


def process_ent(ent: str) -> t.Union[t.List[str], str]:
    first_word = ent.split(" ")[0]
    if (
            first_word.upper() == "THE"
            or len(first_word) == 1
            or first_word.upper() == "THIS"
    ):
        ent = ent.split(" ")[1:]
        ent = " ".join(ent)
    if "......." in ent:
        ent = ent.split(".....")[0]
    new_ent = expand_abbreviations_no_context(ent, dic=get_abbcount_dict())
    if len(new_ent) > 0:
        return new_ent[0]
    else:
        return ent


def process_query(query: str, parameters: t.Dict[str, t.Any] = None, **kwparameters) -> None:
    with MainConfig.connection_helper.neo4j_session_scope() as session:
        try_count = 0
        while try_count <= 10:
            try:
                result = session.run(query, parameters, **kwparameters)
                return
            except exceptions.TransientError:
                try_count += 1
                time.sleep(10)
            except Exception as e:
                try_count += 1
                time.sleep(10)
                print("Error with query: {0}. Error: {1}".format(query, e))


class Neo4jPublisher:
    def __init__(self):
        self.entEntRelationsStmt = []
        self.verifiedEnts = pd.DataFrame()
        self.crowdsourcedEnts = set()

    def process_json(self, filepath: str, q: mp.Queue) -> str:
        with open(filepath) as f:
            j = json.load(f)
            o = {}

            o["id"] = j.get("id", "")
            o["doc_num"] = j.get("doc_num", "")
            o["doc_type"] = j.get("doc_type", "")
            o["display_title_s"] = j.get("display_title_s", "")
            o["display_org_s"] = j.get("display_org_s", "")
            o["display_doc_type_s"] = j.get("display_doc_type_s", "")
            o["ref_list"] = [s.replace("'", '\"') for s in j.get("ref_list", [])]
            o["access_timestamp_dt"] = j.get("access_timestamp_dt", "")
            o["publication_date_dt"] = (j.get("publication_date_dt", "") or "")
            o["crawler_used_s"] = j.get("crawler_used_s", "")
            o["source_fqdn_s"] = j.get("source_fqdn_s", "")
            o["source_page_url_s"] = j.get("source_page_url_s", "")
            o["download_url_s"] = j.get("download_url_s", '')
            o["cac_login_required_b"] = j.get("cac_login_required_b", False)
            o["title"] = j.get("title", "").replace('"', "\'")
            o["keyw_5"] = [s.encode('ascii', 'ignore').decode('utf-8') for s in j.get("keyw_5", [])]
            o["filename"] = j.get("filename", "")
            o["summary_30"] = j.get("summary_30", "")
            o["type"] = j.get("type", "")
            o["page_count"] = j.get("page_count", 0)
            o["topics_rs"] = j.get("topics_s", [])
            o["init_date"] = j.get("init_date", "")
            o["change_date"] = j.get("change_date", "")
            o["author"] = j.get("author", "")
            o["signature"] = j.get("signature", "")
            o["subject"] = j.get("subject", "")
            o["classification"] = j.get("classification", "")
            o["group_s"] = j.get("group_s", "")
            o["pagerank_r"] = j.get("pagerank_r", 0)
            o["kw_doc_score_r"] = j.get("kw_doc_score_r", 0)
            o["version_hash_s"] = j.get("version_hash_s", "")
            o["is_revoked_b"] = j.get("is_revoked_b", False)
            o["entities"] = self.process_entity_list(j)

            process_query('CALL policy.createDocumentNodesFromJson(' + json.dumps(json.dumps(o)) + ')')

            # # TODO responsibilities
            # text = j["text"]
            # self.process_responsibilities(text)

            # TODO paragraphs
            # self.process_paragraphs(j, doc_id)

        q.put(1)
        return id

    def process_responsibilities(self, text: str) -> None:
        resp = get_responsibilities(text, agencies=get_agency_names())
        if resp:
            for d in resp.values():
                ent = d["Agency"]
                resps = d["Responsibilities"]
                if ent:
                    filtered_ent = self.filter_ents(ent.strip())
                    if filtered_ent:
                        for r in resps:
                            process_query(
                                'MATCH (e: Entity) WHERE toLower(e.name) = \"'
                                + filtered_ent.lower()
                                + '\" '
                                + 'MERGE (r: Responsibility {name: \"'
                                + r
                                + '\"}) '
                                + 'MERGE (e)-[:RESPONSIBLE_FOR]->(r);'
                            )
        return

    # TODO: refactor param injection logic for cypher statements to guarantee valid statements for all valid strings
    @staticmethod
    def _normalize_string(s: str) -> str:
        """Normalize string to something that won't interfere with a cypher query"""
        return tu.str_chain_apply(
            s,
            [
                tu.translate_to_ascii_string,
                tu.squash_whitespace_to_spaces,
                tu.remove_plus_signs,
                lambda _s: re.sub(r"""['"]\s*['"]""", "", _s),  # remove empty quotes
                lambda _s: re.sub(r'"', r'', _s),  # remove double quotes
                tu.squash_non_word_characters
            ]
        )

    def process_paragraphs(self, j: t.Dict[str, t.Any], doc_id: str) -> None:
        for idx, p in enumerate(j["paragraphs"]):
            process_query(
                'MERGE (a: Document {doc_id: \"'
                + doc_id
                + '\"}) '
                + 'MERGE (p:Paragraph {par_id: \"' + p['id'] + '\"}) '
                + 'SET p.page_num_i = ' + str(p['page_num_i'])
                + ', p.par_count_i = ' + str(p['par_count_i'])
                + ', p.par_raw_text_t = \"' + self._normalize_string(p['par_raw_text_t']) + '\" '
                + ', p.doc_id = \"' + doc_id + '\" '
                + 'CREATE (a)-[:CONTAINS]->(p);'
            )
        return

    def process_entity_list(self, j: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        entity_dict: t.Dict[str, t.Any] = {}
        entity_count: t.Dict[str, int] = {}
        try:
            for p in j["paragraphs"]:
                entities = p["entities"]
                types = list(entities.keys())
                for type in types:
                    entity_list = entities[type]
                    for ent in (self._normalize_string(e) for e in entity_list):
                        ans = self.filter_ents(ent)
                        if len(ans) > 0:
                            if ans not in entity_dict:
                                entity_dict[ans] = []
                                entity_count[ans] = 0

                            entity_dict[ans].append(p["par_inc_count"])
                            entity_count[ans] += 1
        except:
            print('Error creatign entities for: ' + j["id"], file=sys.stderr)

        return {"entityPars": entity_dict, "entityCounts": entity_count}

    def populate_verified_ents(self, csv: str = Config.agencies_csv_path) -> None:
        csv_untrimmed = pd.read_csv(csv, na_filter=False)
        csv = csv_untrimmed.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        self.verifiedEnts = csv

        if Config.does_assist_table_exist():
            with Config.connection_helper.web_db_session_scope('ro') as session:
                verified_pg = session.execute("SELECT tokens_assumed FROM gc_assists WHERE tagged_correctly=true")
                verified = [el[0] for el in verified_pg]
        else:
            verified = []
            print("Could not retrieve gc_assists table - it doesn't exist.", file=sys.stderr)

        # process entities
        processed_set = set()
        upper_set = set()

        for ent in verified:
            new_ent = process_ent(ent)
            if new_ent.upper() not in upper_set:
                upper_set.add(new_ent.upper())
                processed_set.add(new_ent)

        self.crowdsourcedEnts = processed_set

    def process_entity_relationships(self) -> None:
        total_ents = len(self.verifiedEnts)
        print('Inserting {0} entities ...'.format(total_ents))
        entity_json = self.verifiedEnts.to_json(orient="records")
        process_query('CALL policy.createEntityNodesFromJson(' + json.dumps(entity_json) + ')')
        return

    def process_dir(self, files: t.List[str], file_dir: str, q: mp.Queue, max_threads: int) -> None:
        if not files:
            return

        with ThreadPoolExecutor(max_workers=min(max_threads, 16)) as ex:
            futures = []
            for filename in files:
                try:
                    if filename.endswith('.json'):
                        futures.append(ex.submit(self.process_json(os.path.join(file_dir, filename), q)))
                except Exception as err:
                    print('RuntimeError in: ' + filename + ' Error: ' + str(err), file=sys.stderr)
                    q.put(1)
        return

    def filter_ents(self, ent: str) -> str:
        new_ent = process_ent(ent)
        name_df = self.verifiedEnts[
            self.verifiedEnts["Agency_Name"].str.upper() == new_ent.upper()
            ]
        if len(name_df):
            return name_df.iloc[0, 1]
        else:
            if new_ent in self.crowdsourcedEnts:
                return new_ent
            else:
                return ""

    def process_crowdsourced_ents(self, without_web_scraping: bool, infobox_dir: t.Optional[str] = None):
        # check that if no web scraping, we have infobox-dir defined.
        # check that infobox-dir was specified, is a directory, has stuff in it if not webscraping.
        if without_web_scraping:
            if infobox_dir is None:
                print("ERROR: infobox-dir was not specified with --without-web-scraping. run the command again with "
                      "--infobox-dir specified.")
                return

            if not Path(infobox_dir).is_dir():
                print("ERROR: infobox-dir is not a directory with --without-web-scraping. Run the command again with "
                      "--infobox-dir pointing to a directory.")
                return

            if not list(Path(infobox_dir).iterdir()):
                print("ERROR: infobox-dir is an empty directory with --without-web-scraping. Run the command again "
                      "with --infobox-dir pointing to a non-empty directory.")
                return

        total_ents = len(self.crowdsourcedEnts)
        print('Inserting {0} entities...'.format(total_ents))

        # get the info from wiki page if possible
        for ent in self.crowdsourcedEnts:
            if without_web_scraping:
                # read in json
                filename = infobox_dir + '/' + ent + '_infobox.json'
                if os.path.exists(filename):
                    f = open(filename)
                    info = json.load(f)
                else:
                    info = {}
                    print("Infobox file does not exist for entity {0}".format(ent))
            else:
                info = wu.get_infobox_info(ent)

            if 'Redirect_Name' in info.keys():
                name = info['Redirect_Name']
            else:
                name = ent

            # s is the insert statement for this entity's node
            s = 'MERGE (e:Entity {name: \"' + self._normalize_string(name) + '\"})  '

            # loop through the keys and add the metadata to the node
            for key in info.keys():
                if key == 'Redirect_Name':  # we don't need this as it's just name in the metadata
                    continue
                # r is the relationship statement between nodes
                r = 'MATCH (e:Entity) where e.name =~ \"(?i)' + self._normalize_string(name) + '\"  '
                ins = info[key]
                # sometimes the value is a list depending on HTML format, so unwrap it
                if isinstance(ins, list):
                    for exp in ins:
                        # find if the value is a node that already exists. if it is, add a relationship using key
                        # as the relation
                        # create rule for child_agency/child_agencies
                        if self._normalize_string(key) == 'Child_agencies' or self._normalize_string(
                                key) == 'Child_agency':
                            rel = 'HAS_CHILD'
                        else:
                            rel = key
                        r += 'MATCH (f: Entity) where f.name =~ \"(?i)' + exp + '\" '
                        r += 'CREATE (e)-[:' + self._normalize_string(rel).upper() + ']->(f)'
                        self.entEntRelationsStmt.append(r)
                        # reset the relationship insert string
                        r = 'MATCH (e:Entity) where e.name =~ \"(?i)' + self._normalize_string(name) + '\"  '

                    # must unwind the list to add to neo4j as a param ([1,2,3] -> '1;2;3')
                    ins = ''
                    for el in info[key]:
                        ins += el + '; '
                    ins = ins[:-2]

                else:
                    # create rule for child_agency/child_agencies
                    if self._normalize_string(key) == 'Child_agencies' or self._normalize_string(key) == 'Child_agency':
                        rel = 'HAS_CHILD'
                    else:
                        rel = key

                    # create the relationships
                    r += 'MATCH (f: Entity) where f.name =~ \"(?i)' + self._normalize_string(ins) + '\" '
                    r += 'CREATE (e)-[:' + self._normalize_string(rel).upper() + ']->(f)'
                    self.entEntRelationsStmt.append(r)

                s += 'SET e.' + self._normalize_string(key) + '= \"' + ins + '\" '

            process_query(s + ';')

        self.entEntRelationsStmt = list(set(self.entEntRelationsStmt))

        for r in self.entEntRelationsStmt:
            process_query(r)
