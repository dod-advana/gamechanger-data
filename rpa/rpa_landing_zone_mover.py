import boto3
import tempfile
from zipfile import ZipFile
from io import BytesIO
from notification import slack
import json
import typing
import datetime
import traceback


def notify_with_tb(msg, tb):
    full = msg + '\n' + tb
    slack.send_notification(full)


s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

source_bucket = "advana-data-zone"
source_prefix = "bronze/gamechanger/rpa-landing-zone/"

destination_bucket = "advana-data-zone"


def filter_and_move():
    """
        Ingest zip files from rpa landing zone
        Filter them based on cumulative manifest
        Place in external uploads

        Things that happen in this function...
            retrieve zips from s3
        for each zip, without downloading file, create zip obj ->
            read manifest.json for crawler used, metadata lines and version hashes
            get cumulative manifest for crawler used
            read through zip obj for metadata files, filter previous hashes from cumulative manifest (like scrapy does)
            create corrected manifest (matching what a scrapy crawler wouldve downloaded)
            upload all new files, metadata, and corrected manifest
            copy old cumulative manifest if exists, add new lines to new manifest
            rename old cumulative manifest with datetime
            upload new manifest
            delete zip from rpa landing zone

        any error - delete the created external-uploads/crawler-downloader/{external_uploads_dt} bucket and dont delete the zip from rpa landing zone
    """
    print('starting filter and move')
    print('fetching zips...')
    zips_as_s3_objs = get_filename_s3_obj_map()
    print('objs :', zips_as_s3_objs.values())
    for zip_filename, s3_obj in zips_as_s3_objs.items():
        print('checking', zip_filename)
        # archive keeps the original filename so zip_filename irrelevant when searching in the zip but it is useful for identifying the zip name

        external_uploads_dt = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        destination_prefix_dt = f"bronze/gamechanger/external-uploads/crawler-downloader/{external_uploads_dt}"
        # set prefix dt per zip so multiple zips dont end up in the same timestamped output

        crawler_used = None
        try:
            # create in memory zip file object
            with create_zip_obj(s3_obj) as zf:
                zip_names = zf.namelist()
                # in archive base name (ie the original folder name when zipped)
                base_dir = base_dir_heuristic(zip_names)

                corrected_manifest_jdocs: typing.List[dict] = []
                # immediately try to upload this so it will error if not in the archive
                upload_file_from_zip(
                    zf_ref=zf, zip_filename=f'{base_dir}crawler_output.json', prefix=destination_prefix_dt)

                # get crawler name from manifest file
                try:
                    with zf.open(f'{base_dir}manifest.json') as manifest:

                        for line in manifest.readlines():
                            jsondoc = json.loads(line)
                            if not crawler_used:
                                crawler_used = jsondoc['crawler_used']
                            if jsondoc.get('entry_type', None):
                                # reading through all of the manifest to get the metadata lines... :/
                                corrected_manifest_jdocs.append(jsondoc)

                except:
                    msg = f"[ERROR] RPA Landing Zone Mover failed to handle manifest file, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename}"
                    notify_with_tb(msg, traceback.format_exc())
                    # skip to next zip
                    continue

                if not crawler_used:
                    msg = f"[ERROR] RPA Landing Zone Mover failed to discover crawler_used, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename} \n(check manifest.json)"
                    slack.send_notification(msg)
                    # skip to next zip
                    continue

                previous_hashes, cmltv_manifest_s3_obj, cmltv_manifest_lines = get_previous_manifest_for_crawler(
                    crawler_used)

                not_in_previous_hashes = set()

                for name in zip_names:
                    if name.endswith('.metadata'):
                        with zf.open(name) as metadata:
                            jsondoc = json.loads(metadata.readline())

                            version_hash = jsondoc.get('version_hash', None)
                            if version_hash and not version_hash in previous_hashes:
                                not_in_previous_hashes.add(name)
                                corrected_manifest_jdocs.append(jsondoc)

                    for to_move_meta in not_in_previous_hashes:
                        zip_filename = to_move_meta.replace('.metadata', '')

                        if zip_filename in zip_names:
                            upload_file_from_zip(
                                zf_ref=zf, zip_filename=zip_filename, prefix=destination_prefix_dt)
                            upload_file_from_zip(
                                zf_ref=zf, zip_filename=to_move_meta, prefix=destination_prefix_dt)

                upload_jsonlines(
                    lines=corrected_manifest_jdocs, filename='manifest.json', prefix=destination_prefix_dt)

                # the manifest from rpa is everything because it can't determine previous hashes before downloading
                # need to make a corrected one from filtered hashes (like scrapy does)
                with tempfile.TemporaryFile(mode='r+', encoding="UTF-8") as new_manifest:
                    # new crawlers wont have existing cumulative manifest
                    if cmltv_manifest_s3_obj:

                        # copy old cumulative manifest lines into new manifest file
                        for jsondoc in cmltv_manifest_lines:
                            line = json.dumps(jsondoc) + '\n'
                            new_manifest.write(line)

                        # s3 copy old cumulative manifest to a new name before overwriting
                        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_filename = f'cumulative-manifest.{ts}.json'
                        backup_prefix = get_cumulative_manifest_prefix(crawler_used).replace(
                            'cumulative-manifest.json', backup_filename)
                        s3.Object(destination_bucket, backup_prefix).copy_from(
                            CopySource={'Key': cmltv_manifest_s3_obj.key,
                                        'Bucket': cmltv_manifest_s3_obj.bucket_name}
                        )

                    for jsondoc in corrected_manifest_jdocs:
                        line = json.dumps(jsondoc) + '\n'
                        new_manifest.write(line)

                    # rewind file to top so there is data to read for put_object
                    new_manifest.seek(0)

                    key = get_cumulative_manifest_prefix(crawler_used)
                    s3_client.put_object(
                        Body=new_manifest.buffer,
                        Bucket=destination_bucket,
                        Key=key
                    )

        except:
            msg = f"[ERROR] RPA Landing Zone mover failed while handling the following:\n {source_bucket}/{s3_obj.key}"
            notify_with_tb(msg, traceback.format_exc())

            try:
                undo_uploads(prefix=destination_prefix_dt)
            except:
                msg = '[ERROR] Failed undo_uploads'
                notify_with_tb(msg, traceback.format_exc())

            continue

        # if no errors, go ahead and delete the zip so it won't be picked up again
        s3_obj.delete()


