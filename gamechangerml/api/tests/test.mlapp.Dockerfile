FROM python:3.8-slim
ARG GC_ML_HOST
 
COPY ./gamechangerml/api/tests/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY ./ /opt/app-root/src
WORKDIR /opt/app-root/src
ENV PYTHONPATH=/opt/app-root/src
RUN pytest ./gamechangerml/api/tests/api_tests.py
# ENTRYPOINT ["pytest", "./gamechangerml/api/tests/api_tests.py"]

