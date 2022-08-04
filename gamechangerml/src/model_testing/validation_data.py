import logging
import pandas as pd
import numpy as np
from collections import OrderedDict
from gamechangerml.src.utilities.text_utils import normalize_answer, normalize_query, filter_title_queries
from gamechangerml.src.utilities.test_utils import *
from gamechangerml.configs import ValidationConfig
from gamechangerml.src.utilities.test_utils import filter_date_range, open_txt
from gamechangerml import REPO_PATH

CORPUS_DIR = os.path.join(REPO_PATH, "gamechangerml", "corpus")
logger = logging.getLogger(__name__)


class ValidationData:
    def __init__(self, validation_dir):

        self.validation_dir = validation_dir


class SQuADData(ValidationData):
    def __init__(
        self,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        squad_path=ValidationConfig.DATA_ARGS["squad"]["dev"],
        sample_limit=None,
    ):

        super().__init__(validation_dir)
        logger.info(
            f"Pulling validation data from {str(os.path.join(validation_dir, squad_path))}"
        )
        if not os.path.exists(os.path.join(validation_dir, squad_path)):
            logger.warning("No directory exists for this validation data.")
        self.dev = open_json(squad_path, validation_dir)
        self.queries = self.get_squad_sample(sample_limit)

    def get_squad_sample(self, sample_limit):
        """Format SQuAD data into list of dictionaries (length = sample size)"""

        data_limit = len(self.dev["data"])

        if sample_limit:
            data_limit = np.min([data_limit, sample_limit])
            par_limit = sample_limit // data_limit
        else:
            par_limit = np.max([len(d["paragraphs"])
                               for d in self.dev["data"]])

        count = 0
        queries = []
        for p in range(par_limit):
            for d in range(data_limit):
                try:
                    base = self.dev["data"][d]["paragraphs"][p]
                    context = base["context"]
                    questions = base["qas"]
                    q_limit = np.min([2, par_limit, len(questions)])
                    for q in range(q_limit):
                        if count < sample_limit:
                            count += 1
                            mydict = {
                                "search_context": context,
                                "question": questions[q]["question"],
                                "id": questions[q]["id"],
                                "null_expected": questions[q]["is_impossible"],
                                "expected": questions[q]["answers"],
                            }
                            queries.append(mydict)
                        else:
                            break
                except:
                    pass

        logger.info(
            "Generated {} question/answer pairs from SQuAD dataset".format(
                len(queries))
        )

        return queries


class QADomainData(ValidationData):
    def __init__(
        self,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        qa_gc_data_path=ValidationConfig.DATA_ARGS["question_gc"]["queries"],
    ):

        super().__init__(validation_dir)
        self.all_queries = open_json(qa_gc_data_path, self.validation_dir)
        self.queries = self.check_queries()

    def check_queries(self):
        """Check that in-domain examples contain expected answers in their context"""

        checked = []
        for test in self.all_queries["test_queries"]:
            alltext = normalize_query(" ".join(test["search_context"]))
            checked_answers = [
                i for i in test["expected"] if normalize_answer(i["text"]) in alltext
            ]
            test["expected"] = checked_answers
            if test["expected"] != []:
                checked.append(test)
            else:
                logger.info(
                    "Could not add {} to test queries: answer not in context".format(
                        test["question"]
                    )
                )

        logger.info(
            "Generated {} question/answer pairs from in-domain data".format(
                len(checked)
            )
        )

        return checked


class MSMarcoData(ValidationData):
    def __init__(
        self,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        queries=ValidationConfig.DATA_ARGS["msmarco"]["queries"],
        collection=ValidationConfig.DATA_ARGS["msmarco"]["collection"],
        relations=ValidationConfig.DATA_ARGS["msmarco"]["relations"],
        metadata=ValidationConfig.DATA_ARGS["msmarco"]["metadata"],
    ):

        super().__init__(validation_dir)
        self.queries = open_json(queries, self.validation_dir)
        self.collection = open_json(collection, self.validation_dir)
        self.relations = open_json(relations, self.validation_dir)
        self.metadata = open_json(metadata, self.validation_dir)
        self.corpus = self.get_msmarco_corpus()

    def get_msmarco_corpus(self):
        """Format MSMarco so it can be indexed like the GC corpus"""

        return [(x, y, "") for x, y in self.collection.items()]


