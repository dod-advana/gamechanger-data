FROM --platform=x86_64 registry.access.redhat.com/ubi8/python-36

ARG \
    PYTHON_VERSION_NO_DOTS=36 \
    GHOSTSCRIPT_VERSION=9.55.0 \
    JBIG2ENC_VERSION=0.29 \
    LEPTONICA_VERSION=1.82.0 \
    TESSERACT_OCR_VERSION=4.1.1 \
    TESSERACT_OCR_LANGPACK_VERSION=4.1.0 \
    POSTGRESQL_MAJOR_VERSION=13

# BRIEFLY ROOT
USER root

# PYTHON & LOCALE ENV VARS
ENV LANG="C.utf8" \
    LANGUAGE="C.utf8" \
    LC_ALL="C.utf8" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING="UTF-8"

# Additional Repos
RUN \
      rpm --import https://download.postgresql.org/pub/repos/yum/RPM-GPG-KEY-PGDG \
  &&  dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL \
  &&  rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-8 \
  &&  dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

RUN \
      dnf install -y \
        zip \
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
        libpng \
        libpng-devel \
        libtiff \
        libtiff-devel \
        libjpeg-turbo \
        libjpeg-turbo-devel \
        "python${PYTHON_VERSION_NO_DOTS}-devel" \
        ghostscript \
        qpdf-libs \
        "postgresql${POSTGRESQL_MAJOR_VERSION}" \
        "postgresql${POSTGRESQL_MAJOR_VERSION}-devel"

RUN \
    curl -LfSo /tmp/awscliv2.zip "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
    && echo "[INFO] Installing AWS CLI ..." && ( \
      unzip -q /tmp/awscliv2.zip -d /opt \
      &&  /opt/aws/install \
      &&  rm -f  /tmp/awscliv2.zip \
  ) 2>&1 1>/dev/null

# OCRMYPDF REQS: https://ocrmypdf.readthedocs.io/en/v12.7.0/installation.html
# ocrmypdf <- (compiled) tesserat 4.0+
#          <- (compiled) jbig2enc 0.29+ <- (c) leptonica
#          <- (skipped) unpaper 6.1+ (to support --clean flag...)
#          <- (rpm) pngquant 2.5+
#          <- (compiled) ghostscript 9.23+
#          <- (rpm) qpdf-libs ?????
#          <- (compiled) qpdf 8.2.1

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

# leptonica - tesseract dep
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

# tesseract - ocrmypdf dep
RUN \
  git clone --depth 1 --branch "${TESSERACT_OCR_VERSION}" https://github.com/tesseract-ocr/tesseract.git /opt/tesseract \
  && echo "[INFO] Installing from source: TESSERACT-OCR ..." && ( \
    cd /opt/tesseract \
    && export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig \
    && export PKG_CONFIG=/usr/bin/pkg-config \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
  ) 2>&1 1>/dev/null

# where tesseract language packs reside
ENV TESSDATA_PREFIX=/usr/local/share/tessdata/

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
    && make \
    && make install \
    && ldconfig \  
  ) 2>&1 1>/dev/null

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

# key directories
ENV \
  APP_ROOT="${APP_ROOT:-/opt/app-root}" \
  APP_VENV="${APP_VENV:-/opt/app-root/venv}" \
  APP_DIR="${APP_ROOT}/src"

RUN \
      mkdir -p "${APP_DIR}" "${APP_VENV}" \
  &&  python -m venv "${APP_VENV}" --prompt app-venv \
  && "${APP_VENV}/bin/python" -m pip install --upgrade --no-cache-dir pip setuptools wheel