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


def process_query(query: str) -> None:
    with MainConfig.connection_helper.neo4j_session_scope() as session:
        try_count = 0
        while try_count <= 10:
            try:
                session.run(query)
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
        self.docInsertStmt = []
        self.relationsInsertStmt = []
        self.pubInsertStmt = []
        self.belongsToInsertStmt = []
        self.entInsertStmt = []
        self.pubEntRefStmt = []
        self.entEntRelationsStmt = []
        self.respInsertStmt = []
        self.entRespRelationStmt = []
        self.verifiedEnts = pd.DataFrame()
        self.crowdsourcedEnts = set()

    def process_json(self, filepath: str, q: mp.Queue) -> str:
        with open(filepath) as f:
            j = json.load(f)
            id = j["id"]
            # publication variables
            docNum = j["doc_num"]
            docType = j["doc_type"]
            displayTitle = j.get("display_title_s","").replace('"', "\'").encode('ascii', 'ignore').decode('utf-8')
            displayOrg = j.get("display_org_s", "")
            displayType = j.get("display_doc_type_s","")
            pubName = '{0} {1}'.format(docType, docNum) if (docNum != '' and docType != '') \
                else j["id"].split(",")[0].replace('.pdf_0', '')
            ref_list = [s.replace("'", '\"') for s in j["ref_list"]]
            accessTimestamp = j.get("access_timestamp_dt","")
            publicationDate = (j.get("publication_date_dt", "") or "")
            crawlerUsed = j.get("crawler_used_s","")
            sourceFqdn = j.get("source_fqdn_s","")
            sourcePageUrl = j.get("source_page_url_s","")
            downloadUrl = j.get("download_url_s", '')
            cacLoginRequired = str(j.get('cac_login_required_b',""))
            # doc variables
            title = j["title"].replace('"', "\'")
            doc_id = j["id"]
            # TODO: implement json decoder that strips non-ascii codes
            keyw_5 = [s.encode('ascii', 'ignore').decode('utf-8') for s in j["keyw_5"]]
            filename = j["filename"]
            docName = filename.split('.pdf')[0]

            # TODO: implement json decoder that strips non-ascii codes
            summary_30 = j["summary_30"]
            summary_30_str = str(summary_30).replace('"', "\'").encode('ascii', 'ignore').decode('utf-8')
            summary_30_str = str(summary_30_str).replace("\\", "/").encode('ascii', 'ignore').decode('utf-8')
            type = j["type"]
            pageCount = j["page_count"]

            tmp_topics = []
            topics = {}

            try:
                topics = j["topics_rs"]

                keys = list(topics.keys())
                tmp_topics = []
                for key in keys:
                    key_arr = key.split(' ')
                    new_key = ' '.join([x.capitalize() for x in key_arr])
                    tmp_topics.append(new_key)
            except Exception as e:
                print(title)

            # Create document and publication and belongs_to relationships
            query = (
                'MERGE (a:Document {doc_id: \"' + doc_id + '\"}) '
                + 'SET a.keyw_5 = ' + str(keyw_5)
                + ', a.topics = ' + str(tmp_topics)
                + ', a.filename = \"' + filename
                + '\", a.title= \"' + title
                + '\", a.display_title_s = \"' + displayTitle
                + '\", a.display_org_s = \"' + displayOrg
                + '\", a.display_doc_type_s = \"' + displayType
                + '\", a.access_timestamp_dt = \"' + accessTimestamp
                + '\", a.publication_date_dt = \"' + publicationDate
                + '\", a.crawler_used_s = \"' + crawlerUsed
                + '\", a.source_fqdn_s = \"' + sourceFqdn
                + '\", a.source_page_url_s = \"' + sourcePageUrl
                + '\", a.download_url_s = \"' + downloadUrl
                + '\", a.cac_login_required_b = \"' + cacLoginRequired
                + '\", a.doc_num = \"' + docNum
                + '\", a.summary_30 = \"' + summary_30_str
                + '\", a.doc_type = \"' + docType
                + '\", a.type = \"' + type
                + '\", a.name = \"' + docName
                + '\", a.ref_list = ' + str(ref_list)
                + " , a.page_count = " + str(pageCount)
                + ' '
                + 'MERGE (b:Publication {name: \"' + pubName + '\"}) '
                + 'SET b.doc_type = \"' + docType
                + '\", b.doc_num = \"' + docNum
                + '\", b.display_org_s = \"' + displayOrg
                + '\", b.display_doc_type_s = \"' + displayType
                + '\" '
                + 'MERGE (a)-[:BELONGS_TO]->(b);'
            )

            process_query(query)

            # relationships
            self.process_ref_list(ref_list, pubName)
            self.process_entity_list(j, doc_id)
            self.process_topics(topics, doc_id)

            # responsibilities
            text = j["text"]
            self.process_responsibilities(text)

        q.put(1)
        return id

    def process_topics(self, topics: t.Dict[str, t.Any], doc_id: str) -> None:
        topic_query = 'MERGE (a:Document {doc_id: \"' + doc_id + '\"}) '

        for idx, topic_key in enumerate(topics.keys()):
            char_code = idx
            ref_var = ''
            key_arr = topic_key.split(' ')
            new_key = ' '.join([x.capitalize() for x in key_arr])
            for i in range(int(char_code / 24) + 2):
                ref_var += chr(char_code % 24 + 98)
            topic_query += (
                    'MERGE (' + ref_var + ':Topic {name: \"' + new_key + '\"}) '
                    + 'MERGE (a)-[:CONTAINS {relevancy: ' + str(topics[topic_key]) + '}]->(' + ref_var + ') '
                    + 'MERGE (' + ref_var + ')-[:IS_IN {relevancy: ' + str(topics[topic_key]) + '}]->(a) '
            )

        process_query(topic_query)

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

    def process_ref_list(self, ref_list: t.List[str], name: str) -> None:
        if len(ref_list) <= 0:
            return

        query = ('MERGE (a:Publication {name: \"'
                 + name
                 + '\"}) ')
        for idx, ref in enumerate(ref_list):
            char_code = idx
            ref_var = ''
            for i in range(int(char_code / 24) + 1):
                ref_var += chr(char_code % 24 + 98)
            query += ('MERGE (' + ref_var + ':Publication {name: \"'
                      + ref
                      + '\"}) '
                      + 'MERGE (a)-[:REFERENCES]->(' + ref_var + ') ')

        query += ';'
        process_query(query)
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

    def process_entity_list(self, j: t.Dict[str, t.Any], doc_id: str) -> None:
        entityDict: t.Dict[str, t.Any] = {}
        entityCount: t.Dict[str, int] = {}
        for p in j["paragraphs"]:
            entities = p["entities"]
            types = list(entities.keys())
            for type in types:
                entity_list = entities[type]
                for ent in (self._normalize_string(e) for e in entity_list):
                    ans = self.filter_ents(ent)
                    if len(ans) > 0:
                        if ans not in entityDict:
                            entityDict[ans] = []
                            entityCount[ans] = 0

                        entityDict[ans].append(p["par_inc_count"])
                        entityCount[ans] += 1

        self.process_entity_refs(entityDict, entityCount, doc_id)
        return

    def process_entity_refs(self, entityDict: t.Dict[str, t.Any], entityCount: t.Dict[str, int], doc_id: str) -> None:
        query = 'MERGE (a: Document {doc_id: \"' \
                + doc_id \
                + '\"})'
        create_query = ''
        for idx, ent in enumerate(list(entityDict.keys())):
            char_code = idx
            ref_var = ''
            for i in range(int(char_code / 24) + 1):
                ref_var += chr(char_code % 24 + 98)
            query += ' MERGE (' + ref_var + ': Entity {name: \"' + ent + '\"})'
            create_query += ' CREATE (a)-[:MENTIONS {count: ' \
                            + str(entityCount[ent]) \
                            + ', pars: ' \
                            + str(entityDict[ent]) \
                            + '}]->(' + ref_var + ')'

        process_query(query + create_query + ';')
        return

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
        for _, row in tqdm(self.verifiedEnts.iterrows(), total=total_ents):
            process_query(
                'MERGE (e:Entity {name: \"'
                + row.Agency_Name
                + '\"}) SET e.aliases = \"'
                + row.Agency_Aliases
                + '\" SET e.website = \"'
                + row.Website
                + '\" SET e.image = \"'
                + row.Agency_Image
                + '\" SET e.address = \"'
                + row.Address
                + '\" SET e.phone = \"'
                + row.Phone
                + '\" SET e.tty = \"'
                + row.TTY
                + '\" SET e.tollfree = \"'
                + row.TollFree
                + '\" SET e.branch = \"'
                + row.Government_Branch
                + '\" SET e.type = \"'
                + 'organization'
                + '\" '
                + 'MERGE (p:Entity {name: \"'
                + row.Parent_Agency
                + '\"}) '
                + 'MERGE (e)-[:CHILD_OF]->(p) '
                + 'WITH e '
                + 'UNWIND split( \"'
                + row.Related_Agency
                + '\", \';\') AS re '
                + 'MERGE (a:Entity {name: trim(re)}) '
                + 'MERGE(e)-[:RELATED_TO]->(a) '
                + 'MERGE(a)-[:RELATED_TO]->(e) '
            )
        return

    def process_dir(self, files: t.List[str], file_dir: str, q: mp.Queue) -> None:
        if not files:
            return

        with ThreadPoolExecutor(max_workers=len(files)) as ex:
            futures = []
            for filename in files:
                if filename.endswith('.json'):
                    futures.append(ex.submit(self.process_json(os.path.join(file_dir, filename), q)))
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

