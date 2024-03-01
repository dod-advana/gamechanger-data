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


@lru_cache(maxsize=None)
def get_all_entities_and_aliases() -> t.List[str]:
    orgs_df = pd.read_excel(Config.graph_relations_xls_path, "Orgs")
    roles_df = pd.read_excel(Config.graph_relations_xls_path, "Roles")
    all_entities = list(orgs_df['Name']) + list(roles_df['Name'])
    alias_mapping_dict = {}
    for name, aliases in orgs_df[["Name", "Aliases"]].itertuples(index=False):
        if pd.isna(aliases):
            continue
        alias_keys = aliases.split(";")
        alias_mapping_dict.update({alias_key: name for alias_key in alias_keys})
    for name, aliases in roles_df[["Name", "Aliases"]].itertuples(index=False):
        if pd.isna(aliases):
            continue
        alias_keys = aliases.split(";")
        alias_mapping_dict.update({alias_key: name for alias_key in alias_keys})
    return all_entities, alias_mapping_dict


@lru_cache(maxsize=None)
def get_orgs_df() -> pd.DataFrame:
    orgs_df = pd.read_excel(Config.graph_relations_xls_path, "Orgs")
    orgs_df = orgs_df.drop([col for col in orgs_df.columns if "Unnamed" in col], axis=1)
    orgs_df = orgs_df.fillna("")
    orgs_df = orgs_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return orgs_df


@lru_cache(maxsize=None)
def get_roles_df() -> pd.DataFrame:
    roles_df = pd.read_excel(Config.graph_relations_xls_path, "Roles")
    roles_df = roles_df.drop([col for col in roles_df.columns if "Unnamed" in col], axis=1)
    roles_df = roles_df.fillna("")
    roles_df = roles_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return roles_df


