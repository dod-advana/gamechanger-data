ARG BASE_IMAGE=registry.redhat.io/rhel8/postgresql-13:1-138
FROM --platform=x86_64 $BASE_IMAGE

ARG \
    GHOSTSCRIPT_VERSION=9.55.0 \
    JBIG2ENC_VERSION=0.29 \
    LEPTONICA_VERSION=1.82.0 \
    TESSERACT_OCR_VERSION=4.1.1 \
    TESSERACT_OCR_LANGPACK_VERSION=4.1.0 \
    QPDF_VERSION=8.2.1

# BRIEFLY ROOT
USER root

# PYTHON & LOCALE ENV VARS
ENV LANG="C.utf8" \
    LANGUAGE="C.utf8" \
    LC_ALL="C.utf8" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING="UTF-8" \
    PKG_CONFIG_PATH=/usr/local/lib/pkgconfig \
    PKG_CONFIG=/usr/bin/pkg-config \
    TESSDATA_PREFIX=/usr/local/share/tessdata/

# Additional Repos
RUN rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-8 \
  &&  dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm


# COMMON Packages & More Particular RPM Dependcies
RUN dnf install -y glibc-locale-source.x86_64 \
  &&  dnf install -y zip \
        unzip \
        gzip \
        zlib \
        zlib-devel \
        git \
        git-lfs \
        make \
        automake \
        autoconf \
        libtool \
        gcc \
        gcc-c++ \
        gcc-gfortran \
        libpng \
        libpng-devel \
        libtiff \
        libtiff-devel \
        libjpeg-turbo \
        libjpeg-turbo-devel \
        python38 \
        python38-devel \
        python38-Cython \
        libpq-devel \
        openblas \
        openblas-threads \
        diffutils \
        file \
      && dnf clean all

RUN \
    curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && echo "[INFO] Installing AWS CLI ..." && ( \
      unzip -q /tmp/awscliv2.zip -d /opt \
      &&  /opt/aws/install \
      &&  rm -f  /tmp/awscliv2.zip \
  ) 2>&1 1>/dev/null

# OCRMYPDF REQS: https://ocrmypdf.readthedocs.io/en/v12.7.0/installation.html
# ocrmypdf <- (compiled) tesseract 4.0+
#          <- (compiled) jbig2enc 0.29+ <- (compiled) leptonica
#          <- (skipped) unpaper 6.1+ (to support --clean flag...)
#          <- (rpm) pngquant 2.5+
#          <- (compiled) ghostscript 9.23+
#          <- (compiled) qpdf 8.2.1

