import pika
import os
import json
import requests

def publish_to(results, queue, source=None):
    for result in results:
        # text = "s, is\n1358\n1.49\n3.\nad\n*****\nHERB. PATAV. (PAD)\nMicromeria greu\nprope Lesine\nHD04822\ngręce\n8. pampon fldh\ nMh. pauciflon Us. bub.\nStalio\nSofie & andren\npy Lined\nVISIANI"
        message = { 'ID': result['resolvable_object_id'], 'Text': result['annotation'], 'Source': source }

        # Publish it to a queue
        connection_params = pika.ConnectionParameters(host='rabbitmq')
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='', routing_key=queue, body=json.dumps(message))
        
# Get some ocr text from somewhere... in this case, the annotater api
url = os.environ['ANNOTATER_URI']
#filter = 'source=gcv_ocr_text&notes=ITALY:Test OCR for Padua&limit=200&offset=0'
#filter = 'source=gcv_ocr_text&search=urn:catalog:O&limit=200&offset=0'
# filter = 'source=gcv_merged_close_blocks&search=urn:catalog:O&limit=200&offset=0'
# filter = 'source=gcv_td_whints_text&limit=200&offset=0'
filter = 'source=gcv_ocr_text&search=https://storage.gbif-no.sigma2.no/test/TNU/Labiatae/&limit=200&offset=0'
query_string = f'{url}?{filter}'
response = requests.get(query_string)
results = response.json()['results']
# import pdb; pdb.set_trace()

# Get just the latest results
latest_results = {}
for res in results:
    if res['resolvable_object_id'] in latest_results:
        if res['id'] > latest_results[res['resolvable_object_id']]['id']:
            latest_results[res['resolvable_object_id']] = res
    else:
        latest_results[res['resolvable_object_id']] = res
import pdb; pdb.set_trace()
publish_to(latest_results, os.environ['INPUT_QUEUE_GPT'])
#publish_to(results, os.environ['INPUT_QUEUE_PYTHON_DWC'])