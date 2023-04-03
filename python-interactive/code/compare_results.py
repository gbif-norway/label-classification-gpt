import os
import json
import requests
import pandas as pd
import collections

def generate_html(dataframe: pd.DataFrame):
    table_html = dataframe.to_html(index=False, border=0, table_id="table", classes='table table-striped', justify='left', escape=False, render_links=True).replace('\\n', '<br>')
    # https://codepen.io/mugunthan/pen/RwbVqYO https://mark-rolich.github.io/Magnifier.js/ https://github.com/malaman/js-image-zoom
    script = """
    <script src="https://code.jquery.com/jquery-3.6.4.slim.min.js" integrity="sha256-a2yjHM4jnF9f54xUQakjZGaqYs/V1CYvWpoqZzC2/Bw=" crossorigin="anonymous"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"> type="text/javascript"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/dataTables.bootstrap5.min.js"> type="text/javascript"></script>
    <script>
        var options1 = {
            width: 250,
            zoomWidth: 300,
            offset: {vertical: 0, horizontal: 10}
        };
        const containers = document.querySelectorAll('.img-container');
        containers.forEach((container) => {
            new ImageZoom(container, options1);
        });
        $(document).ready(function () {
            $('#table').DataTable();
        });
    </script>
    """

    return f"""
    <html>
    <header>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
        <script src="https://unpkg.com/js-image-zoom@0.7.0/js-image-zoom.js" type="application/javascript"></script>
        <link href="https://cdn.datatables.net/1.13.4/css/dataTables.bootstrap5.min.css" rel="stylesheet">
        <style>
        .img-container {{
            max-width: 250px;
            height: 200px;
            display: block;
        }}
        .img-container-wrapper {{ width: 550px; display: block;}}
        tbody tr {{ height: 400px; }}
        body {{ padding: 2em; }}
        </style>
    </header>
    <body>
    {table_html}
    {script}
    </body>
    </html>
    """

url = os.environ['ANNOTATER_URI']
response = requests.get(f'{url}?source=gcv_ocr_text&notes=ITALY:Test OCR for Padua&limit=200&offset=0')
results = response.json()['results']
df_dict = {}
for result in results:
    id = result['resolvable_object_id']
    cols = {'ocr': result['annotation']}
    annotation_response = requests.get(f"{url}?resolvable_object_id={id}")
    annotations = annotation_response.json()['results']
    for annotation in annotations:
        if annotation['source'] == 'gpt4':
            try:
                gpt4 = annotation['annotation']['choices'][0]['message']['content']
            except KeyError:
                gpt4 = annotation['annotation']
            gpt4 = {k: v for k, v in gpt4.items() if v}
            gpt4 = dict(sorted(gpt4.items()))
            cols['gpt4'] = '\n'.join([f'{k}: {v}' for k, v in gpt4.items()])
            # for i in range(3):
            #     if f'gpt4_{i}' not in cols:
            #         cols[f'gpt4_{i}'] = gpt4
            #         break
        if annotation['source'] == 'pythondwc_v1':
            pythondwc = annotation['annotation']
            if 'agents' in pythondwc:
                pythondwc['recordedBy'] = '|'.join(pythondwc['agents'])
                del pythondwc['agents']
            pythondwc = dict(sorted(pythondwc.items()))
            #cols['pythondwc_v1'] = '\n'.join([f'{k}: {v}' for k, v in pythondwc.items()])
    df_dict[id] = cols

table = pd.DataFrame.from_dict(df_dict, orient='index')
table.insert(0, 'image', '<div class="img-container-wrapper"><div class="img-container"><img src="' + table.index + '" class="zoom-image"></div></div>')    # .str.replace('https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/', '')
with open("index.html", "w") as writer:
    writer.write(generate_html(table))
import pdb; pdb.set_trace()
table.to_csv('test.csv', index=False)