RUN git clone --depth 1 --branch "release-qpdf-${QPDF_VERSION}" https://github.com/qpdf/qpdf.git /opt/qpdf \
  && echo "[INFO] Installing from source: QPDF ..." && ( \
    cd /opt/qpdf \
    && ./autogen.sh \
    && ./configure \
    && make -j \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# leptonica - tesseract/jbig2enc dep
RUN git clone --depth 1 --branch "${LEPTONICA_VERSION}" https://github.com/danbloomberg/leptonica.git /opt/leptonica \
  && echo "[INFO] Installing from source: LEPTONICA ..." && ( \
    cd /opt/leptonica \
    && ./autogen.sh \
    && ./configure \
    && make -j \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# jbig2enc - optional ocrmypf/tesseract dep
RUN  git clone --depth 1 --branch "${JBIG2ENC_VERSION}" https://github.com/agl/jbig2enc.git /opt/jbig2enc \
  &&  echo "[INFO] Installing from source: JBIG2ENC ..." && ( \
        cd /opt/jbig2enc \
        && ./autogen.sh \
        && ./configure \
        && make -j \
        && make install \
        && ldconfig \
      ) 2>&1 1>/dev/null

# tesseract - ocrmypdf dep
RUN \
      git clone --depth 1 --branch "${TESSERACT_OCR_VERSION}" https://github.com/tesseract-ocr/tesseract.git /opt/tesseract \
  &&  echo "[INFO] Installing from source: TESSERACT-OCR ..." && ( \
        cd /opt/tesseract \
        && ./autogen.sh \
        && ./configure \
        && make -j \
        && make install \
        && ldconfig \
      ) 2>&1 1>/dev/null

# tesseract language packs - ocrmypdf dep
RUN \
      echo "[INFO] Installing language packs for TESSERACT-OCR ..." && ( \
      mkdir -p "${TESSDATA_PREFIX}" \
      && curl -L -o "${TESSDATA_PREFIX}/eng.traineddata" \
        "https://github.com/tesseract-ocr/tessdata_fast/raw/${TESSERACT_OCR_LANGPACK_VERSION}/eng.traineddata" \
      && curl -L -o "${TESSDATA_PREFIX}/spa.traineddata" \
        "https://github.com/tesseract-ocr/tessdata_fast/raw/${TESSERACT_OCR_LANGPACK_VERSION}/spa.traineddata" \
)

# ghostscript - ocrmypdf dep
RUN \
      curl -L \
      "https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs9550/ghostscript-${GHOSTSCRIPT_VERSION}.tar.gz" \
        | tar -xz -C /opt \
      && echo "[INFO] Installing from source: GHOSTSCRIPT ..." && ( \
        cd "/opt/ghostscript-${GHOSTSCRIPT_VERSION}" \
        && ./autogen.sh \
        && ./configure \
        && make -j \
        && make install \
        && ldconfig \
      ) 2>&1 1>/dev/null

#####
## ## APP SETUP
#####

# non-root app USER/GROUP
ARG \
  APP_UID=1000 \
  APP_GID=1000

# ensure user/group exists, formally
RUN ( (getent group $APP_GID &> /dev/null) \
        || groupadd --system --gid $APP_GID app_default \
    ) && ( (getent passwd $APP_UID &> /dev/null) \
        || useradd --system --shell /sbin/nologin --gid $APP_GID --uid $APP_UID app_default \
    )

# ensure key app directories
ENV APP_ROOT="/opt/app-root"
ENV APP_VENV="${APP_ROOT}"
ENV APP_VENV_CFG="${APP_VENV}/etc"
ENV APP_SRC="${APP_ROOT}/src"

RUN \
  mkdir -p \
    "${APP_ROOT}" \
    "${APP_VENV}" \
    "${APP_VENV_CFG}" \
    "${APP_SRC}" \
  && chown -R "${APP_UID}:${APP_GID}" \
    "${APP_ROOT}" \
    "${APP_VENV}" \
    "${APP_VENV_CFG}" \
    "${APP_SRC}"


#RUN ln -s /usr/pgsql-13/bin/pg_config /usr/sbin/pg_config
#RUN export PATH=/usr/pgsql-13/bin/:$PATH
#RUN export LD_LIBRARY_PATH=/usr/pgsql-13/lib
RUN dnf install -y libpq-devel

# setup venv
COPY ./dev_tools/requirements/rhel8.locked.requirements.txt /tmp/requirements.txt
COPY ./dev_tools/combined_entities.csv ${APP_VENV}/lib/python3.8/site-packages/gamechangerml/data/combined_entities.csv 

RUN \
      python3 -m venv "${APP_VENV}" --prompt app-root \
  &&  "${APP_VENV}/bin/python" -m pip install --upgrade --no-cache-dir pip setuptools wheel \
  &&  "${APP_VENV}/bin/python" -m pip install --no-cache-dir -r /tmp/requirements.txt \
  &&  chown -R "${APP_UID}:${APP_GID}" "${APP_VENV}"

# Entrypoint
COPY ./dev_tools/docker/k8s/entrypoint.sh /usr/bin/entrypoint
RUN chmod a+rx "/usr/bin/entrypoint"

# thou shall not root
USER $APP_UID:$APP_GID

COPY --chown="${APP_UID}:${APP_GID}" ./ "${APP_SRC}/" 
WORKDIR "${APP_SRC}"

ENV \
    BASH_ENV="/usr/bin/entrypoint" \
    ENV="/usr/bin/entrypoint" \
    PROMPT_COMMAND=". /usr/bin/entrypoint" \
    LD_LIBRARY_PATH="/usr/local/lib/"

ENTRYPOINT [ "/usr/bin/entrypoint" ]
