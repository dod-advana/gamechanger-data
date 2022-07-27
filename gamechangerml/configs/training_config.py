from os.path import join
from gamechangerml import DATA_PATH


class TrainingConfig:
    """Configurations for model training."""

    TRAINING_DATA_DIR = join(DATA_PATH, "training")
  
    TRAIN_TEST_SPLIT_RATIO = 0.8
  
