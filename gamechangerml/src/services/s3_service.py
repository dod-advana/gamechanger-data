from boto3 import Session
from os.path import join


class S3Service:
    """This class is responsible for providing connection to S3, including 
    uploading and downloading files.
    """

    @staticmethod
    def connect_to_bucket(bucket_name, logger):
        """Connect to S3 bucket.

        Returns:
            boto3.resources.factory.s3.Bucket or None: The Bucket if 
                connection was successful. Otherwise, None.
        """
        try:
            session = Session()
            s3 = session.resource("s3")
            bucket = s3.Bucket(bucket_name)
        except Exception as e:
            logger.exception("Failed to connect to S3 bucket.")
            bucket = None
            raise e

        return bucket

    @staticmethod
    def upload_file(bucket, filepath, s3_fullpath, logger):
        """Upload a file to the S3 bucket.
        
        Args:
            bucket (boto3.resources.factory.s3.Bucket): Bucket to upload to. 
                See S3Service.connect_to_bucket().
            filepath (str): Path to the file to upload.
            s3_fullpath (str): Path to save to in S3.
            logger (logging.Logger)

        Returns:
            None
    """
        try:
            bucket.upload_file(filepath, s3_fullpath)
        except Exception as e:
            logger.exception(
                f"Failed to upload file at {filepath} to S3 {s3_fullpath}."
            )
            raise e

    @staticmethod
    def download(bucket, prefix, output_dir, logger):
        """Download file(s) from S3.

        Args:
            bucket (boto3.resources.factory.s3.Bucket): Bucket to download from. 
                See S3Service.connect_to_bucket().
            prefix (str): Prefix for file(s) to download.
            output_dir (str): Path to local directory to download file(s) to.
            logger (logging.Logger)

        Raises:
            Exception: If download fails.

        Returns:
            list of str: Local paths of downloaded files.
        """
        files = []
        try:
            for obj in bucket.objects.filter(Prefix=prefix):
                if obj.size != 0:
                    logger.info(f"Downloading {obj.key}.")
                    output_path = join(output_dir, obj.key.split("/")[-1])
                    bucket.download_file(obj.key, output_path)
                    files.append(output_path)
                else:
                    logger.debug(
                        f"S3 object size is 0. Skipping download. {obj.key}."
                    )
        except Exception as e:
            logger.exception(f"S3 download failed for {prefix}.")
            raise e
        
        return files

    @staticmethod
    def get_object_names(bucket, prefix, name_type="path"):
        """Get object names for the given S3 prefix.

        Args:
            prefix (str): Get object names with this prefix.
            bucket (boto3.resources.factory.s3.Bucket): Bucket to get objects 
                from. See S3Service.connect_to_bucket().
            name_type (str, optional): The following options are supported:
                "path": to get paths (paths do not include the prefix)
                "filename": to get file names
                "dir": to get parent directory names (i.e., part before the first 
                    "/" in the object path, not including the prefix)
                Default is "path".
        
        Raises:
            ValueError: If invalid name_type is given.

        Returns:
            list of str
        """
        name_types = ["path", "filename", "dir"]
        if name_type not in name_types:
            raise ValueError(
                f"Invalid name_type argument. Supported options are: {name_types}."
            )
            
        start_char = len(prefix)
        names = [obj.key[start_char:] for obj in bucket.objects.filter(Prefix=prefix)]
        
        if name_type == "filename":    
            names = [name.split("/")[-1] for name in names]
        elif name_type == "dir":
            names = list(set([
                name.split("/")[0] for name in names
            ]))

        return names
