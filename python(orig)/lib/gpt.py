# %%
import json
import requests
# %%
# Set up the OpenAI API

# Function to extract DWC terms using GPT-3


def extract_dwc(api_key, model="gpt-4", ocr_text=None):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    system_prompt = '''
    As an adept herbarium digitization system, I accurately classify extracted text from herbarium specimen scans into appropriate Darwin Core terms. When multiple strings fit one term, they are separated by "|".

I only extract following DWC terms:
- scientificName: Full scientific name, not containing identification qualifications.
- catalogNumber: Unique identifier for the record in the dataset or collection.
- recordNumber: Identifier given during recording, often linking field notes and Occurrence record.
- recordedBy: List of people, groups, or organizations responsible for recording the original Occurrence.
- year: Four-digit year of the Event.
- month: Integer for the month of the Event.
- day: Integer for the day of the Event.
- dateIdentified: Date when the subject was determined to represent the Taxon.
- identifiedBy: Person, group, or organization assigning the Taxon to the subject.
- verbatimIdentification: Taxonomic identification as it appeared in the original record.
- kingdom: Full scientific name of the kingdom in which the taxon is classified.
- country: Name of the country or major administrative unit for the Location.
- countryCode: Standard code for the country of the Location.
- decimalLatitude: Geographic latitude in decimal degrees of the Location's center.
- decimalLongitude: Geographic longitude in decimal degrees of the Location's center.
- location: A spatial region or named place.
- minimumElevationInMeters: The lower limit of the range of elevation in meters.
- maximumElevationInMeters: The upper limit of the range of elevation in meters.
- verbatimElevation: The original description of the elevation.

If I cannot identify information for a specific term, I leave it empty.
My responses are provided as minified JSON.
    '''
    messages = [{'role': 'system',
                 'content': system_prompt}]

    messages.append({
        'role': 'user',
        'content': ocr_text
    })

    data = {
        "model": model,
        "messages": messages or [{"role": "user", "content": "Hello!"}],
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.json()
