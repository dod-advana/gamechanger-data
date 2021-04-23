FROM pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime
ADD api/requirements.txt .
RUN apt-get update
#RUN apt install --yes gcc python3-dev libc-dev
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-deps --trusted-host files.pythonhosted.org -r requirements.txt
RUN apt-get -y install awscli
RUN mkdir gc
# add API source code
COPY api/ dataScience/api/
# add source code
COPY src/. dataScience/src/
COPY setup_env.sh/ dataScience/setup_env.sh
COPY configs dataScience/configs
COPY scripts dataScience/scripts
# COPY transformer_cache transformer_cache

#CMD gunicorn dataScience.api.fastapi.mlapp:app --bind 0.0.0.0:5000 --workers 1 -k uvicorn.workers.UvicornWorker --log-level debug --timeout 0 --graceful-timeout 0
CMD ["/bin/bash",  "dataScience/api/fastapi/startFast.sh", "DEV"]
