############# Steps for Ingest ###############################################
# Example run: ./tmp/scripts/steps.sh -j test-dod-spider -c dod_strategy_spider
# gc_aws_login
# cd dev_tools
# docker-compose up

err(){
    printf "[ERROR] $*" >>/dev/stderr
}

inflog(){
    printf "[INFO] $*\n"
}

list_spiders() {
    search_dir=/home/melkiga/code/gamechanger-crawlers/dataPipelines/gc_scrapy/gc_scrapy/spiders/
    title="Crawler Names:"
    names=$(find $search_dir -type f -name *spider.py -printf '%h\0%d\0\t\t\t\t\t%P\n' | sed "s/.*\///; s/\.py//" | sort -t '\0' -n | awk -F'\0' '{print $3}');
    printf "\t$title $names\n"
}


usage() { 
    space="                           "
    printf "\nUsage:\t$0\n" 
    arg1="[-j <job-name>]"
    arg2="[-c <run-crawler>]"
    arg3="[-u <update-neo4j>]"
    printf "\t%s %s %s (Required) Name of job output folder\n" $arg1 "${space:${#arg1}}" 
    printf "\t%s %s %s (Optional) Crawler name\n" $arg2 "${space:${#arg2}}" 
    printf "\t%s %s %s (Optional, default=False) Update Neo4j\n" $arg3 "${space:${#arg3}}" 
    list_spiders
    exit 1;
}


if (($# == 0))
then
    USAGE
fi

while getopts ":j:c:u:h" opt
do
    case $opt in
        j) JOB_NAME=${OPTARG};;
        c) CRAWLER=${OPTARG};;
        u) NEO4J=${OPTARG};;
        h) usage;;
        \?) err "Invalid option: -$OPTARG exiting."; usage;
        exit;;
        :) echo "Option -$OPTARG requires an argument" >&2
        exit;;
    esac
done

inflog "Arguments:\n\t- Job Name: $JOB_NAME\n\t- Crawler: $CRAWLER\n\t- Update Neo4j: $NEO4J";

############# Environment Setup ###############################################
## 1. environment variable setup
readonly SCRIPT_ENV="${SCRIPT_ENV:-local}"
readonly APP_CONFIG_NAME="${APP_CONFIG_NAME:-$SCRIPT_ENV}"
readonly ES_CONFIG_NAME="${ES_CONFIG_NAME:-$SCRIPT_ENV}"

# Data repo setup vars
readonly DATA_REPO_DIR="/home/melkiga/code/gamechanger-data"
readonly APP_CONFIG_LOCAL_PATH="${DATA_REPO_DIR}/configuration/app-config/${APP_CONFIG_NAME}.json"

# Crawler repo setup vars
readonly CRAWL_REPO_DIR="/home/melkiga/code/gamechanger-crawlers"
readonly SPIDER_PATH="${CRAWL_REPO_DIR}/dataPipelines/gc_scrapy/gc_scrapy/spiders"

# ML repo setup vars
readonly ML_REPO_DIR="/home/melkiga/code/gamechanger-ml"
readonly TOPIC_MODEL_LOCAL_DIR="${ML_REPO_DIR}/gamechangerml/models/topic_models/models/"

# Script setup vars
readonly WORKING_DIR="${DATA_REPO_DIR}/tmp/test-runs"
readonly JOB_DIR="${WORKING_DIR}/$JOB_NAME"
readonly CRAWLER_OUTPUT_DIR="${JOB_DIR}/crawler-output"
readonly PARSED_OUTPUT_DIR="${JOB_DIR}/parsed_docs"
readonly BD_BACKUP_DIR="${JOB_DIR}/db_backups"
readonly THUMBNAIL_DIR="${JOB_DIR}/thumbnails"

# AWS setup vars
readonly AWS_CMD="${AWS_CMD:-aws}"
readonly S3_BUCKET_NAME="${S3_BUCKET_NAME:-advana-data-zone}"

