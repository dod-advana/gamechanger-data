import argparse
import json
import os
import pandas as pd


def processPublications(devCorp, prodCorp, dir):
    catalog = []
    for filename in os.listdir(dir):
        if filename.endswith(".json"):
            with open(os.path.join(dir, filename)) as f:
                for line in f:
                    j = json.loads(line)
                    # publication variables
                    pubName = j["doc_name"]
                    pubNum = j["doc_num"]
                    pubType = j["doc_type"]
                    cac_required = j["cac_login_required"]
                    if "crawler_used" in j:
                        ingest_pipeline = j["crawler_used"]
                        update_frequency = "Every 3 days"
                    else:
                        ingest_pipeline = "Manual"
                        update_frequency = "N/A"

                    if pubName.split(",")[0] in devCorp:
                        avail_in_dev = True
                    else:
                        avail_in_dev = False

                    if pubName.split(",")[0] in prodCorp:
                        avail_in_prod = True
                    else:
                        avail_in_prod = False

                    catalog.append(
                        (
                            pubName,
                            pubNum,
                            pubType,
                            ingest_pipeline,
                            update_frequency,
                            cac_required,
                            avail_in_dev,
                            avail_in_prod,
                        )
                    )
    return pd.DataFrame(
        data=catalog,
        columns=[
            "Publication Name",
            "Publication Number",
            "Publication Type",
            "Ingest Pipeline (Crawler)",
            "Update Frequency",
            "CAC Login Required",
            "Avail In Dev",
            "Avail In Prod",
        ],
    )


def processDevCorpusList(dir):
    catalog = []
    for filename in os.listdir(dir):
        if filename.endswith(".json"):
            with open(os.path.join(dir, filename)) as f:
                j = json.load(f)
                catalog.append(j["id"].split(",")[0])
    return catalog


def processProdCorpusList(prod_file):
    catalog = []
    with open(prod_file) as f:
        for line in f:
            catalog.append(line[31:].split(",")[0])
    return catalog


def processDevCorpus(dir, crawler_df, prodCorp):
    df = crawler_df.copy()
    for filename in os.listdir(dir):
        if filename.endswith(".json"):
            with open(os.path.join(dir, filename)) as f:
                j = json.load(f)
                pubName = j["id"].split(",")[0]
                if (pubName in df["Publication Name"].values) == False:
                    pubNum = j["doc_num"]
                    pubType = j["doc_type"]
                    cac_required = True
                    ingest_pipeline = "Manual"
                    update_frequency = "N/A"
                    avail_in_dev = True
                    if pubName.split(",")[0] in prodCorp:
                        avail_in_prod = True
                    else:
                        avail_in_prod = False
                    df.append(
                        [
                            (
                                pubName,
                                pubNum,
                                pubType,
                                ingest_pipeline,
                                update_frequency,
                                cac_required,
                                avail_in_dev,
                                avail_in_prod,
                            )
                        ]
                    )
    return df


def processProdCorpus(prod_file, dev_df):
    df = dev_df.copy()
    with open(prod_file) as f:
        for line in f:
            pubName = line[31:].split(",")[0]
            if (pubName in df["Publication Name"].values) == False:
                if len(pubName.split(" ")) > 1:
                    pubNum = pubName.split(" ")[1]
                    pubType = pubName.split(" ")[0]
                    cac_required = True
                    ingest_pipeline = "Manual"
                    update_frequency = "N/A"
                    avail_in_dev = False
                    avail_in_prod = True
                    df.append(
                        [
                            (
                                pubName,
                                pubNum,
                                pubType,
                                ingest_pipeline,
                                update_frequency,
                                cac_required,
                                avail_in_dev,
                                avail_in_prod,
                            )
                        ]
                    )
    return df


def process(source, dev, prod):
    dev_corp_list = processDevCorpusList(dev)
    prod_corp_list = processProdCorpusList(prod)
    crawler_df = processPublications(dev_corp_list, prod_corp_list, source)
    dev_df = processDevCorpus(dev, crawler_df, prod_corp_list)
    total_df = processProdCorpus(prod, dev_df)
    return total_df


def parse_args():
    parser = argparse.ArgumentParser(
        description="This program processes document JSONs into neo4j insert statements."
    )
    parser.add_argument(
        "-source",
        "-s",
        action="store",
        help="A source directory of crawler output files.",
        required=True,
    )
    parser.add_argument(
        "-dev", "-d", action="store", help="Dev File Directory Corpus.",
    )
    parser.add_argument(
        "-prod", "-p", action="store", help="Text list of doc names in prod.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = process(args.source, args.dev, args.prod)
    df.to_csv("publication_corpus.csv")