class RetrieverGSData(ValidationData):
    def __init__(self, validation_dir,  available_ids, gold_standard):

        super().__init__(validation_dir)
        self.samples = pd.read_csv(
            os.path.join(
                ValidationConfig.DATA_ARGS['user_dir'], gold_standard),
            names=["query", "document"],
        )
        self.queries, self.collection, self.relations = self.dictify_data(
            available_ids)

    def dictify_data(self, available_ids):
        """
        Filter out any validation queries whose documents areen't in the index.
        Forrmat gold standard csv examples into MSMarco format.
        """
        ids = [
            ".".join(i.strip("\n").split(".")[:-1]).strip().lstrip()
            for i in available_ids
        ]
        self.samples["document"] = self.samples["document"].apply(
            lambda x: [i.strip().lstrip() for i in x.split(";")]
        )
        self.samples = self.samples.explode("document")
        df = self.samples[
            self.samples["document"].isin(ids)
        ]  # check ids are in the index
        if df.shape[0] < self.samples.shape[0]:
            all_ids = self.samples["document"].unique()
            missing_ids = [i for i in all_ids if i not in ids]
            logger.info(
                "Validation IDs not in the index (removed from validation set): {}".format(
                    missing_ids
                )
            )
            logger.info("Number of missing IDs: {}".format(
                str(len(missing_ids))))
            logger.info(
                "Number documents in the index to test: {}".format(
                    str(len(all_ids) - len(missing_ids))
                )
            )

        df = df.groupby("query").agg(
            {"document": lambda x: x.tolist()}).reset_index()
        query_list = df["query"].to_list()
        doc_list = df["document"].to_list()
        q_idx = ["query_" + str(i) for i in range(len(query_list))]
        queries = dict(zip(q_idx, query_list))
        collection = dict(zip(all_ids, all_ids))
        relations = dict(zip(q_idx, doc_list))

        logger.info(
            "Generated {} test queries of gold standard data from search history".format(
                len(query_list))
        )

        return queries, collection, relations


class UpdatedGCRetrieverData(RetrieverGSData):
    def __init__(
        self,
        available_ids,
        level=["gold", "silver"],
        data_path=None,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        gold_standard=ValidationConfig.DATA_ARGS["retriever_gc"]["gold_standard"],
    ):

        super().__init__(validation_dir,  available_ids, gold_standard)
        new_data = ""
        try:
            if data_path:  # if there is a path for data, use that
                self.data_path = os.path.join(data_path, level)
            else:
                new_data = get_most_recent_dir(
                    os.path.join(
                        ValidationConfig.DATA_ARGS["validation_dir"], "domain", "sent_transformer"
                    )
                )
                self.data_path = os.path.join(new_data, level)
            (
                self.new_queries,
                self.new_collection,
                self.new_relations,
            ) = self.load_new_data()
            self.combine_in_domain()
        except Exception as e:
            logger.info(
                f"Error getting data from {new_data}. Could not create UpdatedGCRetrieverData object."
            )

    def load_new_data(self):

        f = open_json("intelligent_search_data.json", self.data_path)
        intel = json.loads(f)
        logger.info(
            f"Added {str(len(intel['correct']))} correct query/sent pairs from updated GC retriever data."
        )
        return intel["queries"], intel["collection"], intel["correct"]

    def combine_in_domain(self):

        self.queries.update(
            {
                k: v
                for (k, v) in self.new_queries.items()
                if k in self.new_relations.keys()
            }
        )
        self.collection.update(self.new_collection)
        self.relations.update(self.new_relations)

        return


