# %%
import os
from google.cloud import bigquery
import pandas as pd
from sqlalchemy import create_engine, text
# %%
def get_connection():
  return create_engine(f'postgresql://{os.environ["DO_PG_USER"]}:{os.environ["DO_PG_PASSWORD"]}@{os.environ["DO_PG_URI"]}:{os.environ["DO_PG_PORT"]}/{os.environ["DO_PG_DB"]}')
# %%
genus = 'Adianthum'
sql = f"""
    SELECT genus, levenshtein(genus, '{genus}') AS distance
    FROM distinct_genus
    WHERE levenshtein(genus, '{genus}') <=3
    ORDER BY distance ASC
    LIMIT 5;"""
# %%
name = 'VISIANI'
sql = f"""
    SELECT person_name, levenshtein(person_name, '{name}') AS distance
    FROM people
    WHERE levenshtein(person_name, '{name}') <= 3
    AND countrycode = 'IT'
    ORDER BY distance ASC
    LIMIT 3;
"""
# %%
with get_connection().begin() as conn: results = conn.execute(text(sql))
# %%
sql = "SELECT pg_size_pretty( pg_database_size('bigquery_cache') );"
# %%
sql = "SELECT count(*) from people where countrycode='IT';"
# %%
sql = "SELECT distinct countrycode from people;"
# %%
sql = "SELECT count(*) from people;"
