def get_latest_model_name(s3_models_dir, bucket):
    """Get the name of the most recently uploaded model in S3.

    Args:
        s3_models_dir (str): Directory where models are stored in S3.
        bucket (boto3.resources.factory.s3.Bucket): Bucket to get latest model 
            name from. 

    Returns:
        str or None: If None, means no models found. If str, name of the latest 
            model.
    """
    models = [
        (obj.key, obj.last_modified) 
        for obj in bucket.objects.filter(Prefix=s3_models_dir)
    ]
    if not models:
        return None
    latest_model_name = max(models, key=lambda x: x[1])[0]
    latest_model_name = latest_model_name[len(s3_models_dir):].split("/")[0]

    return latest_model_name
