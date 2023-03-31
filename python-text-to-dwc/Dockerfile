FROM python:3.8.2
RUN pip install --upgrade pip && pip install pika pandas db-dtypes psycopg2-binary
RUN pip install google-cloud-bigquery google-auth google-auth-httplib2 google-api-python-client pycountry sqlalchemy
RUN pip install --timeout=10000 nmslib
RUN pip install --timeout=10000 spacy
RUN pip install taxonerd
RUN pip install https://github.com/nleguillarme/taxonerd/releases/download/v1.5.0/en_core_eco_md-1.0.2.tar.gz
WORKDIR /srv