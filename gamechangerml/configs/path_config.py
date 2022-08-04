from os.path import join
from gamechangerml import DATA_PATH, MODEL_PATH


class PathConfig:
    """Configurations for repository paths."""
    
    DATA_DIR = DATA_PATH
    LOCAL_MODEL_DIR = MODEL_PATH
    TRANSFORMER_PATH = join(MODEL_PATH, "transformers")
