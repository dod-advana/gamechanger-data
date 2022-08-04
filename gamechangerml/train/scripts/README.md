# Scripts CLI
gamechangerml/train/scripts/cli.py 

## Train Topics Model
`python -m gamechangerml.train.scripts create-topics [-c, -u, -s]` \
`-c, --corpus-location  <str>: default = gamechangerml/corpus` \
`-u, --upload  <Flag>: default = off` \
`-s, --sample-rate  <float>(0.0, 1.0]: default = 1.0`

> Train a model from local files with a sample rate of 60% and upload the resulting model

`python -m gamechangerml.train.scripts create-topics -c ~/Desktop/gamechanger-ml/gamechangerml/corpus  -s 0.6  --upload` 