# Python setup vars
readonly DATA_PYTHON_CMD="${PYTHON_CMD:-$DATA_REPO_DIR/.venv/bin/python}"
readonly CRAWLER_PYTHON_CMD="${PYTHON_CMD:-$CRAWL_REPO_DIR/.venv/bin/python}"

inflog "\t Gamechanger Data Repo: ${DATA_REPO_DIR}"
inflog "\t Gamechanger Crawlers Repo: ${CRAWL_REPO_DIR}"
inflog "\t Gamechanger ML Repo: ${ML_REPO_DIR}"
inflog "\t Job's Directory: ${JOB_DIR}"
inflog "\t Script env config name: ${SCRIPT_ENV}"
inflog "\t Local app config: ${APP_CONFIG_LOCAL_PATH}"
inflog "\t S3 bucket name: ${S3_BUCKET_NAME}"
inflog "\t Topic model dir: ${TOPIC_MODEL_LOCAL_DIR}"
inflog "\t Spiders dir: ${SPIDER_PATH}"

## 2. setup folders
inflog "Setting up output directories"

# if crawler specified, set the DO_CRAWL variable
if [[ $CRAWLER ]]; then readonly DO_CRAWL=$CRAWLER; fi
if [[ $NEO4J ]]; then readonly UPDATE_NEO4J=$NEO4J; fi
echo $UPDATE_NEO4J
# if we want to crawl
if [[ $DO_CRAWL ]]; then
    inflog "\t Crawler specified, creating crawler output directory ${CRAWLER_OUTPUT_DIR}"
    rm -rf $JOB_DIR
    mkdir --parents $CRAWLER_OUTPUT_DIR
    if [[ $UPDATE_NEO4J != "yes" ]]; then
        mkdir --parents $PARSED_OUTPUT_DIR
    fi
else 
    inflog "\t No crawler specified, keeping previous crawler output"
    inflog "\t Deleting parsed outputs from ${PARSED_OUTPUT_DIR}"
    if [[ ! -d $CRAWLER_OUTPUT_DIR ]]; then err "No crawler output found at ${CRAWLER_OUTPUT_DIR}. Exiting."; usage; fi
    rm -rf $PARSED_OUTPUT_DIR
    if [[ $UPDATE_NEO4J != "yes" ]]; then
        mkdir $PARSED_OUTPUT_DIR
    fi
    rm -rf $THUMBNAIL_DIR
    rm -rf $BD_BACKUP_DIR
fi

############# Configure Data Repo ###############################################

function configure_repo() {
    inflog "\t Initializing default config files"
    inflog "poetry run $DATA_PYTHON_CMD -m configuration init $SCRIPT_ENV --app-config $APP_CONFIG_NAME --elasticsearch-config $ES_CONFIG_NAME"
    poetry run $DATA_PYTHON_CMD -m configuration init "$SCRIPT_ENV" \
  	--app-config "$APP_CONFIG_NAME" \
  	--elasticsearch-config "$ES_CONFIG_NAME"
}

configure_repo

function post_checks() {
  inflog "\t Running post-deploy checks..."
  inflog "\t Checking connections..."
  poetry run $DATA_PYTHON_CMD -m configuration check-connections
}

post_checks

############# Run ###############################################

## 1. run crawler
if [[ $DO_CRAWL ]]; then
    inflog "Running crawler ${CRAWLER}"
    inflog "\t Creating prev manifest file: $CRAWLER_OUTPUT_DIR/prev_manifest.json"
    touch $CRAWLER_OUTPUT_DIR/prev_manifest.json
    cd $CRAWL_REPO_DIR
    inflog "\t Running crawler"
    poetry run $CRAWLER_PYTHON_CMD -m scrapy runspider $SPIDER_PATH/$CRAWLER.py \
    -a download_output_dir=$CRAWLER_OUTPUT_DIR \
    -a previous_manifest_location=$CRAWLER_OUTPUT_DIR/prev_manifest.json \
    -o $CRAWLER_OUTPUT_DIR/output.json
    inflog "\t Output file writting to $CRAWLER_OUTPUT_DIR/output.json"
    cd $DATA_REPO_DIR
fi

