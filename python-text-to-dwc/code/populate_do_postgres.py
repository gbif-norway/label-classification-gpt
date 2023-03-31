import os
from google.cloud import bigquery
import pandas as pd
from sqlalchemy import create_engine, text

def get_connection():
  return create_engine(f'postgresql://{os.environ["DO_PG_USER"]}:{os.environ["DO_PG_PASSWORD"]}@{os.environ["DO_PG_URI"]}:{os.environ["DO_PG_PORT"]}/{os.environ["DO_PG_DB"]}')

def bigquery(sql):  
  from google.cloud import bigquery  # Not sure why this has to be here, but it does...
  client = bigquery.Client()
  query_job = client.query(sql)
  return query_job.result(page_size=2000)

def _populate(bigquery_sql, table_sql, table_name):
  print('populating')
  with get_connection().begin() as conn:
    conn.execute(text((table_sql)))
  with get_connection().begin() as conn:
    i = 0
    for df in bigquery(bigquery_sql).to_dataframe_iterable():
      print(f'Running {i}')
      df.fillna('', inplace=True)
      df.to_sql(table_name, conn, if_exists='append', method='multi', index=False) 
      i += 1
  # with get_connection().begin() as conn:
  #   count = conn.execute(text('select count(*) from taxonomy;')).first()[0]
  #   print(f'Populated {count} records')

def populate_taxonomy():
  with open('taxonomy_query.sql', 'r') as file:
    bigquery_sql = file.read()
  table_sql = 'DROP TABLE IF EXISTS taxonomy; CREATE TABLE taxonomy (family TEXT, genus TEXT, infraspecificepithet TEXT, PRIMARY KEY (family, genus, infraspecificepithet));'
  _populate(bigquery_sql, table_sql, 'taxonomy')

def populate_distinct_taxonomy_views():
  for unit in ['genus', 'family']:
    with get_connection().begin() as conn:
      conn.execute(text(f'DROP VIEW IF EXISTS distinct_{unit}; CREATE VIEW distinct_{unit} AS SELECT DISTINCT {unit} FROM taxonomy;'))

def populate_people():
  with open('people_query.sql', 'r') as file:
    bigquery_sql = file.read()
  table_sql = 'DROP TABLE IF EXISTS people; CREATE TABLE people (person_name TEXT, countrycode TEXT, person_count INTEGER, PRIMARY KEY (person_name, countrycode));'
  _populate(bigquery_sql, table_sql, 'people')
  drops = ['no disponible', 'anonymous', 'anon.', 'anon', 'unknown', 'et al.', 'identified by the collector', 'collector', 'herbarium']
  for drop in drops:
    with get_connection().begin() as conn:
      conn.execute(text(f"DELETE FROM people WHERE person_name = '{drop}'"))
  entities = ['herbarium', 'institute', 'museum', 'university']
  for entity in entities:
    with get_connection().begin() as conn:
      conn.execute(text(f"DELETE FROM people WHERE person_name LIKE '%{entity}%' OR person_name LIKE '{entity}%' OR person_name LIKE '%{entity}' OR person_name LIKE '{entity}'"))
  with get_connection().begin() as conn:
    conn.execute(text(f"DELETE FROM people WHERE person_name LIKE '%erbariu%'"))
  with get_connection().begin() as conn:
    conn.execute(text('DELETE FROM people WHERE LENGTH(person_name) > 50;'))
    conn.execute(text('DELETE FROM people WHERE LENGTH(person_name) < 4;'))

def populate_distinct_people_view():
  with get_connection().begin() as conn:
    conn.execute(text(f'DROP VIEW IF EXISTS distinct_people; CREATE VIEW distinct_people AS SELECT DISTINCT person_name FROM people;'))

def add_fuzzystrmatch():
  with get_connection().begin() as conn:
      conn.execute(text('CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;'))

import pdb; pdb.set_trace()
# import code
# code.interact()