#!/bin/bash
echo "Creating transformers folder"
git lfs install
TransformerList=("https://huggingface.co/sentence-transformers/msmarco-distilbert-base-v2
https://huggingface.co/valhalla/distilbart-mnli-12-3")

for Path in "${TransformerList[@]}"
do
    echo "$Path"
    git clone "$Path"
  done


