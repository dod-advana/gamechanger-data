FROM python:3.6.1
RUN apt-get install ca-certificates
ADD ./dev-requirements.txt ./dev-requirements.txt
ENV APP_REQUIREMENTS_PATH="dev-requirements.txt"
RUN pip install --upgrade pip setuptools wheel
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-2.2.5/en_core_web_lg-2.2.5.tar.gz
RUN pip install --trusted-host files.pythonhosted.org -r "$APP_REQUIREMENTS_PATH"
ADD . gamechangerml
ENTRYPOINT ["python", "-m", "gamechangerml.scripts.run_train_models", "--corpus","corpus/"]
