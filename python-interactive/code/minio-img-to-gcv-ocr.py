import pika
from minio import Minio
import json
import os

def get_images(bucket_name, prefix):
    minio_client = Minio(os.getenv('MINIO_URI'), access_key=os.getenv('MINIO_ACCESS_KEY'), secret_key=os.getenv('MINIO_SECRET_KEY'))
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    return [obj.object_name for obj in objects if obj.object_name.endswith((".jpg", ".jpeg", ".png"))]
 
bucket_name = "img"
prefix = "uio-algae/"
image_names = get_images(bucket_name, prefix)

connection_params = pika.ConnectionParameters(host='rabbitmq')
connection = pika.BlockingConnection(connection_params)
channel = connection.channel()
channel.queue_declare(queue=os.environ['INPUT_QUEUE_GCV_OCR'])

for image_name in image_names:
    minio_url = f"https://{os.getenv('MINIO_URI')}/{bucket_name}/{image_name}"
    body = json.dumps({ 'ID': minio_url, 'Text': minio_url, 'Source': 'minio'})
    import pdb; pdb.set_trace()
    channel.basic_publish(exchange='', routing_key=os.environ['INPUT_QUEUE_GCV_OCR'], body=body)


