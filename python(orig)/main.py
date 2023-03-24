
#%%
from lib.ocr import get_text_from_local_image
from lib.gpt import extract_dwc
import json

#%%
api_key = ""
image_path = ""
#%%
ocr_text = get_text_from_local_image(image_path)
resp = extract_dwc(api_key, ocr_text=ocr_text)
content = json.loads(resp['choices'][0]['message']['content'])
content

# %%
