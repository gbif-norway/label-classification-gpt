import os
import json
import requests
from google.cloud import vision
import io
import pika

import itertools

def is_close(block1, block2, distance=300):
    for point1, point2 in itertools.product(block1['vertices'], block2['vertices']):
        if abs(point1['x'] - point2['x']) <= distance and abs(point1['y'] - point2['y']) <= distance:
            return True
    return False

def merge_blocks(block1, block2):
    merged_vertices = [
        {"x": min(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": min(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": max(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": min(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": max(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": max(v["y"] for v in block1["vertices"] + block2["vertices"])},
        {"x": min(v["x"] for v in block1["vertices"] + block2["vertices"]), "y": max(v["y"] for v in block1["vertices"] + block2["vertices"])}
    ]
    return {'vertices': merged_vertices, 'text': block1['text'] + ' ' + block2['text']}

def merge_close_blocks(blocks, distance=300):
    merged_blocks = []
    merged_indices = set()
    has_merged = False

    for i, block1 in enumerate(blocks):
        if i in merged_indices:
            continue

        new_block = block1.copy()
        for j, block2 in enumerate(blocks):
            if j in merged_indices or i == j:
                continue

            if is_close(new_block, block2, distance):
                new_block = merge_blocks(new_block, block2)
                merged_indices.add(j)
                has_merged = True

        merged_blocks.append(new_block)
        merged_indices.add(i)

    if has_merged:
        return merge_close_blocks(merged_blocks, distance)
    else:
        return merged_blocks

def flatten(document):
    blocks = []
    for page in document:
        for block in page['blocks']:
            ps = []
            for paragraph in block['paragraphs']:
                ws = []
                for word in paragraph['words']:
                    ws.append(''.join([l['text'] for l in word['symbols']]))
                ps.append(' '.join(ws))
            b = {
                #'top': min(block['boundingBox']['vertices'][0]['y'], block['boundingBox']['vertices'][1]['y']),
                'text': ' '.join(ps),
                'vertices': block['boundingBox']['vertices']
            }
            blocks.append(b)

    #sorted_blocks = sorted(blocks, key=lambda x: x['top'])
    merged_blocks = merge_close_blocks(blocks)
    return '\n'.join([b['text'] for b in merged_blocks])
    #stext = [x['text'] for x in sorted_blocks]
    #mtext = [x['text'] for x in merged_blocks]
    #return {'merged': mtext, 'sorted': stext}

connection_params = pika.ConnectionParameters(host='rabbitmq')
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue=os.environ['INPUT_QUEUE_ANNOTATE'])

# Get some ocr text from somewhere... in this case, the annotater api
url = os.environ['ANNOTATER_URI']
#query_string = f'{url}?source=gcv_ocr_pages&search=https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/&limit=1'
#query_string = f'{url}?resolvable_object_id=https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/cistus.jpg&source=gcv_ocr_pages&limit=5&offset=0'
query_string = f'{url}?source=gcv_ocr_pages&limit=1&offset=0'
while True:
    response = requests.get(query_string)
    response_json = response.json()

    for result in response_json['results']:
        print(result['resolvable_object_id'])
        message = {
            'ID': result['resolvable_object_id'],
            'Text': flatten(result['annotation']), 
            'Source': 'gcv_merged_close_blocks'
        }
        channel.basic_publish(exchange='', routing_key=os.environ['INPUT_QUEUE_ANNOTATE'], body=json.dumps(message))

    if response_json['next']:
        query_string = response_json['next']
    else:
        break

import pdb; pdb.set_trace()
# "imageContext": {
#         "languageHints": ["en-t-i0-handwrit"]
#       }