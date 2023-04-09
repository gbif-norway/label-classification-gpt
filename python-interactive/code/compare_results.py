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
            $('#table').DataTable( { "columns": [ null, null, { "width": "390px" }, { "width": "390px" } ] } );
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

def image_html(img_url):
    return f'<div class="img-container-wrapper"><div class="img-container"><img src="{img_url}" class="zoom-image"></div></div>'

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

def get_gbif_dwc_and_img(occurrenceID, datasetKey='68a0650f-96ae-499c-8b2a-a4f92c01e4b3'):
    query_string = f'https://api.gbif.org/v1/occurrence/search?datasetKey={datasetKey}&occurrenceID={occurrenceID}&mediaType=StillImage&multimedia=true'
    results = query_url(query_string)
    img = results[0]['media'][0]['identifier']
    return img, results[0]

def get_gpt4_dwc(id):
    gpt4 = query_url(f"{os.environ['ANNOTATER_URI']}?resolvable_object_id={id}&source=gpt4&limit=1")  # Should give most recent gpt4 annotation
    gpt4_ann = gpt4[0]['annotation']
    try:
        gpt4_ann = gpt4_ann['choices'][0]['message']['content']
    except KeyError:
        pass
    return gpt4_ann

def get_dwc_fields(record):
    dwcs = {key: value for (key, value) in record.items() if key in FIELDS and value is not None}
    dwcs = rename_keys(dwcs, {'elevation': 'verbatimElevation', 'location': 'locality'})
    return dwcs

def rename_keys(dct, key_map):
    return {key_map.get(key, key): value for key, value in dct.items()}

def standardise_dwcs_for_comparison(dict1, dict2):
    dict1, dict2 = get_dwc_fields(dict1), get_dwc_fields(dict2)
    all_keys = set(dict1.keys()) | set(dict2.keys())
    dict1, dict2 = map_dicts_to_keys(dict1, dict2, all_keys)
    return sort_dict(dict1), sort_dict(dict2)

def map_dicts_to_keys(dict1, dict2, keys):
    return ({key: dict1.get(key, None) for key in keys},
            {key: dict2.get(key, None) for key in keys})

def sort_dict(dct):
    return dict(sorted(dct.items()))

def compare_dwcs(dict1, dict2):
    dict1, dict2 = standardise_dwcs_for_comparison(dict1, dict2)
    common = {k: v for k, v in dict1.items() if str(dict2[k]).lower() == str(dict1[k]).lower()}
    handle_scientific_name(common, dict1, dict2)
    return (common,
            {k: v for k, v in dict1.items() if k not in common},
            {k: v for k, v in dict2.items() if k not in common})

def handle_scientific_name(common, dict1, dict2):
    if 'scientificName' not in common and dict1['scientificName'] is not None and dict2['scientificName'] is not None:
        name1, name2 = map(get_genus_species, (dict1['scientificName'], dict2['scientificName']))
        if name1 == name2:
            common['scientificName'] = name1.title()

def get_genus_species(scientific_name):
    return ' '.join(scientific_name.split(' ')[0:2]).lower()

def table_text(dwc_dict):
    return '\n'.join([f'{k}: {v}' for k, v in dwc_dict.items()])

def make_gbif_gpt4_comparison_tables(filter):
    results = query_url(f"{os.environ['ANNOTATER_URI']}?{filter}")
    html_dict = {}
    df_dict = {}
    for result in results:
        print(result['resolvable_object_id'])
        ocr = re.sub('UiO : Natural History Museum University of Oslo inches.+\n', '', result['annotation'])
        img, gbif_dwc = get_gbif_dwc_and_img(result['resolvable_object_id'])
        common, gbif_dwc_diff, gpt4_diff = compare_dwcs(gbif_dwc, get_gpt4_dwc(result['resolvable_object_id']))
        common_text = f'<div class="common"><h4>Common</h4>{table_text(common)}</div>'
        html_dict[result['resolvable_object_id']] = {
            'image': image_html(img),
            'ocr': ocr,
            'gbif_dwc': f'{common_text}<div class="different"><h4>Differing</h4>{table_text(gbif_dwc_diff)}</div>',
            'gpt4_dwc': f'{common_text}<div class="different"><h4>Differing</h4>{table_text(gpt4_diff)}</div>'
        }
        df_dict[result['resolvable_object_id']] = {
            'image': image_html(img),
            'ocr': ocr,
            'common': common,
            'gbif_dwc_diff': gbif_dwc_diff,
            'gpt4_diff': gpt4_diff
        }

    return pd.DataFrame.from_dict(html_dict, orient='index'), pd.DataFrame.from_dict(df_dict, orient='index')

filter = 'source=gcv_merged_close_blocks&search=urn:catalog:O&limit=200&offset=0'
html_table, df_table = make_gbif_gpt4_comparison_tables(filter)
with open('index-uio.html', 'w') as writer:
    writer.write(generate_html(html_table))
import pdb; pdb.set_trace()


# filter = 'source=gcv_ocr_text&notes=ITALY:Test OCR for Padua&limit=200&offset=0' # for Italy specimens
# img, gbif_dwc = id, None # for Italy specimens # .str.replace('https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/', '')
    
            # pythondwc = annotation['annotation']
            # if 'agents' in pythondwc:
            #     pythondwc['recordedBy'] = '|'.join(pythondwc['agents'])
            #     del pythondwc['agents']
            # pythondwc = dict(sorted(pythondwc.items()))