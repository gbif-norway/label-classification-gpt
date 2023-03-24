# %%
from google.cloud import vision
from google.oauth2 import service_account
# %%

def get_text_from_local_image(image_path):
    # Set up the Google Vision API client
    credentials = service_account.Credentials.from_service_account_file(
        '/Users/amarok/src/herbarium_gpt/gapi.json')
    client = vision.ImageAnnotatorClient(credentials=credentials)

    # Read the image from the local drive
    with open(image_path, 'rb') as image_file:
        content = image_file.read()

    # Create an Image object with the content
    image = vision.Image(content=content)

    # Perform text detection on the image
    response = client.text_detection(image=image)

    # Print the full text found in the image
    return response.full_text_annotation.text


