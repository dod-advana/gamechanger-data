#!/usr/bin/env bash

helpFunction()
{
   echo ""
   echo "Usage: $0 -v versionNumber"
   echo -e "\t-v version number to upload to the s3 bucket"

   echo ""
   echo "Usage: $0 -p path"
   echo -e "\t-p path to model folder"
   return 0
  #  exit 0 # Exit script after printing help
}
function download_transformers() {
  # Print helpFunction in case parameters are empty
  local S3_TRANS_MODEL_PATH="s3://advana-data-zone/bronze/gamechanger/models/transformers/v${version}/transformers.tar.gz"

  echo "Creating transformers folder"
  git lfs install
  rm -rf "$models_dest_dir/transformers/"
  mkdir "$models_dest_dir/transformers/"
  echo "Cloning transformers folder"

  git clone https://huggingface.co/deepset/bert-base-cased-squad2 "${models_dest_dir}/transformers/bert-base-cased-squad2"
  git clone https://huggingface.co/valhalla/distilbart-mnli-12-3 "${models_dest_dir}/transformers/distilbart-mnli-12-3"
  git clone https://huggingface.co/distilbert-base-uncased-distilled-squad "${models_dest_dir}/transformers/distilbert-base-uncased-distilled-squad"
  git clone https://huggingface.co/distilroberta-base "${models_dest_dir}/transformers/distilroberta-base"
  git clone https://huggingface.co/sentence-transformers/msmarco-distilbert-base-v2 "${models_dest_dir}/transformers/msmarco-distilbert-base-v2"
  echo "Tar files"

  tar -zcvf "${models_dest_dir}/transformers.tar.gz" "${models_dest_dir}/transformers/"
  echo "uploading to s3 $S3_TRANS_MODEL_PATH"
  aws s3 cp "$models_dest_dir/transformers.tar.gz" $S3_TRANS_MODEL_PATH
}

while getopts v:p: flag
do
  case "${flag}" in
      v) version=${OPTARG};;
      p) models_dest_dir=${OPTARG};;
  esac
done

if [ -z "$version" ]
then
  echo "Version number for s3 must be provided to have the script work";
  helpFunction
  return 0
fi
if [ -z "$models_dest_dir" ]
then
  echo "Model path must be provided to have the script work";
  helpFunction
  return 0
fi

download_transformers
