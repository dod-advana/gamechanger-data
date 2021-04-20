from dataScience.src.utilities.utils import *
from dataScience.src.utilities.aws_helper import *
import os
import sys

os.chdir(
    os.getcwd()[: os.getcwd().find("gamechanger") + 11]
    + "/dataScience/models/topic_models/models/"
)
s3_models_dir = "models/topic_models/"

try:
    sys.argv[1]
except:
    raise Exception(
        '\nArgument not specified. Specify "load" or "save" as an argument into the shell script.'
    )

# if we're loading models from s3
if sys.argv[1].lower() == "load":
    print("\nLoading models from s3 \n")

    # download everything from s3
    print(get_models_list(s3_models_dir))
    for s in get_models_list(s3_models_dir):
        get_model_s3(s[0], s3_models_dir)
    print("\nFinished")

# if we're saving models into s3
elif sys.argv[1].lower() == "save":
    print("\nSaving models into s3\n")

    # check if the directory is empty
    print(f"List of files being uploaded: {os.listdir()}")
    if not os.listdir():
        raise Exception(
            "\nModels directory is empty. Load models into the directory before saving to s3."
        )

    # upload everything in the directory to s3
    for s in os.listdir():
        print(f"Uploading {s} ...")
        upload_file(s, s3_models_dir + s)
    print(allso)
    print("\nFinished")
else:
    raise Exception(
        'Specify "load" or "save" as an argument into the shell script.')
