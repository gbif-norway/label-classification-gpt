import pika
import os
import json
import requests

# Get some ocr text from somewhere... in this case, the annotater api
url = os.environ['ANNOTATER_URI']
query_string = f'{url}?source=gcv_ocr_text&limit=1'
response = requests.get(query_string)
text = response.json()['results'][0]['annotation']

# ann = "s, is\n1358\n1.49\n3.\nad\n*****\nHERB. PATAV. (PAD)\nMicromeria greu\nprope Lesine\nHD04822\ngręce\n8. pampon fldh\ nMh. pauciflon Us. bub.\nStalio\nSofie & andren\npy Lined\nVISIANI"
message = { 'ID': 'test-rukaya2', 'Text': text }

# Publish it to the GPT input queue channel (another service which writes to the annotater API is listening for output from this)
connection_params = pika.ConnectionParameters(host='rabbitmq')
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue=os.environ['INPUT_QUEUE_GPT'])
channel.basic_publish(exchange='', routing_key=os.environ['INPUT_QUEUE_GPT'], body=json.dumps(message))
import pdb; pdb.set_trace()