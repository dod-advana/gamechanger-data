import pandas as pd

# simple script to combine agencies (orgs) and topics for ingestion
topics_path = "dataScience/data/topics_wiki.csv"
out_path = "dataScience/data/combined_entities.csv"
org_path = "dataScience/data/agencies/agencies_in_corpus.csv"
topics = pd.read_csv(topics_path)
orgs = pd.read_csv(org_path)
orgs.drop(columns=["Unnamed: 0"], inplace=True)
topics.rename(columns={"name": "entity_name",
              "type": "entity_type"}, inplace=True)
orgs.rename(columns={"Agency_Name": "entity_name"}, inplace=True)
orgs["entity_type"] = "org"

combined_ents = orgs.append(topics)
combined_ents.to_csv(out_path, index=False)
