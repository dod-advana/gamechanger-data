FROM nvidia/cuda:11.0-base
CMD nvidia-smi
#set up environment
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests -y curl
RUN apt-get install unzip
RUN apt-get -y install python3
RUN apt-get -y install python3-pip

ADD api/requirements.txt .
#RUN apt install --yes gcc python3-dev libc-dev
RUN pip3 install --upgrade pip wheel setuptools
RUN pip3 install --no-deps --trusted-host files.pythonhosted.org -r requirements.txt
RUN pip3 install awscli
RUN mkdir gc
# add API source code
COPY api/ dataScience/api/
# add source code
COPY src/. dataScience/src/
COPY setup_env.sh/ dataScience/setup_env.sh
COPY configs dataScience/configs
COPY scripts dataScience/scripts
# COPY transformer_cache transformer_cache

RUN chmod +x dataScience/api/fastapi/startFast.sh
#CMD gunicorn dataScience.api.fastapi.mlapp:app --bind 0.0.0.0:5000 --workers 1 -k uvicorn.workers.UvicornWorker --log-level debug --timeout 0 --graceful-timeout 0
ENTRYPOINT  ["/bin/bash",  "dataScience/api/fastapi/startFast.sh", "DEV"]