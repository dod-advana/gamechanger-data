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
    print("Downloading Legislation dataset")

    legislation_base_url = "https://s3.amazonaws.com/pp-projects-static/congress/bills/"

    congress_list = [x+93 for x in range(0,23)] # Starting with the 93rd Congress

    for congress in congress_list:

        download_url = legislation_base_url + str(congress)+ ".zip"

        r = requests.get(download_url, allow_redirects=True)

        with open(staging_folder + str(congress) + ".zip", "wb") as leg_dataset:
            leg_dataset.write(r.content)
        filename = str(congress) + ".zip"
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        manifest_dic = {
            "entry_type": "file",
            "entrypoint": "https://s3.amazonaws.com/pp-projects-static/congress/bills/",
            "filename": filename,
            "md5_hash": filename_hash,
            "origin": download_url,
            "version_hash": filename_hash,
        }

        print(manifest_dic)
        with open(staging_folder + str(congress)+"_manifest.json", "w") as manifest_file:
            json.dump(manifest_dic, manifest_file)

        print("Completed Downloading Legilsation History dataset")
