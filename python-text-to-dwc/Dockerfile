FROM python:3-slim
RUN pip install --upgrade pip && pip install pika pandas db-dtypes psycopg2-binary 
RUN pip install google-cloud-bigquery google-auth google-auth-httplib2 google-api-python-client pycountry sqlalchemy 
RUN pip install --timeout=10000 spacy 
RUN pip install taxonerd
WORKDIR /srv