ARG BASE_IMAGE='gamechanger/core/base-env:latest'
FROM $BASE_IMAGE

## shell for RUN cmd purposes
SHELL ["/bin/bash", "-c"]
USER root
ARG TMP_BASE_DIR="/tmp/staging"

#####
## ## StreamSets Setup
#####

RUN mkdir -p "${TMP_BASE_DIR}"
ARG STREAMSETS_TGZ_URL='https://archives.streamsets.com/datacollector/3.6.2/tarball/streamsets-datacollector-all-3.6.2.tgz'
ARG STREAMSETS_TGZ_PATH="${TMP_BASE_DIR}/streamsets.tgz"
ARG STREAMSETS_UNPACKED_BASE_DIR="/opt/streamsets-datacollector-3.6.2"

# pull down the goods & extract at the home location
RUN curl -kL -o "$STREAMSETS_TGZ_PATH" "$STREAMSETS_TGZ_URL" \
    && tar -xzf "$STREAMSETS_TGZ_PATH" -C "/opt" \
    && test -d "$STREAMSETS_UNPACKED_BASE_DIR" \
    && rm -f "$STREAMSETS_TGZ_PATH"

# setup sdc user/group
RUN useradd sdc && echo password | passwd --stdin sdc
# non-login user, not as useful for debugging
# RUN groupadd -r sdc && useradd -r -d "$STREAMSETS_UNPACKED_BASE_DIR" -g sdc -s /sbin/nologin sdc

# some important streamsets env vars
ENV SDC_CONF=/etc/sdc
ENV SDC_HOME="$STREAMSETS_UNPACKED_BASE_DIR"
ENV SDC_LOG=/var/log/sdc
ENV SDC_DATA=/var/lib/sdc
ENV SDC_RESOURCES=/var/lib/sdc-resources

# create relevant directories
RUN mkdir -p "$SDC_LOG" \
    && mkdir -p "$SDC_CONF" \
    && mkdir -p "$SDC_DATA" \
    && mkdir -p "$SDC_RESOURCES"

# populate misc streamsets dirs & set permissions
RUN cp -R "$STREAMSETS_UNPACKED_BASE_DIR"/etc/* "$SDC_CONF" \
    && chown -R sdc:sdc "$SDC_LOG" \
    && chown -R sdc:sdc "$SDC_CONF" \
    && chown -R sdc:sdc "$SDC_DATA" \
    && chown -R sdc:sdc "$SDC_RESOURCES" \
    && chown -R sdc:sdc "$SDC_HOME"

#####
## ## Misc Config  (placed later to avoid heavier layer rebuilds)
#####

# this doesn't matter since StreamSets tarball install includes ALL packages, but.. just in case, this fixes a cert bug
RUN sed -i 's/run curl/run curl --insecure /g'  "${SDC_HOME}/libexec/_stagelibs"

# run /bin/bash shell in executor stage by default
RUN echo 'stage.conf_com.streamsets.pipeline.stage.executor.shell.shell=/bin/bash' >> "${SDC_CONF}"/sdc.properties

# clean up
RUN rm -rf "$TMP_BASE_DIR"

#####
## ## SDC user config
#####

ENV SDC_USER_HOME='/home/sdc'
ENV DOCKER_ENTRYPOINT="/usr/local/bin/docker-entrypoint.sh"

COPY ./dev/docker/devtools/streamsets/docker-entrypoint.sh "$DOCKER_ENTRYPOINT"
RUN chmod a+x "$DOCKER_ENTRYPOINT"

# grant sudo to sdc user
RUN usermod -aG wheel sdc

# run these cmds and entrypoint after as sdc user
USER sdc

RUN echo insecure > "$SDC_USER_HOME/.curlrc"

#####
## ## START CONFIG
#####

EXPOSE 18630/tcp

ENTRYPOINT $DOCKER_ENTRYPOINT