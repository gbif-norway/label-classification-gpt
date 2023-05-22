import os
import json
import requests
from sqlalchemy import create_engine, text

# url = os.environ['ANNOTATER_URI']
# query_string = f'{url}?search=https://storage.gbif-no.sigma2.no/italy&source=pythondwc_v1&limit=1000'
# response = requests.get(query_string)

def get_connection():
  return create_engine(f'postgresql://{os.environ["DO_PG_USER"]}:{os.environ["DO_PG_PASSWORD"]}@{os.environ["DO_PG_URI"]}:{os.environ["DO_PG_PORT"]}/annotater')

with get_connection().begin() as conn:
  #sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
  sql = "SELECT * from api_annotation LIMIT 1;"
  results = conn.execute(text(sql))
  print(results.first())
  #sql = "DELETE FROM api_annotation WHERE source='pythondwc_v1';"
  import pdb; pdb.set_trace() 