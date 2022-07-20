import pandas as pd
import os
from gamechangerml import DATA_PATH

popular_df = pd.read_csv(os.path.join(DATA_PATH, "features", "popular_documents.csv"))
