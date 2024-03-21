import boto3
import tempfile
from zipfile import ZipFile
from io import BytesIO
from notification import slack
from notification.slack import notify_with_tb
import json
import typing
import datetime
import traceback
import codecs


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
        constZip_filename = zip_filename # zip_filename gets reassigned, this is to keep the value throughout
        print('\nchecking', zip_filename, '.zip')
        # archive keeps the original filename so zip_filename irrelevant when searching in the zip but it is useful for identifying the zip name

        external_uploads_dt = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        destination_prefix_dt = f"bronze/gamechanger/external-uploads/crawler-downloader/{external_uploads_dt}"
        # set prefix dt per zip so multiple zips dont end up in the same timestamped output

        crawler_used = None

        # """
        # zip folder needs to follow this format!!!:
        # 
        # in s3, there needs to be a exampleName.zip
        # inside the folder, needs to contain the same exampleName folder.
        # example --> exampleName.zip/exampleName/ and the exampleName folder needs to house the following:
        # crawler_output.json, pdf/html + .metadata and manifest.json
        # """

        try:
            # create in memory zip file object
            in_memory_zip = create_byte_obj(s3_obj)

            with ZipFile(in_memory_zip, 'r') as zf: # zf -> zip files
                file_names = zf.namelist()

                print('file names -> ' , file_names)

                base_dir = base_dir_heuristic(file_names)
                if not base_dir:
                    print('improper file zip structure, no base dir. skipping ', zip_filename, '.zip \n')
                    continue # Skip to next zip
                else:
                    print('base_dir --> ', base_dir)

                corrected_manifest_jdocs: typing.List[dict] = []

                # immediately upload this so it will error if not in the archive
                crawler_output_loc = f'{base_dir}crawler_output.json' # test/crawler_output.json required format
                if crawler_output_loc == '': 
                    'crawler_output.json not found, stopping execution'
                    continue 

                upload_file_from_zip(
                    zf_ref=zf, zip_filename=crawler_output_loc, prefix=destination_prefix_dt, bucket=destination_bucket, base_dir=base_dir)
                print('successfully created ', external_uploads_dt, 'at ', destination_prefix_dt)

                # get crawler name from manifest file
                # test prefix manifest source 2024-03-07T10:30:01/
                try:
                    with zf.open(f'{base_dir}manifest.json') as manifest: # test/manifest.json required format
                        print('manifest found in zip to compare')
                        for line in manifest.readlines():
                            # decode the line in the manifest files
                            line = codecs.decode(line, 'utf-8-sig')
                            jsondoc = json.loads(line)
                            if not crawler_used:
                                crawler_used = jsondoc['crawler_used']
                            if jsondoc.get('entry_type', None):
                                # reading through all of the manifest to get the metadata lines... :/
                                corrected_manifest_jdocs.append(jsondoc)

                except:
                    msg = f"[ERROR] RPA Landing Zone Mover failed to handle manifest file, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename}"
                    notify_with_tb(msg, traceback)
                    # skip to next zip
                    continue

                if not crawler_used:
                    msg = f"[ERROR] RPA Landing Zone Mover failed to discover crawler_used, skipping:\n {source_bucket}/{s3_obj.key} > {zip_filename} \n(check manifest.json)"
                    slack.send_notification(msg)
                    # skip to next zip
                    continue

                previous_hashes, cmltv_manifest_s3_obj, cmltv_manifest_lines = get_previous_manifest_for_crawler(
                    crawler_used)
                print('pulled previous manifest from ', get_cumulative_manifest_prefix(crawler_used) )

                not_in_previous_hashes = set()

                # sorting through the version hashes and checking for new files
                for name in file_names:
                    if name.endswith('.metadata'):
                        with zf.open(name) as metadata:
                            # we need to correct the metadata for utf-8 first, then read everything else
                            data = metadata.read()
                            corrected_metadata = codecs.decode(
                                data, 'utf-8-sig')
                        metadata.close()

                        # print for error checking (to be removed)
                        # print("raw data: " + data.decode() + "\n")
                        # print("cleaned metadata: " +
                        #       str(corrected_metadata) + "\n")

                        # clean just in case for newlines
                        corrected_metadata = corrected_metadata.replace(
                            "\n", "")
                        # now read the metadata line as a json and get its version hash
                        try:
                            jsondoc = json.loads(corrected_metadata)
                            version_hash = jsondoc.get('version_hash', None)
                        except:
                            print("WARNING: metadata file errored on load. Skipping")
                            continue
                        # only getting docs that aren't in previous hashes
                        if version_hash and not version_hash in previous_hashes:
                            not_in_previous_hashes.add(name)
                            corrected_manifest_jdocs.append(jsondoc)

                            # upload all of the files not in previous version hashes to s3
                            zip_filename = name.replace(
                                '.metadata', '')  # name of the main file
                            
                            print('zip_filename: ', zip_filename)
                            print('file_names: ', file_names)

                            # if base_dir in file_names:
                            for file_name in file_names:
                                zip_filename = f'{base_dir}{file_name}' if not file_name.startswith(base_dir) else file_name
                                stripped_name = file_name[len(base_dir):].lstrip('/') if name.startswith(base_dir) else name
                                # upload the main file
                                upload_file_from_zip(
                                    zf_ref=zf, zip_filename=zip_filename, prefix=destination_prefix_dt, base_dir=base_dir)
                                print('uploaded ', stripped_name, " to ", destination_prefix_dt)
                                
                            print('move complete for ', constZip_filename, '.zip to ', destination_prefix_dt)


                # upload the manifest file after getting all correctd metadata jdocs
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
            notify_with_tb(msg, traceback)

            try:
                undo_uploads(prefix=destination_prefix_dt)
            except:
                msg = '[ERROR] Failed undo_uploads'
                notify_with_tb(msg, traceback)

            continue

        # if no errors, go ahead and delete the zip so it won't be picked up again
        s3_obj.delete()
  