class NLIData(ValidationData):
    def __init__(
        self,
        sample_limit,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        matched=ValidationConfig.DATA_ARGS["nli"]["matched"],
        mismatched=ValidationConfig.DATA_ARGS["nli"]["matched"],
    ):

        super().__init__(validation_dir)
        self.matched = open_jsonl(matched, self.validation_dir)
        self.mismatched = open_jsonl(mismatched, self.validation_dir)
        self.sample_csv = self.get_sample_csv(sample_limit)
        self.query_lookup = dict(
            zip(self.sample_csv["promptID"], self.sample_csv["sentence1"])
        )

    def get_sample_csv(self, sample_limit):
        """Format NLI data into smaller sample for evaluation"""

        match_df = pd.DataFrame(self.matched)
        mismatched_df = pd.DataFrame(self.mismatched)
        match_df["set"] = "matched"
        mismatched_df["set"] = "mismatched"
        both = pd.concat([match_df, mismatched_df])
        # assign int ranks based on gold label
        gold_labels_map = {"entailment": 2, "neutral": 1, "contradiction": 5}
        both["gold_label_int"] = both["gold_label"].map(gold_labels_map)

        # filter out propmtIDs that don't have a clear 0, 1, 2 rank
        sum_map = both.groupby("promptID")["gold_label_int"].sum().to_dict()
        both["rank_sum"] = both["promptID"].map(sum_map)
        both = both[both["rank_sum"] == 8]

        # map ranks
        rank_map = {"entailment": 0, "neutral": 1, "contradiction": 2}
        both["expected_rank"] = both["gold_label"].map(rank_map)

        cats = both["genre"].nunique()

        # get smaller sample df with even proportion of genres across matched/mismatched
        sample = pd.DataFrame()
        for i in both["genre"].unique():
            subset = both[both["genre"] == i].sort_values(by="promptID")
            if sample_limit:
                split = sample_limit * 3 // cats
                subset = subset.head(split)
            sample = pd.concat([sample, subset])

        logger.info(
            (
                "Created {} sample sentence pairs from {} unique queries:".format(
                    sample.shape[0], sample_limit
                )
            )
        )

        return sample[
            [
                "genre",
                "gold_label",
                "pairID",
                "promptID",
                "sentence1",
                "sentence2",
                "expected_rank",
            ]
        ]


class MatamoFeedback:
    def __init__(self, start_date, end_date, exclude_searches, testing_only=False):

        self.matamo = concat_matamo(testing_only)
        self.start_date = start_date
        self.end_date = end_date
        self.exclude_searches = exclude_searches
        self.intel, self.qa = self.split_matamo()

    def split_matamo(self):
        """Split QA queries from intelligent search queries"""

        df = self.matamo
        if self.start_date or self.end_date:
            df = filter_date_range(df, self.start_date, self.end_date)
        df.drop_duplicates(
            subset=["user_id", "createdAt", "value_1", "value_2"], inplace=True
        )
        df["source"] = "matamo"
        df["correct"] = (
            df["event_name"]
            .apply(lambda x: " ".join(x.split("_")[-2:]))
            .map({"thumbs up": True, "thumbs down": False})
        )
        df["type"] = df["event_name"].apply(
            lambda x: " ".join(x.split("_")[:-2]))
        df["value_5"] = df["value_5"].apply(
            lambda x: x.replace("sentence_results", "sentence_results:")
            if type(x) == str
            else x
        )

        intel = df[df["type"] == "intelligent search"].copy()
        intel.dropna(axis=1, how="all", inplace=True)
        qa = df[df["type"] == "qa"].copy()
        qa.dropna(axis=1, how="all", inplace=True)

        def process_matamo(df):
            """Reformat Matamo feedback"""

            queries = []
            cols = [i for i in df.columns if i[:5] == "value"]

            def process_row(row, col_name):
                """Split the pre-colon text from rows"""

                if ":" in row:
                    row = row.split(":")
                    key = row[0]
                    vals = ":".join(row[1:])
                    return key, vals
                else:
                    return col_name, row

            for i in df.index:
                query = {}
                query["date"] = df.loc[i, "createdAt"]
                query["source"] = "matamo"
                query["correct_match"] = df.loc[i, "correct"]
                for j in cols:
                    row = df.loc[i, j]
                    if type(row) == str and row[0] != "[":
                        key, val = process_row(row, j)
                        query[key] = val
                        if key in ["question", "search_text", "QA answer"]:
                            clean_val = normalize_query(val)
                            clean_key = key + "_clean"
                            query[clean_key] = clean_val
                queries.append(query)

            return pd.DataFrame(queries)

        return process_matamo(intel), process_matamo(qa)


