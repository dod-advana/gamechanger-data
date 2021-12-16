import os
import re
import boto3

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

destination_bucket = "advana-data-zone"

environ_ids = os.environ.get('ALLOWED_IDS_CSV_STRING', None)
allowed_ids = []
if environ_ids:
    allowed_ids = [
        allowed_id.strip() for allowed_id in environ_ids.split(',')
    ]

idens = "|".join(allowed_ids)
allowed_ids_re = re.compile(f'.*(?P<ids>{idens}).*')

source_bucket = "advana-landing-zone"
destination_bucket = "advana-data-zone"

source_prefix = "edl/non-sensitive/Gamechanger RPA"
destination_prefix = "bronze/gamechanger/rpa-landing-zone"


def move_zips():
    try:
        if not allowed_ids:
            print(
                'ALLOWED_IDS_CSV_STRING env var not set, it should be a comma separated string of user ids, exiting because nothing would be let through')
            exit(1)

        for obj in s3.Bucket(source_bucket).objects.filter(Prefix=source_prefix):
            print(
                f'checking s3 object: {source_bucket}/{obj.key}')

            ids = []
            id_matches = allowed_ids_re.match(obj.key)

            if id_matches:
                ids = id_matches.group('ids')

            if obj.key.endswith('.zip') and ids:
                try:

                    _, __, name_with_ext = obj.key.rpartition('/')
                    if not name_with_ext:
                        return

                    copy_source = {
                        'Bucket': source_bucket,
                        'Key': obj.key
                    }
                    print(
                        f'copy {name_with_ext} to {destination_bucket}/{destination_prefix}')
                    s3.meta.client.copy(
                        copy_source,
                        destination_bucket,
                        f"{destination_prefix}/{name_with_ext}"
                    )
                    print(f'deleting {source_bucket}/{obj.key}')
                    obj.delete()

                except Exception as e:
                    print(
                        f'Error copying {obj.key} to {destination_prefix}/{destination_prefix}', e)

    except Exception as e:
        print('rpa.edl_zip_mover.move_zips() unexpected error:', e)


if __name__ == "__main__":
    move_zips()
