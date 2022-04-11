import boto3
import tempfile
from zipfile import ZipFile
from io import BytesIO
from notification import slack
import json
import typing
import datetime
import traceback
import codecs
import io


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
            in_memory_zip = create_byte_obj(s3_obj)

            with ZipFile(in_memory_zip, 'r') as zf:
                zip_names = zf.namelist()
                # in archive base name (ie the original folder name when zipped)
                base_dir = base_dir_heuristic(zip_names)

                corrected_manifest_jdocs: typing.List[dict] = []
                # immediately try to upload this so it will error if not in the archive
                upload_file_from_zip(
                    zf_ref=zf, zip_filename=f'{base_dir}crawler_output.json', prefix=destination_prefix_dt, convert_sig=True)

                # get crawler name from manifest file
                try:
                    with zf.open(f'{base_dir}manifest.json') as manifest:

                        for line in io.TextIOWrapper(manifest, encoding="utf-8-sig"):
                            jsondoc = json.loads(line)
                            if not crawler_used:
                                crawler_used = jsondoc['crawler_used']
                            if jsondoc.get('entry_type', None):
                                # reading through all of the manifest to get the metadata lines... :/
                                corrected_manifest_jdocs.append(jsondoc)

                except:
                    print(msg)
                    msg = f"[ERROR] RPA Landing Zone Mover failed to handle manifest file, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename}"
                    notify_with_tb(msg, traceback.format_exc())
                    # skip to next zip
                    continue

                if not crawler_used:
                    print(msg)
                    msg = f"[ERROR] RPA Landing Zone Mover failed to discover crawler_used, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename} \n(check manifest.json)"
                    slack.send_notification(msg)
                    # skip to next zip
                    continue

                previous_hashes, cmltv_manifest_s3_obj, cmltv_manifest_lines = get_previous_manifest_for_crawler(
                    crawler_used)

                not_in_previous_hashes = set()

                # sorting through the version hashes and checking for new files
                for name in zip_names:
                    if name.endswith('.metadata'):
                        try:
                            with zf.open(name) as metadata:
                                metadata_str = next(
                                    io.TextIOWrapper(
                                        metadata, encoding="utf-8-sig")
                                )

                            jsondoc = json.loads(metadata_str)
                            version_hash = jsondoc.get(
                                'version_hash', None)
                        except Exception as e:
                            print(
                                f"WARNING: metadata file errored on load. Skipping", name, '::', e)
                            continue
                        # only getting docs that aren't in previous hashes
                        if version_hash and not version_hash in previous_hashes:
                            not_in_previous_hashes.add(name)
                            corrected_manifest_jdocs.append(jsondoc)

                            # upload all of the files not in previous version hashes to s3
                            zip_filename = name.replace(
                                '.metadata', '')  # name of the main file

                            # make sure file the metadata is for is actually available to send
                            if zip_filename in zip_names:
                                # upload the main file, don't convert
                                upload_file_from_zip(
                                    zf_ref=zf, zip_filename=zip_filename, prefix=destination_prefix_dt, convert_sig=False)
                                # upload the metadata
                                upload_jsonlines(
                                    lines=[jsondoc], filename=name, prefix=destination_prefix_dt)

                # upload the manifest file after getting all metadata jdocs
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
        print('get_previous_manifest_for_crawler lines count', len(lines))
        if lines:
            count = 0
            for line in lines:
                jsondoc = json.loads(line)
                if count < 5 and type(jsondoc) == str:
                    print(
                        'string type jsondoc: jsondoc[0:20], jsondoc[-20:] ->', jsondoc[0:20], jsondoc[-20:])
                else:
                    version_hash = jsondoc.get('version_hash', None)
                    if version_hash:
                        previous_hashes.add(version_hash)

            # only set it if it has lines, would still be an Object otherwise
            manifest_s3_obj = s3_obj

    except s3_client.exceptions.NoSuchKey:
        msg = f"[WARN] No cumulative-manifest found for {crawler_used}, a new one will be created"
        slack.send_notification(msg)
        return (previous_hashes, manifest_s3_obj, lines)
    except Exception as e:
        msg = f"[ERROR] Unexpected error occurred getting previous manifest for crawler: {crawler_used}"
        notify_with_tb(msg, traceback.format_exc())
        raise e

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


def create_byte_obj(s3_obj):
    body_bytes = s3_obj.get()['Body'].read()
    bytes_obj = BytesIO(body_bytes)
    return bytes_obj


def upload_file_from_zip(zf_ref, zip_filename, prefix, bucket=destination_bucket, convert_sig=False):
    with zf_ref.open(zip_filename, "r") as f:
        _, __, filename = zip_filename.rpartition('/')

        if convert_sig:
            data = io.TextIOWrapper(f, encoding="utf-8-sig")
        else:
            data = f

        s3_client.upload_fileobj(
            data, bucket, f"{prefix}/{filename}")


def upload_jsonlines(lines: typing.List[dict], filename: str, prefix: str, bucket=destination_bucket):
    """
    This function takes in a list of jsons and puts it into an s3 location with the appropriate filename
    :param lines: the list of json-readable lines to be uploaded as a single file to s3
    :param filename: name of the file the jsons will be written into and uploaded in
    :param prefix: prefix to upload to in s3
    :param bucket: bucket to upload to in s3
    """
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
