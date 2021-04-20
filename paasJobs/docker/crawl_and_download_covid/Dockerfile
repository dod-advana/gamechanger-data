FROM advana/gc-crawler:latest

#####
## ## App Setup
#####

## tmpdir/dldir settings
# where temporary files stored by tools like mktemp
ENV TMPDIR="/var/tmp"

# where the output of the container run is stored
ENV DLDIR="$TMPDIR/dl"

# setup workdir
ENV APP_REPO_DIR="/app"
RUN mkdir -p "${APP_REPO_DIR}"

# make sure PATH makes sense
ENV PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Default WORKDIR is app setup dir
WORKDIR "${APP_REPO_DIR}"

# copy code
COPY . "${APP_REPO_DIR}"
ENV PYTHONPATH="${APP_REPO_DIR}"

ENTRYPOINT ["/bin/bash", "/app/paasJobs/docker/crawl_and_download_covid/run_job.sh"]