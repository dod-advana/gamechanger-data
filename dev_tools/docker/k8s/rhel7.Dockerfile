ARG BASE_IMAGE='registry.access.redhat.com/ubi7/ubi:7.9-516'
FROM --platform=x86_64 $BASE_IMAGE

ARG \
    COMPILE_PYTHON_VERSION=36 \
    GHOSTSCRIPT_VERSION=9.55.0 \
    JBIG2ENC_VERSION=0.29 \
    LEPTONICA_VERSION=1.82.0 \
    TESSERACT_OCR_VERSION=4.1.1 \
    TESSERACT_OCR_LANGPACK_VERSION=4.1.0 \
    QPDF_VERSION=8.2.1

USER root

# PYTHON & LOCALE ENV VARS
ENV LANG="C.utf8" \
    LANGUAGE="C.utf8" \
    LC_ALL="C.utf8" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING="UTF-8" \
    PKG_CONFIG_PATH=/usr/local/lib/pkgconfig \
    PKG_CONFIG=/usr/bin/pkg-config \
    TESSDATA_PREFIX=/usr/local/share/tessdata/ \
    COMPILE_PYTHON_VERSION="${PYTHON_VERSION}"

# Additional Repos
RUN \
      rpm --import https://download.postgresql.org/pub/repos/yum/RPM-GPG-KEY-PGDG \
  &&  yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-7 \
  &&  yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

# COMMON Packages & More Particular RPM Dependcies
RUN \
    yum install -y \
        git \
        git-lfs \
        gcc \
        gcc-c++ \
        llvm11  \
    && yum install -y \
        "rh-python${COMPILE_PYTHON_VERSION}" \
        "rh-python${COMPILE_PYTHON_VERSION}-scldevel" \
        git \
        git-lfs \
        "postgresql13" \
        zip \
        unzip \
        gzip \
        zlib \
        zlib-devel \
        make \
        automake \
        autoconf \
        libtool \
        libpng \
        libpng-devel \
        libtiff \
        libjpeg-turbo \
        libjpeg-turbo-devel \
        ghostscript \
        diffutils \
    &&  yum install -y libpq5-devel-13.4-42PGDG.rhel7.x86_64 \
    &&  yum clean all \
    &&  rm -rf /var/cache/yum


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

RUN \
  git clone --depth 1 --branch "release-qpdf-${QPDF_VERSION}" https://github.com/qpdf/qpdf.git /opt/qpdf \
  && echo "[INFO] Installing from source: QPDF ..." && ( \
    cd /opt/qpdf \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# leptonica - tesseract/jbig2enc dep
RUN \
  git clone --depth 1 --branch "${LEPTONICA_VERSION}" https://github.com/danbloomberg/leptonica.git /opt/leptonica \
  && echo "[INFO] Installing from source: LEPTONICA ..." && ( \
    cd /opt/leptonica \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# jbig2enc - optional ocrmypf/tesseract dep
RUN \
  git clone --depth 1 --branch "${JBIG2ENC_VERSION}" https://github.com/agl/jbig2enc.git /opt/jbig2enc \
  && echo "[INFO] Installing from source: JBIG2ENC ..." && ( \
    cd /opt/jbig2enc \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# tesseract - ocrmypdf dep
RUN \
  git clone --depth 1 --branch "${TESSERACT_OCR_VERSION}" https://github.com/tesseract-ocr/tesseract.git /opt/tesseract \
  && echo "[INFO] Installing from source: TESSERACT-OCR ..." && ( \
    cd /opt/tesseract \
    && ./autogen.sh \
    && ./configure \
    && make \
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

#####
## ## APP SETUP
#####

# non-root app USER/GROUP
ARG \
  APP_UID=1001 \
  APP_GID=1001

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

# setup venv
COPY ./dev_tools/requirements/requirements.txt /tmp/requirements.txt
RUN \
      scl enable "rh-python${PYTHON_VERSION}" -- python -m venv "${APP_VENV}" --prompt app-root \
  &&  "${APP_VENV}/bin/python" -m pip install --upgrade --no-cache-dir pip setuptools wheel \
  &&  "${APP_VENV}/bin/python" -m pip install -r /tmp/requirements.txt \
  &&  chown -R "${APP_UID}:${APP_GID}" "${APP_VENV}"

# Entrypoint with all SCL's/ENV enabled
COPY ./dev_tools/docker/builder/entrypoint.sh /usr/bin/entrypoint
RUN chmod a+rx "/usr/bin/entrypoint"

# thou shall not root
USER $APP_UID:$APP_GID

ENV \
    BASH_ENV="/usr/bin/entrypoint" \
    ENV="/usr/bin/entrypoint" \
    PROMPT_COMMAND=". /usr/bin/entrypoint" \
    LD_LIBRARY_PATH="/usr/local/lib/"

ENTRYPOINT [ "/usr/bin/entrypoint" ]