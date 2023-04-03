import os
import json
import requests
from google.cloud import vision
import io
from PIL import Image, ImageDraw

def get_image(path = './ambrosia_maritima.jpg'):
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    return content

def get_crop_hint():
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=get_image())
    response = client.crop_hints(image=image)
    # Full response only returns one crop hint
    # crop_hints_annotation {
    #     crop_hints {
    #         bounding_poly {vertices {y: 764} vertices { x: 3506 y: 764 } vertices { x: 3506 y: 2746 } vertices { y: 2746 }
    #         }
    #         confidence: 0.5
    #         importance_fraction: 0.828965068
    #     }
    # }

def draw_boxes(image, bounds, color):
    """Draw a border around the image using the hints in the vector list."""
    draw = ImageDraw.Draw(image)

    for bound in bounds:
        draw.polygon(
            [
                bound[0]['x'],
                bound[0]['y'],
                bound[1]['x'],
                bound[1]['y'],
                bound[2]['x'],
                bound[2]['y'],
                bound[3]['x'],
                bound[3]['y'],
            ],
            None,
            color,
        )
    return image

def ocr(image):
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=get_image(image))
    return client.text_detection(image=image)

def update_vertices(vertices1, vertices2):
    min_x = min(vertices1[0]['x'], vertices2[0]['x'])
    min_y = min(vertices1[0]['y'], vertices2[0]['y'])
    max_x1 = max(vertices1[2]['x'], vertices2[2]['x'])
    max_y1 = max(vertices1[2]['y'], vertices2[2]['y'])
    max_x2 = max(vertices1[3]['x'], vertices2[3]['x'])
    max_y2 = max(vertices1[3]['y'], vertices2[3]['y'])
    return [{'x': min_x, 'y': min_y}, {'x': max_x1, 'y': min_y}, {'x': max_x1, 'y': max_y1}, {'x': min_x, 'y': max_y2}]

def merge_blocks(sorted_blocks, threshold=300):
    merged_blocks = []

    for item in sorted_blocks:
        if not merged_blocks or item['top'] - merged_blocks[-1]['top'] > threshold:
            merged_blocks.append(item)
        else:
            merged_blocks[-1]['text'] += ' ' + item['text']
            merged_blocks[-1]['vertices'] = update_vertices(merged_blocks[-1]['vertices'], item['vertices'])

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
                'top': min(block['boundingBox']['vertices'][0]['y'], block['boundingBox']['vertices'][1]['y']),
                'text': '\n'.join(ps),
                'vertices': block['boundingBox']['vertices']
            }
            blocks.append(b)

    sorted_blocks = sorted(blocks, key=lambda x: x['top'])
    merged_blocks = merge_blocks(sorted_blocks)
    bounds = [b['vertices'] for b in merged_blocks]
    # im1 = Image.open('cistus.jpg')
    # width, height = im1.size
    # padding = 30
    # for i, block in enumerate(merged_blocks):
    #     bound = block['vertices']
    #     left = max(0, min([v['x'] for v in bound]) - padding)
    #     upper = max(0, min([v['y'] for v in bound]) - padding)
    #     right = min(width, max([v['x'] for v in bound]) + padding)
    #     lower = min(height, max([v['y'] for v in bound]) + padding)
    #     print(f'{i} = {block["text"]}')
    #     im1.crop((left, upper, right, lower)).save(f'out/{i}_cropped.jpg')
    # import pdb; pdb.set_trace()
    #return merged_blocks
    # newimg = draw_boxes(im1, bounds, 'red')
    # newimg.save('new.jpg')
    # another = draw_boxes(im1, [b['vertices'] for b in sorted_blocks], 'red')
    # another.save('another.jpg')
    stext = [x['text'] for x in sorted_blocks]
    mtext = [x['text'] for x in merged_blocks]
    return mtext, stext

# import pdb; pdb.set_trace()
# res = ocr('out/.jpg')
# res.full_text_annotation.text
# Get some ocr text from somewhere... in this case, the annotater api
url = os.environ['ANNOTATER_URI']
query_string = f'{url}?search=https://storage.gbif-no.sigma2.no/italy&source=gcv_ocr_pages&limit=5&offset=0'
#query_string = f'{url}?resolvable_object_id=https://storage.gbif-no.sigma2.no/italy/padua-2023-03-24/cistus.jpg&source=gcv_ocr_pages&limit=5&offset=0'
response = requests.get(query_string)
results = response.json()['results']
# first = results[0]['annotation']
# print(results[0]['resolvable_object_id'])
# flat = flatten(first)
flats = []
for result in results:
    print(result['resolvable_object_id'])
    f = flatten(result['annotation'])
    flats.append({
        'ID': result['resolvable_object_id'],
        'Text_merged': f[0],
        'Text_sorted': f[1]
    })
for v in flats: 
    print(f'{v["ID"]}\n\n{v["Text_merged"]}\n\n{v["Text_sorted"]}\n\n\n')
import pdb; pdb.set_trace()
# "imageContext": {
#         "languageHints": ["en-t-i0-handwrit"]
#       }