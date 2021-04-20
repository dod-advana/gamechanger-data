import click
import requests
from datetime import datetime, timedelta
import json
import hashlib


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    '--staging-folder',
    help="Staging folder",
    required=True
)
def run(staging_folder: str) -> None:
    print("Downloading Covd dataset")

    covd_base_url = "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases/"
    days_to_subtract = 1
    covd_download_date = datetime.today() - timedelta(days=days_to_subtract)
    d1 = covd_download_date.strftime("%Y-%m-%d")
    download_url = covd_base_url + "cord-19_" + d1 + ".tar.gz"

    r = requests.get(download_url, allow_redirects=True)

    with open(staging_folder + "/covid_19.tar.gz", "wb") as covd_dataset:
        covd_dataset.write(r.content)
    filename = "cord-19_" + d1 + ".tar.gz"
    filename_hash = hashlib.md5(filename.encode()).hexdigest()
    manifest_dic = {
        "entry_type": "file",
        "entrypoint": "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/historical_releases.html",
        "filename": "cord-19_" + d1 + ".tar.gz",
        "md5_hash": filename_hash,
        "origin": download_url,
        "version_hash": filename_hash,
    }

    print(manifest_dic)
    with open(staging_folder + "/manifest.json", "w") as manifest_file:
        json.dump(manifest_dic, manifest_file)

    print("Completed Downloading Covd dataset")
