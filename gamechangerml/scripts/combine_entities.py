import pandas as pd
from gamechangerml import DATA_PATH
import os

# simple script to combine agencies (orgs) and topics for ingestion
topics_path = os.path.join(DATA_PATH, "features", "topics_wiki.csv")
out_path = os.path.join(DATA_PATH, "features", "combined_entities.csv")
org_path = os.path.join(DATA_PATH, "features", "agencies.csv")
topics = pd.read_csv(topics_path)
orgs = pd.read_csv(org_path)
orgs.drop(columns=["Unnamed: 0"], inplace=True)
topics.rename(columns={"name": "entity_name",
              "type": "entity_type"}, inplace=True)
orgs.rename(columns={"Agency_Name": "entity_name"}, inplace=True)
orgs["entity_type"] = "org"

combined_ents = orgs.append(topics)
combined_ents.to_csv(out_path, index=False)