## 2. run parser
# inflog "Running parser"
# poetry run $DATA_PYTHON_CMD -m common.document_parser pdf-to-json -w -s $CRAWLER_OUTPUT_DIR -d $PARSED_OUTPUT_DIR
# python -m common.document_parser pdf-to-json -w -s tmp/test-runs/dod-policy/crawler-output -d tmp/test-runs/dod-policy/parsed_docs
## 3. core ingest
readonly SNAPSHOT_PREIX="gamechanger/test-output-steps"
readonly JOB_TS="$(date +%FT%T)"
if [[ $UPDATE_NEO4J != "yes" ]]; then
    poetry run $DATA_PYTHON_CMD -m dataPipelines.gc_ingest pipelines core ingest \
        --skip-neo4j-update=no \
        --skip-snapshot-backup=no \
        --skip-db-backup=no \
        --skip-db-update=no \
        --current-snapshot-prefix="${SNAPSHOT_PREIX}/" \
        --backup-snapshot-prefix="${SNAPSHOT_PREIX}/backup/" \
        --db-backup-base-prefix="${SNAPSHOT_PREIX}/backup/db/" \
        --load-archive-base-prefix="${SNAPSHOT_PREIX}/load-archive/" \
        --bucket-name=$S3_BUCKET_NAME \
        --job-dir=$JOB_DIR \
        --batch-timestamp=$JOB_TS \
        --index-name=gamechanger_20210409 \
        --alias-name="alias-test-0" \
        --max-threads=16 \
        --max-ocr-threads=4 \
        --max-s3-threads=1 \
        --skip-revocation-update=no \
        --skip-es-revocation=no \
        --crawler-output=$CRAWLER_OUTPUT_DIR/output.json \
        local \
        --local-raw-ingest-dir=$CRAWLER_OUTPUT_DIR \
        #--local-parsed-ingest-dir=$PARSED_OUTPUT_DIR
    fi


## 3. update neo4j
if [[ $UPDATE_NEO4J ]]; then
    poetry run $DATA_PYTHON_CMD -m dataPipelines.gc_ingest pipelines core ingest \
        --skip-neo4j-update=no \
        --skip-snapshot-backup=yes \
        --skip-db-backup=no \
        --skip-db-update=no \
        --current-snapshot-prefix="${SNAPSHOT_PREIX}/" \
        --backup-snapshot-prefix="${SNAPSHOT_PREIX}/backup/" \
        --db-backup-base-prefix="${SNAPSHOT_PREIX}/backup/db/" \
        --load-archive-base-prefix="${SNAPSHOT_PREIX}/load-archive/" \
        --bucket-name=$S3_BUCKET_NAME \
        --job-dir=$JOB_DIR \
        --batch-timestamp=$JOB_TS \
        --index-name=gamechanger_20210409 \
        --alias-name=\'\' \
        --max-threads=16 \
        --max-ocr-threads=4 \
        --max-s3-threads=1 \
        --skip-revocation-update=no \
        --skip-es-revocation=no \
        update-neo4j
    fi

# python -m dataPipelines.gc_ingest pipelines core ingest \
#     --skip-neo4j-update=no \
#     --skip-snapshot-backup=yes \
#     --skip-db-backup=no \
#     --skip-db-update=no \
#     --current-snapshot-prefix="gamechanger/test-output-steps/" \
#     --backup-snapshot-prefix="gamechanger/test-output-steps/backup" \
#     --db-backup-base-prefix="gamechanger/test-output-steps/backup/db/" \
#     --load-archive-base-prefix="gamechanger/test-output-steps/load-archive" \
#     --bucket-name="advana-data-zone" \
#     --job-dir="tmp/test-runs/dod-ingest" \
#     --batch-timestamp="2022-06-21T01:19:31" \
#     --index-name="gamechanger_20210409" \
#     --alias-name=\'\' \
#     --max-threads=16 \
#     --max-ocr-threads=4 \
#     --max-s3-threads=1 \
#     --skip-revocation-update=no \
#     --skip-es-revocation=yes \
#     update-neo4j