def base_dir_heuristic(zip_names: list):
    if not zip_names:
        return ''
    
    # Initialize base_dir with the directory of the first file
    base_dir = '/'.join(zip_names[0].split('/')[:-1]) + '/' if '/' in zip_names[0] else ''
    
    # Check if all files start with the same base dir
    for name in zip_names:
        current_dir = '/'.join(name.split('/')[:-1]) + '/' if '/' in name else ''
        if current_dir != base_dir:
            base_dir = ''
            break
    return base_dir


def undo_uploads(prefix):
    s3.Bucket(destination_bucket).objects.filter(Prefix=prefix).delete()

# Creates directory if not present
# Targets crawler's specific cumulative-manifest, not overall cumu-manif
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
        notify_with_tb(msg, traceback)
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


def create_byte_obj(s3_obj):
    body_bytes = s3_obj.get()['Body'].read()
    bytes_obj = BytesIO(body_bytes)
    return bytes_obj

def upload_file_from_zip(zf_ref, zip_filename, prefix, bucket=destination_bucket, base_dir=''):
    with zf_ref.open(zip_filename, "r") as f:
        # Remove the base_dir from zip_filename
        if base_dir and zip_filename.startswith(base_dir):
            filename = zip_filename[len(base_dir):].lstrip('/')
        else:
            filename = zip_filename
        s3_client.upload_fileobj(f, bucket, f"{prefix}/{filename}")
        
def delete_empty_base_dir(bucket, base_dir_prefix):
    # Check if base_dir is empty
    base_dir_contents = list(s3_client.list_objects_v2(Bucket=bucket, Prefix=base_dir_prefix)['Contents'])
    if len(base_dir_contents) == 1 and base_dir_contents[0]['Key'].endswith('/'):
        s3_client.delete_object(Bucket=bucket, Key=base_dir_contents[0]['Key'])
        print('\ndeleted ', base_dir_prefix)
    else:
        print('\n', base_dir_prefix, ' was not empty, did not delete')


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
    new_file.close()  # extra close just to be safe


if __name__ == '__main__':
    filter_and_move()