def base_dir_heuristic(zip_names: list):
    dirs = [zn for zn in zip_names if zn.endswith("/")]
    if len(dirs) == 0:
        print(f'no dirs detected, attempting just filenames from {zip_names}')
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


def undo_uploads(prefix):
    s3.Bucket(destination_bucket).objects.filter(Prefix=prefix).delete()


def get_cumulative_manifest_prefix(crawler_used):
    return f"bronze/gamechanger/data-pipelines/orchestration/crawlers_rpa/{crawler_used}/cumulative-manifest.json"


def get_previous_manifest_for_crawler(crawler_used) -> typing.Tuple[set, typing.Union[None, object]]:
    previous_hashes = set()
    manifest_s3_obj = None
    lines = None
    try:
        key = get_cumulative_manifest_prefix(crawler_used)
        s3_obj = s3.Object(source_bucket, key)
        lines = s3_obj.get()['Body'].read().decode(
            'utf-8').splitlines()
        if lines:
            for line in lines:
                jsondoc = json.loads(line)
                version_hash = jsondoc.get('version_hash', None)
                if version_hash:
                    previous_hashes.add(version_hash)

            # only set it if it has lines, would still be an Object otherwise
            manifest_s3_obj = s3_obj

    except s3_client.exceptions.NoSuchKey:
        msg = f"[WARN] No cumulative-manifest found for {crawler_used}, a new one will be created"
        slack.send_notification(msg)
    except Exception as e:
        msg = f"[ERROR] Unexpected error occurred getting previous manifest for crawler: {crawler_used}"
        notify_with_tb(msg, traceback.format_exc())
        raise e

    finally:
        return (previous_hashes, manifest_s3_obj, lines)


def get_filename_s3_obj_map() -> typing.Dict[str, object]:
    out = {}
    for obj in s3.Bucket(source_bucket).objects.filter(Prefix=source_prefix):
        if obj.key.endswith('.zip'):
            print('found', obj.key)
            _, __, name_with_ext = obj.key.rpartition('/')
            filename, *_ = name_with_ext.rpartition('.')
            out[filename] = obj
    return out


def create_zip_obj(s3_obj) -> ZipFile:
    body_bytes = s3_obj.get()['Body'].read()
    bytes_obj = BytesIO(body_bytes)
    zf = ZipFile(bytes_obj, 'r')
    return zf


def upload_file_from_zip(zf_ref, zip_filename, prefix, bucket=destination_bucket):
    with zf_ref.open(zip_filename, "r") as f:
        _, __, filename = zip_filename.rpartition('/')
        s3_client.upload_fileobj(
            f, bucket, f"{prefix}/{filename}")


def upload_jsonlines(lines, filename, prefix, bucket=destination_bucket):
    with tempfile.TemporaryFile(mode='r+') as new_file:
        for line in lines:
            jsondoc = json.dumps(line) + '\n'
            new_file.write(jsondoc)

        new_file.seek(0)
        key = f"{prefix}/{filename}"

        s3_client.put_object(
            Body=new_file.buffer,
            Bucket=bucket,
            Key=key
        )


if __name__ == '__main__':
    filter_and_move()
