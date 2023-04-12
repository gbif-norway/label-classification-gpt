import os
import json
from minio import Minio
from google.cloud import vision
import pika

# RabbitMQ connection
params = pika.ConnectionParameters(host='rabbitmq')
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue=os.environ['INPUT_QUEUE_ANNOTATE'])

def get_images(bucket_name, prefix):
    minio_client = Minio(os.getenv('MINIO_URI'), access_key=os.getenv('MINIO_ACCESS_KEY'), secret_key=os.getenv('MINIO_SECRET_KEY'))
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    return [obj.object_name for obj in objects if obj.object_name.endswith((".jpg", ".jpeg", ".png"))]

def send_to_ocr(image_url):
    gcv_client = vision.ImageAnnotatorClient()
    response = gcv_client.annotate_image({
        "image": {"source": {"image_uri": image_url}},
        "features": [{"type_": vision.Feature.Type.TEXT_DETECTION}],
        "image_context": {"language_hints": ["no", "la"]},
    })
    return response.text_annotations[0].description if response.text_annotations else None
    #return response

def send_to_rabbitmq(minio_url, ocr_results):
    payload = { "ID": minio_url, "Text": ocr_results, "Source": "gcv_td_whints_text" }
    channel.basic_publish(exchange="", routing_key=os.environ['INPUT_QUEUE_ANNOTATE'], body=json.dumps(payload))

# def ocr_algae():
bucket_name = "img"
prefix = "uio-algae/"

image_names = get_images(bucket_name, prefix)
print(image_names)
for image_name in image_names:
    minio_url = f"https://{os.getenv('MINIO_URI')}/{bucket_name}/{image_name}"
    print(minio_url)
    ocr_results = send_to_ocr(minio_url)
    if ocr_results:
        send_to_rabbitmq(minio_url, ocr_results)

connection.close()

# import pdb; pdb.set_trace()