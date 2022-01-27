from cmath import e
from turtle import clone
import boto3
from zipfile import ZipFile
from io import BytesIO
import datetime
from notification.slack import send_notification, notify_with_tb
import traceback
from textwrap import dedent

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

source_bucket = "advana-data-zone"
destination_bucket = "advana-data-zone"

source_prefix = "advana-landing-zone/non-sensitive/Gamechanger Clones"
destination_base_prefix = "bronze/gamechanger/clone_mover_landing_zone"
errored_destination_base_prefix = "bronze/gamechanger/clone_mover_landing_zone_errored"

NAME_FILE = "clone-name.txt"

# Fetch zips from s3 (advana-landing-zone/non-sensitive/Gamechanger Clones)
# Read zip for file that has crawler_used info
# Fetch previous manifest for that crawler
# Filter previously seen files
# Move new files to external uploads


def base_dir_heuristic(zip_names: list):
    dirs = [zn for zn in zip_names if zn.endswith("/")]
    if len(dirs) == 0:
        print(f'no dirs detected, attempting just filenames from zf.namelist()')
        return ''
    elif len(dirs) == 1:
        return dirs[0]
    else:
        base_dirs = []
        for zdir in dirs:
            count = 0
            for letter in zdir:
                if letter == '/':
                    count += 1
                if count > 1:
                    break

        if len(base_dirs) == 1:
            return base_dirs[0]
        else:
            raise RuntimeError(
                f'More than one dir detected in zip, cant find root dir from: {base_dirs}')


def unzip_and_move():
    try:
        # for each zip in the bucket
        for s3_obj in s3.Bucket(source_bucket).objects.filter(Prefix=source_prefix):
            if s3_obj.key.endswith('.zip'):
                print(f"Looking at {s3_obj.key}")
                body_bytes = s3_obj.get()['Body'].read()
                bytes_obj = BytesIO(body_bytes)
                clone_name = None
                base_dir = ''
                # get the clone name to make destination for files
                with ZipFile(bytes_obj, 'r') as zf:
                    # skip OS prefixed names
                    # this is zf.nameslist() example from local zip
                    #   ['clone_mover_test/',
                    #   'clone_mover_test/DoD365LaptopTabletUserGuide_v30Apr2021.pdf',
                    #    '__MACOSX/clone_mover_test/._DoD365LaptopTabletUserGuide_v30Apr2021.pdf']
                    zip_names = [
                        n for n in zf.namelist() if n.startswith(base_dir)
                    ]
                    # in archive base name (ie the original folder name when zipped)
                    base_dir = base_dir_heuristic(zip_names)
                    print(f'base dir is {base_dir} in {s3_obj.key}')

                    # find and read NAME_FILE in zip
                    zipped_name_filepath = f'{base_dir}{NAME_FILE}'
                    try:
                        with zf.open(zipped_name_filepath) as cnf:
                            clone_name = str(cnf.readline(), 'ascii').strip()
                    except:
                        msg = f"[ERROR] EDL Clone Mover failed opening clone name file {zipped_name_filepath}, skipping:\n {source_bucket}/{s3_obj.key}"
                        notify_with_tb(msg, traceback)
                        # skip to next zip
                        continue

                    if not clone_name:
                        print("No clone name found in {NAME_FILE}")
                        continue

                    print(f'{s3_obj.key} clone name is {clone_name}')

                    destination_prefix = f"{destination_base_prefix}/{clone_name}"
                    upload_errors = []

                    # move each file into destination
                    for zip_filename in zip_names:
                        try:
                            with zf.open(zip_filename) as f:
                                _, __, filename = zip_filename.rpartition('/')
                                s3_client.upload_fileobj(
                                    f, destination_bucket, f"{destination_prefix}/{filename}")
                        except Exception as e:
                            upload_errors.append(f"{zip_filename} - {e}")

                    should_delete = True
                    if upload_errors:
                        # Quarantine zip into errored bucket so files arent lost even though they werent all moved
                        err_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                        error_destination_prefix = f"{errored_destination_base_prefix}/{clone_name}/{err_time}-{s3_obj.key}"
                        send_notification(
                            dedent(
                                f"""Error(s) unpacking and uploading file(s) from {source_bucket}/{s3_obj.key} to {destination_bucket}/{destination_prefix}
                                !! source zip WILL NOT be deleted automatically - moving to {destination_bucket}/{error_destination_prefix}
                                {upload_errors}"""
                            ))
                        try:
                            s3.Object(destination_bucket, error_destination_prefix).copy_from(
                                CopySource={'Key': s3_obj.key,
                                            'Bucket': source_bucket}
                            )
                        except Exception as e:
                            should_delete = False
                            send_notification(
                                f"Error moving {source_bucket}/{s3_obj.key} to {destination_bucket}/{error_destination_prefix}, object will not be deleted")

                    if should_delete:
                        s3_obj.delete()

    except Exception as e:
        print('gc_clone_maker.clone_zip_mover.unzip_and_move() unexpected error:', e)


if __name__ == "__main__":
    unzip_and_move()
