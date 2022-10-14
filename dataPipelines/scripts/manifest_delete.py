####################################################################################################### /
# This script parses a cumulative_manifest json file and deletes rows that
# contain specific version hashes.
#######################################################################################################s

import jsonlines

manifest_path = '<path/to/manifest/file>'
crawler_output_path = '<path/to/crawler/output/file>'

data = []


def load_json():
    with jsonlines.open(manifest_path, 'r') as f:
        for line in f.iter(skip_invalid=True):
            data.append(line)


def delete_records():
    with jsonlines.open(crawler_output_path, 'r') as f:
        records_to_remove = []
        for line in f.iter(skip_invalid=True):
            records_to_remove.append(line)

        '''remove records through version_hash'''
        values_to_remove = [item['version_hash'] for item in records_to_remove]
        updated_records = [item for item in data if item['version_hash'] not in values_to_remove]

        return values_to_remove, updated_records


def write_output_manifest():
    with jsonlines.open('cumulative_manifest_updated.json', 'w') as f:
        f.write_all(updated_records)


load_json()
values_to_remove, updated_records = delete_records()
delete_records()
write_output_manifest()

print('\n')
print('Original Cumulative Manifest Records: ' + str(len(data)))
print('Updated Cumulative Manifest Records: ' + str(len(updated_records)))
print('\n')
