import uuid
import cv2
import skimage
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from skimage.color import rgb2gray
from skimage import filters # threshold_otsu, threshold_isodata
from skimage.morphology import binary_dilation, binary_erosion
import numpy as np
import glob


def get_decoded_qr(image_uri):
    im = skimage.io.imread(image_uri)
    cvgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    ret, bw_im = cv2.threshold(cvgray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    decoded_objects = decode(bw_im, symbols=[ZBarSymbol.QRCODE])
    return [x for x in decoded_objects if x.type == 'QRCODE'][0]

def fix_image_rotation(decoded, image_uri, out_filename):
    im = skimage.io.imread(image_uri)
    if decoded.orientation is not None and decoded.orientation != 'UNKNOWN':
        if decoded.orientation == 'LEFT':
            # Rotate by 90 degrees clockwise
            im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
        elif decoded.orientation == 'RIGHT':
            # Rotate by 270 degrees clockwise
            im = cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif decoded.orientation == 'DOWN':
            # Rotate by 180 degrees clockwise
            im = cv2.rotate(im, cv2.ROTATE_180)
    skimage.io.imsave(out_filename, im)

def get_uuid(qr_data):
    if not len(qr_data):
        raise Exception(f'No QR codes detected in image')

    code = qr_data.data.decode('utf-8').split('/')[-1]
    # if len(codes) > 2:
    #     raise Exception(f'More than 2 QR codes/barcodes detected in image - {codes}')

    # uuid = next((x for x in codes if is_uuid4(x)), False)
    # if not uuid:
        # raise Exception(f'No UUID detected in image - {code}')
    # codes.remove(uuid)
    if is_uuid4(code):
        return code # The second code could be a catalogNumber, but for now they should just use uuids, codes.pop()

def is_uuid4(test_uuid, version=4):
    try:
        return uuid.UUID(test_uuid).version == version
    except ValueError:
        return False
    
# uri = 'IMG_0003.jpg'
# decoded_objects = get_decoded_qr(uri)
# fix_image_rotation(decoded_objects, uri)

folder = 'Gramineae2'
# for filename in glob.glob('in/Labiatae/*.jpg'):
for filename in glob.glob(f'in/{folder}/*.jpg'):
    decoded_objects = get_decoded_qr(filename)
    fix_image_rotation(decoded_objects, filename, f'out/{folder}/{get_uuid(decoded_objects)}.jpg')

import pdb; pdb.set_trace()