readonly SCRIPT_PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly REPO_DIR="$(cd "$SCRIPT_PARENT_DIR/../../../" >/dev/null 2>&1 && pwd)"
source $REPO_DIR/gamechangerml/setup_env.sh $2
export PYTHONPATH=$PYTHONPATH:$REPO_DIR

# Main script to load/save current topic models from s3 and store them in gamechangerml/models/topic_models/models
# This sources from setup_env.sh to setup the proper environment, then calls the python script at the end depending
# on the supplied argument
#
# (NOTE: make sure you're in the gc environment before running this script,
# otherwise it'll say module gamechangerml not found)
#
#
# To load models from s3, execute:
# bash topic_model.sh load DEV
# or
# bash topic_model.sh load PROD
#
# To save models into s3 that are in the models directory, execute:
# bash topic_model.sh save DEV
# or
# bash topic_model.sh save PROD

python3 topic_model_loadsave.py $1
