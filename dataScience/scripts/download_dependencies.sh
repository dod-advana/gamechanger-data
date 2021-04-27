#!/bin/bash
echo "Be sure to set up environment variables for s3 by sourcing setup_env.sh if running this manually"
echo "Downloading Transformers Folder"
echo "S3 MODEL PATH TRANSFORMERS: $S3_TRANS_MODEL_PATH"
#python -c "from dataScience.src.utilities.utils import get_transformer_cache; get_transformer_cache(model_path='$S3_TRANS_MODEL_PATH', overwrite=False)"
aws s3 cp "$S3_TRANS_MODEL_PATH" $PWD/dataScience/models/.

echo "Downloading Sentence Index"
echo "S3 MODEL PATH SENTENCE INDEX: $S3_SENT_INDEX_PATH"
aws s3 cp "$S3_SENT_INDEX_PATH" $PWD/dataScience/models/.
#python -c "from dataScience.src.utilities.utils import get_sentence_index; get_sentence_index(model_path='$S3_SENT_INDEX_PATH',overwrite=False)"

echo "Downloading QE Model"
echo "S3 QE MODEL: $S3_QEXP_PATH"
aws s3 cp "$S3_QEXP_PATH" $PWD/dataScience/models/.
