## pip install wikipedia
import wikipedia
from datetime import date
import pandas as pd
import argparse
import os
from gamechangerml import DATA_PATH

def lookup_wiki_summary(query):
    try:
        return wikipedia.summary(query).replace("\n", "")
    except:
        print(f"Could not retrieve description for {query}")
        return ""

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Getting entity descriptions")
    
    parser.add_argument("--filepath", "-p", dest="filepath", help="path to csv with entities")

    args = parser.parse_args()

    if args.filepath:
        entities_filepath = args.filepath
    else:
        entities_filepath = os.path.join(DATA_PATH, "features", "combined_entities.csv")
    df = pd.read_csv(entities_filepath)
    df['information'] = df['entity_name'].apply(lambda x: lookup_wiki_summary(x))
    df['information_source'] = "Wikipedia"
    df['information_retrieved'] = date.today().strftime("%Y-%m-%d")
    df.to_csv(entities_filepath)

    print(f"Saved csv to {entities_filepath}")