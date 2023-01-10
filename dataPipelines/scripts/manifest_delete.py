# -----------------------------------------------------------------------------
# This script reads in two json files, cumulative_manifest and crawler_output,
# and deletes records from the manifest that are linked with unwanted version 
# hashes listed in the crawler_output file. Output is a new cumulative_manifest 
# file with desired data.
# 
# Intended to be used together with the gather_crawler_output script.
# -----------------------------------------------------------------------------

import jsonlines
from datetime import datetime

def delete_manifest_records(manifest_path, crawler_output_path):
    with jsonlines.open(manifest_path, 'r') as f1:
        with jsonlines.open(crawler_output_path, 'r') as f2:
            
            # Read the cumulative_manifest file line by line and add each record into a list of dictionaries
            manifest = [line for line in f1.iter(skip_invalid=True)] 
            
            # Read the crawler_output file and extract the version_hashes that are to be removed/excluded into a new list
            version_hash_to_del = {line['version_hash'] for line in f2.iter(skip_invalid=True)} 
            
            # Create a new set of records that does not contain any of the excluded version_hashes. Any duplicate records are also removed
            updated_manifest = {frozenset(line.items()) : line for line in manifest if line['version_hash'] not in version_hash_to_del}.values()

    return manifest, updated_manifest

def output_updated_manifest(updated_manifest):
    date = datetime.now().strftime('%Y%m%d')
    with jsonlines.open(f'cumulative_manifest_updated_{date}.json', 'w') as f: 
        f.write_all(updated_manifest)

if __name__ == '__main__':
    manifest_path = '<path/to/manifest/file>' # Change to desired file path of cumulative_manifest json
    crawler_output_path = '<path/to/crawler/output/file>' # Change to desired file path of crawler_output json
    manifest, updated_manifest = delete_manifest_records(manifest_path, crawler_output_path)
    output_updated_manifest(updated_manifest)

    print('\n')
    print('Original Cumulative Manifest Records: ' + str(len(manifest)))
    print('Updated Cumulative Manifest Records: ' + str(len(updated_manifest)))
    print('Number of Records Deleted: ' + str((len(manifest) - len(updated_manifest))))
    print('\n')