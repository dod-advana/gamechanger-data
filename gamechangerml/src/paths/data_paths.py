from os.path import join
from pathlib import Path
from gamechangerml import DATA_PATH, REPO_PATH, MODEL_PATH

# features
FEATURES_DATA_DIR = join(DATA_PATH, "features")
POPULAR_DOCUMENTS_FILE = Path(join(FEATURES_DATA_DIR, "popular_documents.csv"))
COMBINED_ENTITIES_FILE = Path(join(FEATURES_DATA_DIR, "combined_entities.csv"))
TOPICS_FILE = join(FEATURES_DATA_DIR, "topics_wiki.csv")
ORGS_FILE = join(FEATURES_DATA_DIR, "agencies.csv")
ABBREVIATIONS_FILE = join(FEATURES_DATA_DIR, "abbreviations.json")
ABBREVIATIONS_COUNTS_FILE = join(FEATURES_DATA_DIR, "abbcounts.json")

# features/generated_files
FEATURES_GENERATED_FILES_DIR = join(FEATURES_DATA_DIR, "generated_files")
PROD_DATA_FILE = join(FEATURES_DATA_DIR, "prod_test_data.csv")
CORPUS_META_FILE = join(FEATURES_GENERATED_FILES_DIR, "corpus_meta.csv")
COMMON_ORGS_FILE = join(FEATURES_GENERATED_FILES_DIR, "common_orgs.csv")

# user_data
USER_DATA_DIR = join(DATA_PATH, "user_data")

# user_data/search_history
SEARCH_HISTORY_DIR = join(USER_DATA_DIR, "search_history")
SEARCH_PDF_MAPPING_FILE = join(SEARCH_HISTORY_DIR, "SearchPdfMapping.csv")
USER_AGGREGATIONS_FILE = join(SEARCH_HISTORY_DIR, "UserAggregations.json")

# user_data/matomo_feedback
MATOMO_FEEDBACK_DIR = join(USER_DATA_DIR, "matomo_feedback")

# training
TRAIN_DIR = join(DATA_PATH, "training")
SENT_TRANSFORMER_TRAIN_DIR = join(TRAIN_DIR, "sent_transformer")

# validation
VALIDATION_DIR = join(DATA_PATH, "validation")
SENT_TRANSFORMER_VALIDATION_DIR = join(VALIDATION_DIR, "domain", "sent_transformer")

# evaluation
EVALUATION_DIR = join(DATA_PATH, "evaluation")

# ltr
LTR_DATA_DIR = join(DATA_PATH, "ltr")

# models
DEFAULT_SENT_INDEX = join(MODEL_PATH, "sent_index_20210715")
TRANSFORMERS_DIR = join(MODEL_PATH, "transformers")

# corpus
CORPUS_DIR = join(REPO_PATH, "gamechangerml", "corpus")