class SearchHistory:
    def __init__(self, start_date, end_date, exclude_searches, testing_only=False):

        self.history = concat_search_hist(testing_only)
        self.start_date = start_date
        self.end_date = end_date
        self.exclude_searches = exclude_searches
        self.intel_matched, self.intel_unmatched = self.split_feedback()

    def split_feedback(self):

        df = self.history
        if self.start_date or self.end_date:
            df = filter_date_range(df, self.start_date, self.end_date)
        # drop all rows where is no search
        df.dropna(subset=['value'], inplace=True)
        # drop duplicates
        df.drop_duplicates(
            subset=['idvisit', 'document', 'value'], inplace=True)
        df['source'] = 'user_history'

        def clean_quot(string):
            return string.replace("&quot;", "'").replace("&#039;", "'").lower()

        def clean_doc(string):
            doc = string.split(".pdf")[0]
            doc = ' '.join([i for i in doc.split(' ') if i != ''])
            return doc

        def is_question(string):
            """If we find a good way to use search history for QA validation (not used currently)"""

            question_words = ["what", "who", "where", "why", "how", "when"]
            if "?" in string:
                return True
            else:
                return bool(set(string.lower().split()).intersection(question_words))

        df.rename(columns={'documenttime': 'date', 'value': 'search_text',
                  'document': 'title_returned'}, inplace=True)
        df['search_text'] = df['search_text'].apply(lambda x: clean_quot(x))
        df['search_text_clean'] = df['search_text'].apply(
            lambda x: normalize_query(x))
        df['search_text_clean'].fillna('', inplace=True)
        df = df[df['search_text_clean'] != '']
        df.drop(columns=['idvisit', 'idaction_name',
                'search_cat', 'searchtime'], inplace=True)

        matched = df[~df['title_returned'].isnull()].copy()
        matched['correct_match'] = True
        matched['title_returned'] = matched['title_returned'].apply(
            lambda x: clean_doc(x))

        unmatched = df[df['title_returned'].isnull()].copy()
        unmatched['correct_match'] = False

        return matched, unmatched


class SearchValidationData:
    def __init__(self, start_date, end_date, exclude_searches, testing_only):

        self.start_date = start_date
        self.end_date = end_date
        self.exclude_searches = exclude_searches
        self.testing_only = testing_only
        self.matamo_data = MatamoFeedback(
            self.start_date, self.end_date, self.exclude_searches, self.testing_only
        )
        self.history_data = SearchHistory(
            self.start_date, self.end_date, self.exclude_searches, self.testing_only
        )


class QASearchData(SearchValidationData):

    # TODO: add context relations attr for QASearchData
    def __init__(
        self, start_date, end_date, exclude_searches, min_correct_matches, max_results
    ):

        super().__init__(start_date, end_date, exclude_searches)
        self.data = self.matamo_data.qa
        self.min_correct_matches = min_correct_matches
        self.max_results = max_results
        (
            self.queries,
            self.collection,
            self.all_relations,
            self.correct,
            self.incorrect,
        ) = self.make_qa()

    def make_qa(self):

        qa = self.data

        # get set of queries + make unique query dict
        qa_queries = set(qa["question_clean"])
        qa_search_queries = update_dictionary(
            old_dict={}, new_additions=qa_queries, prefix="Q"
        )

        # get set of docs + make unique doc dict
        qa_answers = set(qa["QA answer_clean"])
        qa_search_results = update_dictionary(
            old_dict={}, new_additions=qa_answers, prefix="A"
        )

        # map IDs back to df
        qa = map_ids(qa_search_queries, qa, "question_clean", "key")
        qa = map_ids(qa_search_results, qa, "QA answer_clean", "value")

        # create new QA metadata rels
        qa_metadata = {}  # TODO: add option to add existing metadata
        new_qa_metadata = update_meta_relations(
            qa_metadata, qa, "question", "QA answer"
        )

        # filtere the metadata to only get relations we want to test against
        correct, incorrect = filter_rels(
            new_qa_metadata,
            min_correct_matches=self.min_correct_matches,
            max_results=self.max_results,
        )

        return qa_search_queries, qa_search_results, new_qa_metadata, correct, incorrect


