import logging
import os
from datetime import datetime
import pandas as pd
from minio import Minio
from minio.commonconfig import CopySource
import requests


url = os.environ['ANNOTATER_URI']
filter = 'source=gpt4&search=https://storage.gbif-no.sigma2.no/test/TNU/Labiatae/&limit=9999&offset=0'
query_string = f'{url}?{filter}'
response = requests.get(query_string)
results = response.json()['results']
in_df = pd.read_csv('source-tnu.txt', header=0, dtype='str')

results_list = []
for res in results:
    r = res['annotation']['choices'][0]['message']['content']
    r['associatedMedia'] = res['resolvable_object_id']
    r['modified'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    gcv_annotation = requests.get(f'source=gcv_ocr_text&resolvable_object_id={r["resolvable_object_id"]}')
    r['verbatimLabel'] = response.json()['results'][0]
    results_list.append(r)
results_df = pd.DataFrame(results_list)
concat_df = pd.concat([in_df, results_df])
concat_df.to_csv('source.txt', encoding='utf-8', index=False)
import pdb; pdb.set_trace()

    # appended.to_csv('/srv/code/source.txt', encoding='utf-8', index=False) # appended.iloc[-1:].to_csv('/srv/code/source.txt', encoding='utf-8', index=False, header=False)
