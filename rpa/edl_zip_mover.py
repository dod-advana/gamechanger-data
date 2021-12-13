import subprocess
import os
import re

allowed_ids = [
    allowed_id.strip() for allowed_id in
    os.environ.get('ALLOWED_IDS_CSV_STRING', '').split(',')
]

idens = "|".join(allowed_ids)
allowed_re = re.compile(f'.*({idens}).*')

source_bucket = "advana-landing-zone/"
destination_bucket = "advana-data-zone/"

source_path = f"{source_bucket}edl/non-sensitive/Gamechanger RPA/"
destination_path = f"{destination_bucket}bronze/gamechanger/rpa-landing-zone/"


def move_zips():
    if not allowed_ids:
        print(
            'ALLOWED_IDS_CSV_STRING not set, exiting because nothing would be let through')
        exit(1)

    cmd = f'aws s3 ls --recursive {source_path}'.split()
    try:
        file_list = [
            line.decode().split() for line
            in subprocess.check_output(cmd).splitlines()
        ]
        to_move = []
        for s3_line in file_list:
            try:
                filename = s3_line[3]
                if allowed_re.match(filename) and not filename.endswith('/'):
                    to_move.append(filename)
            except IndexError:
                # skip empty names, wont have the 3 index
                continue

        for filename in to_move:
            try:
                file_from = f"{source_bucket}{filename}"
                file_to = f"{destination_path}"
                dryrun = ' --dryrun' if os.environ.get('DRY_RUN', None) else ''
                cmd = f'aws s3 mv s3://{file_from} s3://{file_to}{dryrun}'.split()
                res = subprocess.check_output(cmd)
                print('mv response', res)
            except (subprocess.CalledProcessError, OSError) as e:
                print(f'Error trying to move {filename}\n\n', e)

    except (subprocess.CalledProcessError, OSError) as e:
        return 'ERROR GETTING RPA FILES'


if __name__ == "__main__":
    move_zips()