class IntelSearchData(SearchValidationData):
    def __init__(
        self,
        start_date,
        end_date,
        exclude_searches,
        min_correct_matches,
        max_results,
        filter_queries,
        index_path,
        testing_only
    ):

        super().__init__(start_date, end_date, exclude_searches, testing_only)
        self.exclude_searches = exclude_searches
        self.data = pd.concat(
            [self.matamo_data.intel, self.history_data.intel_matched]
        ).reset_index()
        self.min_correct_matches = min_correct_matches
        self.max_results = max_results
        self.filter_queries = filter_queries
        self.index_path = index_path
        self.queries, self.collection, self.all_relations, self.correct, self.incorrect, self.correct_vals, self.incorrect_vals = self.make_intel()

    def make_intel(self):

        intel = self.data

        int_queries = set(intel['search_text_clean'])

        # if filter queries == True, remove queries that are titles/fuzzy match titles
        if self.filter_queries:
            docs = open_txt(os.path.join(self.index_path, 'doc_ids.txt'))
            docs = [x.split('.pdf')[0] for x in docs]
            remove = filter_title_queries(int_queries, docs)
            self.exclude_searches.extend(remove)
            logger.info(
                f"**** Removing {str(len(self.exclude_searches))} queries.")
        int_queries = [
            i for i in int_queries if i not in self.exclude_searches]

        intel_search_queries = update_dictionary(
            old_dict={}, new_additions=int_queries, prefix='S')

        int_docs = set(intel['title_returned'])
        intel_search_results = update_dictionary(
            old_dict={}, new_additions=int_docs, prefix='R')

        # map IDS back to dfs
        intel = map_ids(intel_search_queries, intel,
                        "search_text_clean", "key")
        intel = map_ids(intel_search_results, intel, "title_returned", "value")

        # create new intel search metadata rels
        intel_metadata = {}  # TODO: add option to add existing metadata
        new_intel_metadata = update_meta_relations(
            intel_metadata, intel, "search_text", "title_returned"
        )

        # filtere the metadata to only get relations we want to test against
        logger.info(f"min_correct_matches: {(str(self.min_correct_matches))}")
        logger.info(f"max_results: {(str(self.max_results))}")
        correct, incorrect = filter_rels(
            new_intel_metadata,
            min_correct_matches=self.min_correct_matches,
            max_results=self.max_results,
        )

        def map_values(queries, collection, relations):
            vals_dict = {}
            for key in relations.keys():
                query = queries[key]
                doc_keys = relations[key]
                docs = [collection[i] for i in doc_keys]
                vals_dict[query] = docs

            return vals_dict

        correct_vals = map_values(
            intel_search_queries, intel_search_results, correct)
        incorrect_vals = map_values(
            intel_search_queries, intel_search_results, incorrect)

        def sort_dictionary(dictionary):

            mydict = OrderedDict(dictionary.items())
            mydict_new = {}
            for key in mydict.keys():
                vals = mydict[key]
                vals.sort()
                mydict_new[key] = vals
            return mydict_new

        correct_vals = sort_dictionary(correct_vals)
        incorrect_vals = sort_dictionary(incorrect_vals)

        return (
            intel_search_queries,
            intel_search_results,
            new_intel_metadata,
            correct,
            incorrect,
            correct_vals,
            incorrect_vals
        )


class QEXPDomainData(ValidationData):
    def __init__(
        self,
        validation_dir=ValidationConfig.DATA_ARGS["validation_dir"],
        qe_gc_path=ValidationConfig.DATA_ARGS["qe_gc"],
    ):

        super().__init__(validation_dir)
        self.data = open_json(qe_gc_path, self.validation_dir)["queries"]
