FROM python:3.6


RUN pip install mlflow==1.3.0 && \
    pip install awscli --upgrade --user && \
    pip install boto3==1.9.240


COPY gamechangerml/mlflow/start_mlflow.sh start_mlflow.sh
RUN chmod 755 start_mlflow.sh
ENTRYPOINT ["/start_mlflow.sh"]