@lru_cache(maxsize=None)
def get_hierarchy_json() -> dict:
    hierarchy_dict = json.load(open(Config.hierarchy_json_path, "r"))
    return hierarchy_dict


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
                return result.data()
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
        self.verified_entities_list, self.alias_mapping_dict = get_all_entities_and_aliases()
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
            o["entities"] = self.process_entity_list(j, "entities")
            o["orgs"] = self.process_entity_list(j, "orgs")
            o["roles"] = self.process_entity_list(j, "roles")
            process_query('CALL policy.createDocumentNodesFromJson(' + json.dumps(json.dumps(o)) + ')')

            # # TODO responsibilities
            # text = j["text"]
            # self.process_responsibilities(text)

            # TODO paragraphs
            # self.process_paragraphs(j, doc_id)

        q.put(1)
        return id

    def process_responsibilities(self, text: str) -> None:
        resp = get_responsibilities(text, agencies=self.verified_entities_list)
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

    def process_entity_list(self, j: t.Dict[str, t.Any], entity_type_key="orgs") -> t.Dict[str, t.Any]:
        entity_dict: t.Dict[str, t.Any] = {}
        entity_count: t.Dict[str, int] = {}
        try:
            for p in j["paragraphs"]:
                entities = p.get(entity_type_key, {})
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
            print('Error creating ' + entity_type_key + ' for: ' + j["id"], file=sys.stderr)

        return {"entityPars": entity_dict, "entityCounts": entity_count}

    def populate_crowdsourced_ents(self) -> None:
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

    def process_orgs(self) -> None:
        orgs_df = get_orgs_df()
        print('Inserting {0} orgs ...'.format(orgs_df.shape[0]))
        orgs_json = orgs_df.to_json(orient="records")
        process_query('CALL policy.createOrgNodesFromJson(' + json.dumps(orgs_json) + ')')
        return

    def process_roles(self) -> None:
        roles_df = get_roles_df()
        print('Inserting {0} roles ...'.format(roles_df.shape[0]))
        roles_json = roles_df.to_json(orient="records")
        process_query('CALL policy.createRoleNodesFromJson(' + json.dumps(roles_json) + ')')
        return

    @staticmethod
    def _get_nodes_and_relations(hierarchy_dict: dict) -> t.Tuple[t.List[str], t.List[t.Tuple[str, str]]]:
        """
            traverse dict level by level to grab parent:child keys
            returns unique node list and relation list
        """
        hierarchy_nodes = set()
        relations = set()
        dict_queue = [hierarchy_dict]

        # iteratively check each depth of the dict like a tree
        # enqueue smaller subset of tree as each level has been added until the empty dict leaf nodes
        while dict_queue:
            d = dict_queue.pop(0)

            for parent_str, child_dict in d.items():
                dict_queue.append(child_dict)
                hierarchy_nodes.add(parent_str)

                for child_str in child_dict.keys():
                    rel_tup = (parent_str, child_str)
                    relations.add(rel_tup)

        return (list(hierarchy_nodes), list(relations))

    def ingest_hierarchy_information(self) -> None:
        """
        This function pulls in the hierarchy json and generates an authority tree in the graph
        1) load in the hierarchy json as a python dictionary
        2) Create any nodes that are not currently in the graph (including matching by name/alias)
            a) This is commonly for non-org/roles, such as `United States Constitution`
        3) Create `HAS_AUTHORITY_OVER` relationships between the nodes in the authority tree
        Returns: None
        """
        print("Inserting Hierarchy Relationships ...")
        hierarchy_dict = get_hierarchy_json()

        all_hierarchy_nodes, authority_relationships = self._get_nodes_and_relations(hierarchy_dict)

        # check to see if the nodes are currently in the graph, for those that aren't (e.g., `United States Constitution`)
        # create a new node for those
        hierarchy_nodes_created = 0
        for hierarchy_node in all_hierarchy_nodes:
            match_cypher = "OPTIONAL MATCH (n:Entity) " \
                           "WHERE n.name='" + hierarchy_node + "' OR '" + hierarchy_node + "' in split(n.aliases,';') "\
                           "RETURN n IS NOT NULL AS Exists"
            # result = process_query(match_cypher)

            # create the node if the match_cypher above does not match on an existing node
            if not process_query(match_cypher)[0]['Exists']:
                create_cypher = "CREATE (n:Entity {name: '" + hierarchy_node + "'})"
                process_query(create_cypher)
                hierarchy_nodes_created += 1
        print(f"Inserted {hierarchy_nodes_created} hierarchy nodes (entity node type)")

        cypher_list = []
        for authority, subordinate in authority_relationships:
            # list join is to trying to find a way to make it more readable in code
            cypher_parts = [
                "MATCH (a:Entity), (b:Entity)",
                f"WHERE (a.name = '{authority}' OR '{authority}' in split(a.aliases, ';')) AND (b.name = '{subordinate}' OR '{subordinate}' in split(b.aliases, ';'))",
                "MERGE (a)-[r:HAS_AUTHORITY_OVER]->(b)"]

            cypher_string = " ".join(cypher_parts)
            cypher_list.append(cypher_string)

        print(f"Inserting {len(cypher_list)} hierarchy relationships ...")

        # Execute all of the `HAS_AUTHORITY_OVER` cypher commands
        for cypher in cypher_list:
            process_query(cypher)

    def process_dir(self, files: t.List[str], file_dir: str, q: mp.Queue, max_threads: int) -> None:
        print(f"process dir started", file=sys.stderr)
        try:
            if not files:
                return
            print(f"has files", file=sys.stderr)
            with ThreadPoolExecutor(max_workers=min(max_threads, 16)) as ex:
                futures = []
                print(f"thread pool {ex}", file=sys.stderr)
                for filename in files:
                    print(f"filename {filename}", file=sys.stderr)
                    try:
                        if filename.endswith('.json'):
                            futures.append(ex.submit(self.process_json(os.path.join(file_dir, filename), q)))
                    except Exception as err:
                        print('RuntimeError in: ' + filename + ' Error: ' + str(err), file=sys.stderr)
                        q.put(1)
                        return
        except Exception as e:
            print(f"Error in process_dir {e}", file=sys.stderr)
            q.put(1)
            return
        finally:
            print(f"process dir finally block, return", file=sys.stderr)
            return

    def filter_ents(self, ent: str) -> str:
        new_ent = process_ent(ent)
        try:
            match_idx = [ent.upper() for ent in self.verified_entities_list].index(new_ent.upper())
            return self.verified_entities_list[match_idx]
        except:
            if new_ent in self.alias_mapping_dict:
                return self.alias_mapping_dict[new_ent]
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
