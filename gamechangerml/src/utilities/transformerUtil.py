from transformers import pipeline
import os
import json
from transformers import (
    AutoTokenizer,
    AutoModel,
    AutoModelForSequenceClassification,
)


def getTransformer(modelname: str):
    """getTransformer: downloads transformers from hugging face and downloads to transformer cache
    Args:
        model: str for model name, must match huggingface
    Returns:
    """
    if not os.path.exists("transformer_cache"):
        os.makedirs("transformer_cache")
    os.environ["TRANSFORMERS_CACHE"] = os.path.join(
        os.getcwd(), "transformer_cache/.cache/torch/transformers"
    )
    success = False
    try:
        tokenizer = AutoTokenizer.from_pretrained(modelname)
        model = AutoModel.from_pretrained(modelname)
        success = True
    except Exception as e:
        print("cannot use automodel to get transformer")
        print(e)
    if not success:
        try:
            tokenizer = AutoTokenizer.from_pretrained(modelname)
            model = AutoModelForSequenceClassification.from_pretrained(
                modelname
            )
            success = True
        except Exception as e:
            print("cannot use automodel to get transformer")
            print(e)
    if not success:
        # likely trying to use question answer
        try:
            unmasker = pipeline("question-answering", model=modelname)
        except Exception as e:
            print("could not use unmasker to get transformer")
            print(e)


def updateMeta(model: str):
    """updateMeta: updates the transformer meta info file
    Args:
        model: str model name
    Returns:

    """
    try:
        with open("transformer_cache/transformer_meta.json", "r") as f:
            data = json.load(f)
        if model not in data:
            data.append(model)
        with open("transformer_cache/transformer_meta.json", "w") as f:
            json.dump(data, f)
    except:
        print("Could not update meta file for transformers")
