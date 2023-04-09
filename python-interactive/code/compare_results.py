import os
import json
import requests
import pandas as pd
import re
import time

FIELDS = ['scientificName', 'catalogNumber', 'recordNumber', 'recordedBy', 'year', 'month', 'day', 'dateIdentified', 'identifiedBy', 'verbatimIdentification', 'country', 'decimalLatitude', 'decimalLongitude', 'location', 'minimumElevationInMeters', 'maximumElevationInMeters', 'verbatimElevation', 'elevation', 'locality']

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
            $('#table').DataTable( {
            "columns": [
                null,
                null,
                { "width": "390px" },
                { "width": "390px" }
            ]
            } );
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
            max-height: 200px;
            display: block;
        }}
        .img-container-wrapper {{ width: 550px; display: block;}}
        tbody tr {{ height: 400px; }}
        body {{ padding: 2em; }}
        .common {{ background-color: #ddffd6; padding: 2px; }}
        h4 {{ font-size: 0.8em; font-weight: bold;  }}
        .different {{ background-color: #ffd6d6; padding: 2px; }}
        </style>
    </header>
    <body>
    {table_html}
    {script}
    </body>
    </html>
    """

def get_dwc_fields(record):
    dwcs = { key:value for (key,value) in record.items() if key in FIELDS and value is not None }
    if 'elevation' in dwcs:
        dwcs['verbatimElevation'] = dwcs['elevation']
        del dwcs['elevation']
    if 'location' in dwcs:
        dwcs['locality'] = dwcs['location']
        del dwcs['location']
    return dwcs

def image_html(img_url):
    return f'<div class="img-container-wrapper"><div class="img-container"><img src="{img_url}" class="zoom-image"></div></div>'

def get_dwc_and_img_from_gbif(occurrenceID):
    query_string = f'https://api.gbif.org/v1/occurrence/search?datasetKey=68a0650f-96ae-499c-8b2a-a4f92c01e4b3&occurrenceID={occurrenceID}&mediaType=StillImage&multimedia=true'
    response = requests.get(query_string)
    if response.status_code == requests.codes.ok:
        results = response.json().get('results')
        img = results[0]['media'][0]['identifier']
        return img, get_dwc_fields(results[0])
    return None, None

def query_url(url):
    max_retries = 20
    retry_count = 0

    while retry_count < max_retries:
        response = requests.get(url)
        if response.ok:
            return response.json()['results']
        else:
            print(f'retry no {retry_count} failed')
            retry_count += 1
            time.sleep(5)
    
    raise Exception(f'URL {url} is still inaccessible')

url = os.environ['ANNOTATER_URI']
# filter = 'source=gcv_ocr_text&notes=ITALY:Test OCR for Padua&limit=200&offset=0' # for Italy specimens
filter = 'source=gcv_merged_close_blocks&search=urn:catalog:O&limit=200&offset=0' # for GBIF specimens
results = query_url(f'{url}?{filter}')
df_dict = {}
for result in results:
    id = result['resolvable_object_id']
    print(id)
    #if not result['annotation'].startswith('UiO : Natural History Museum University of Oslo inches'):
    ocr = re.sub('UiO : Natural History Museum University of Oslo inches.+\n', '', result['annotation'])
    # img, gbif_dwc = id, None # for Italy specimens # .str.replace('https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/', '')
    img, gbif_dwc = get_dwc_and_img_from_gbif(id) # for GBIF specimens
    cols = { 'image': image_html(img), 'ocr': ocr }
    annotations = query_url(f"{url}?resolvable_object_id={id}&source=gpt4")
    # Should make it so we get the most recent gpt4 annotation maybe?
    if not annotations:
        import pdb; pdb.set_trace()
    for annotation in annotations:
        if annotation['source'] == 'gpt4': 
            try:
                gpt4 = annotation['annotation']['choices'][0]['message']['content']
            except KeyError:
                gpt4 = annotation['annotation']
            gpt4 = {k: v for k, v in gpt4.items() if v}
            gpt4 = get_dwc_fields(gpt4)
            gpt4 = dict(sorted(gpt4.items()))
            break
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
    if gbif_dwc:
        all_keys = set(gbif_dwc.keys()) | set(gpt4.keys())
        gbif_dwc = {key: gbif_dwc.get(key, None) for key in all_keys}
        gpt4 = {key: gpt4.get(key, None) for key in all_keys}
        #cols['gbif_dwc'] = '\n'.join([f'{k}: {v}' for k, v in dict(sorted(gbif_dwc.items())).items()])
        #cols['gpt4'] = '\n'.join([f'{k}: {v}' for k, v in dict(sorted(gpt4.items())).items()])
        gbif_items = dict(sorted(gbif_dwc.items()))
        common = [f'{k}: {v}' for k, v in gbif_items.items() if str(gpt4[k]).lower() == str(gbif_dwc[k]).lower()]
        if 'scientificName' not in common and gbif_items['scientificName'] is not None and gpt4['scientificName'] is not None: 
            if ' '.join(gbif_items['scientificName'].split(' ')[0:2]).lower() == ' '.join(gpt4['scientificName'].split(' ')[0:2]).lower():
                common.append(f"scientificName: {gbif_items['scientificName'].split(' ')[0:2]}")
                del gbif_items['scientificName']
                del gpt4['scientificName']
        common_dwcs = '\n'.join(common)
        gbif_items_text = '\n'.join([f'{k}: {v}' for k, v in gbif_items.items() if str(gpt4[k]).lower() != str(gbif_dwc[k]).lower()])
        cols['gbif_dwc'] = f'<div class="common"><h4>Common</h4>{common_dwcs}</div><div class="different"><h4>Differing</h4>{gbif_items_text}</div>'
        gpt4_items = dict(sorted(gpt4.items()))
        gpt4_items_text = '\n'.join([f'{k}: {v}' for k, v in gpt4_items.items() if str(gpt4[k]).lower() != str(gbif_dwc[k]).lower()])
        cols['gpt4'] = f'<div class="common"><h4>Common</h4>{common_dwcs}</div><div class="different"><h4>Differing</h4>{gpt4_items_text}</div>'
    else:
        cols['gpt4'] = '\n'.join([f'{k}: {v}' for k, v in dict(sorted(gpt4.items())).items()])
    df_dict[id] = cols

table = pd.DataFrame.from_dict(df_dict, orient='index')
with open("index-uio.html", "w") as writer:
    writer.write(generate_html(table))
import pdb; pdb.set_trace()
table.to_csv('test.csv', index=False)

