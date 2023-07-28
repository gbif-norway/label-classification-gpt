#%%
import os
import ast
import re
import logging
from minio import Minio
from google.cloud import vision
import openai
from tenacity import retry, wait_exponential
import requests
import pandas as pd

#%% Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#%% Constants
BUCKET_NAME = 'img'
BUCKET_PREFIX = 'tajikistan/TNU/2023-07-27/'
MINIO_URI = os.getenv('MINIO_URI')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
GPT_API_KEY = os.getenv('GPT_API_KEY')
GPT_PROMPT = os.getenv('GPT_PROMPT')
GPT_MODEL = os.getenv('GPT_MODEL')
OUTPUT_FILE = f"{BUCKET_NAME}-{BUCKET_PREFIX.replace('/','-')}.csv"

#%% Creating clients
minio_client = Minio(MINIO_URI, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY)
vision_client = vision.ImageAnnotatorClient()

# Set OpenAI key
openai.api_key = GPT_API_KEY

def get_images(bucket_name, prefix):
    logging.info(f"Fetching images from bucket: {bucket_name}, prefix: {prefix}")
    objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=True)
    image_urls = [f"https://{MINIO_URI}/{bucket_name}/{obj.object_name}" for obj in objects if obj.object_name.endswith((".jpg", ".jpeg", ".png"))]
    logging.info(f"Found {len(image_urls)} images")
    return image_urls

@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def detect_text(image_url):
    logging.info(f"Detecting text in image: {image_url}")
    image = vision.Image()
    image.source.image_uri = image_url
    response = vision_client.text_detection(image=image)
    texts = '\n'.join([text.description for text in response.text_annotations])
    return texts

@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def standardise_text(text, system_prompt):
    logging.info("Standardizing text")
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": text
        }
    ]
    chat_completion = openai.ChatCompletion.create(model=GPT_MODEL, messages=messages)
    content = chat_completion.choices[0].message.content
    return ast.literal_eval(content)

def get_uuid(image_url):
    pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    uuid = re.findall(pattern, image_url)
    return uuid[0] if uuid else None

def main():
    images = get_images(BUCKET_NAME, BUCKET_PREFIX)
    system_prompt = requests.get(GPT_PROMPT).text

    res = []
    for idx, image_url in enumerate(images, start=1):
        logging.info(f"Processing image {idx}/{len(images)}")
        text = detect_text(image_url)
        uuid = get_uuid(image_url)
        if uuid is None:
            logging.error(f"No UUID found in image URL: {image_url}")
            continue
        dwc = standardise_text(text, system_prompt)
        dwc['occcurrenceID'] = uuid
        dwc['associatedMedia'] = image_url
        res.append(dwc)
        dwc_df = pd.DataFrame(res)
        dwc_df.to_csv(OUTPUT_FILE)
    logging.info(f"Processing complete. Processed {len(res)} images. Saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

#%%

