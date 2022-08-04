import os
from . import REPO_ROOT

class Config:
    # ML MODEL PATH
    LOCAL_PACKAGED_MODELS_DIR = os.environ.get(
        "GC_ML_API_MODEL_PARENT_DIR", default=REPO_ROOT.joinpath("models")
    )
    S3_MODELS_DIR = "models/v3/"
