import json
import numpy as np
import os
import psycopg2
from rapidfuzz import process
import re
from typing import List
import itertools

# https://github.com/zas97/ocr_weighted_levenshtein
# https://github.com/luozhouyang/python-string-similarity#weighted-levenshtein
# https://github.com/infoscout/weighted-levenshtein
# https://github.com/maxbachmann/rapidfuzz

def get_connection():
   return psycopg2.connect(
      dbname=os.environ["DO_PG_DB"],
      user=os.environ["DO_PG_USER"],
      password=os.environ["DO_PG_PASSWORD"],
      host=os.environ["DO_PG_URI"],
      port=os.environ["DO_PG_PORT"]
  )

def get_from_postgres(item):
    with get_connection() as conn:
        with conn.cursor('ss') as cursor:
            cursor.execute(f'SELECT {item} from distinct_{item};')
            result_set = set()
            for rows in iter(lambda: cursor.fetchmany(8000), []):
                for row in rows:
                    result_set.add(row[0])
    return result_set

GENUS = get_from_postgres('genus')
FAMILY = get_from_postgres('family')
PERSON_NAME = get_from_postgres('person_name')
print('Loaded genera, families and person_names into memory')

def _get_latin_words_for_search(full: str) -> List[str]:
    full = ' '.join(re.split('\n', full))
    only_words = re.sub('[^A-Za-z()\s\-]', '', full)
    stripped_spaces = re.sub('\s+', ' ', only_words)
    return [x for x in re.split('\s', stripped_spaces.strip()) if len(x) > 3]

def get_scientific_name(full):
    full = _get_latin_words_for_search(full)
    # for i, val in enumerate(itertools.islice(GENUS, 10)): print(val)
    distances = process.cdist(full, GENUS, score_cutoff=70, workers=-1, )
    best = process.extractOne(full[0], GENUS, score_cutoff=70)
    import pdb; pdb.set_trace()