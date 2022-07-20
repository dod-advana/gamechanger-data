 #!/bin/bash
echo "Be sure to set up environment variables for s3 by sourcing setup_env.sh if running this manually"
echo "Downloading Corpus Folder"
echo "S3 MODEL PATH CORPUS: $S3_CORPUS_PATH"
 
 aws s3 sync $S3_CORPUS_PATH $PWD/gamechangerml/corpus_dir/gc_corpus/.