import os
import json
from datetime import date
from typing import List, Union, Tuple, Dict
from gamechangerml.src.model_testing.validation_data import IntelSearchData
from gamechangerml.configs.config import ValidationConfig
from gamechangerml.src.utilities.test_utils import (
    make_timestamp_directory, check_directory, CustomJSONizer
    )
from gamechangerml import DATA_PATH
from gamechangerml.api.utils.pathselect import get_model_paths
import logging
logger = logging.getLogger()

model_path_dict = get_model_paths()
SENT_INDEX = model_path_dict['sentence']


def make_tiered_eval_data(index_path, testing_only):
 
    if not index_path:
        index_path = SENT_INDEX

    if not os.path.exists(os.path.join(DATA_PATH, "validation", "domain", "sent_transformer")):
        os.mkdir(os.path.join(DATA_PATH, "validation", "domain", "sent_transformer"))
    
    sub_dir = os.path.join(DATA_PATH, "validation", "domain", "sent_transformer")
    
    save_dir = make_timestamp_directory(sub_dir)

    def save_data(
        level: str, 
        min_correct_matches: int, 
        max_results: int, 
        start_date: str, 
        end_date: str, 
        exclude_searches: List[str], 
        filter_queries: bool,
        testing_only: bool,
        save_dir: Union[str,os.PathLike]=save_dir) -> Tuple[Dict[str,str], Dict[str,str], Dict[str,str]]:
        """Makes eval data for each tier level using args from config.py and saves to save_dir
        Args:
            level [str]: tier level (['any', 'silver', 'gold'])
            min_correct_matches [int]: number of minimum correct matches to count a positive pair
            max_results [int]: number of max unique results for a query to include matches as positive pairs
            start_date [str]: start date for queries (ex. 2020-12-01)
            end_date [str]: end date for queries (ex. 2021-12-01)
            exclude_searches [List[str]]: searches to ignore for making eval data
            save_dir [str}os.PathLike]: path for saving validation data
        Returns:
            [Tuple[Dict[str,str], Dict[str,str], Dict[str,str]]]: dictionaries of any, silver, and gold data
        """
        min_matches = min_correct_matches[level]
        max_res = max_results[level]

        intel = IntelSearchData(
                    start_date=start_date,
                    end_date=end_date,
                    exclude_searches=exclude_searches,
                    min_correct_matches=min_matches,
                    max_results=max_res,
                    filter_queries=filter_queries,
                    index_path=index_path,
                    testing_only=testing_only
                )

        save_intel = {
            "queries": intel.queries, 
            "collection": intel.collection, 
            "meta_relations": intel.all_relations,
            "correct": intel.correct,
            "incorrect": intel.incorrect,
            "correct_vals": intel.correct_vals,
            "incorrect_vals": intel.incorrect_vals
        }

        metadata = {
            "date_created": str(date.today()),
            "level": level,
            "number_queries": len(intel.queries),
            "number_documents": len(intel.collection),
            "number_correct": len(intel.correct),
            "number_incorrect": len(intel.incorrect),
            "start_date": start_date,
            "end_date": end_date,
            "exclude_searches": exclude_searches,
            "min_correct_matches": min_matches,
            "max_results": max_res,
            "filter_queries": str(filter_queries)
        }

        save_intel = json.dumps(save_intel, cls=CustomJSONizer)
        intel_path = check_directory(os.path.join(save_dir, level))
        intel_file = os.path.join(intel_path, 'intelligent_search_data.json')
        metafile =  os.path.join(intel_path, 'intelligent_search_metadata.json')
        with open(intel_file, "w") as outfile:
            json.dump(save_intel, outfile)
        
        with open(metafile, "w") as outfile:
            json.dump(metadata, outfile)
        logger.info(f"***Saved intelligent search validation data to: {intel_path}")        

        return metadata

    all_data = save_data(
        level='any',
        filter_queries = False,
        testing_only = testing_only,
        **ValidationConfig.TRAINING_ARGS
        )
    
    silver_data = save_data(
        level='silver',
        filter_queries = False,
        testing_only=testing_only,
        **ValidationConfig.TRAINING_ARGS
        )
    
    gold_data = save_data(
        level='gold',
        filter_queries = False, # should use same (updated) exclude list of queries as silver_data
        testing_only=testing_only,
        **ValidationConfig.TRAINING_ARGS
        )
    
    return all_data, silver_data, gold_data

if __name__ == '__main__':
    
    try:
        make_tiered_eval_data(index_path=None, testing_only=False)
    except Exception as e:
        logger.warning(e, exc_info=True)