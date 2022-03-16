import click
import functools


def pass_bucket_name_option(f):
    @click.option(
        '--bucket-name',
        type=str,
        required=True,
        help="S3 bucket name"
    )
    @functools.wraps(f)
    def wf(*args, **kwargs):
        return f(*args, **kwargs)
    return wf