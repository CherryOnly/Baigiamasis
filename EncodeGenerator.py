import os
import cv2
import face_recognition
import pickle
import firebase_admin
from firebase_admin import credentials, storage
from io import BytesIO

import numpy as np

# Initialize Firebase
cred = credentials.Certificate("baigiamasisServiceKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://baigiamasis-darbas-cea75-default-rtdb.firebaseio.com/",
    'storageBucket': "baigiamasis-darbas-cea75.appspot.com"
})

# Initialize Firebase Storage
bucket = storage.bucket()

# Function to download image into memory and decode it
def download_image_into_memory(blob_name):
    blob = bucket.blob(blob_name)
    data = blob.download_as_bytes()
    image_stream = BytesIO(data)
    image_stream.seek(0)
    file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    return img

# Function to find encodings of face images
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        except IndexError as e:
            print(f"No faces found in the image, skipping: {e}")
    return encodeList

# Get list of blobs from Firebase Storage
blobs = bucket.list_blobs()
blob_names = [blob.name for blob in blobs]

imgList = []
studentIds = []

# Iterate over the blob names and download images
for blob_name in blob_names:
    print(f"Downloading {blob_name}...")
    img = download_image_into_memory(blob_name)
    if img is not None:
        imgList.append(img)
        studentId = os.path.splitext(blob_name.replace('Images/', ''))[0] # assuming your blob_name has a 'Images/' prefix
        studentIds.append(studentId)
    else:
        print(f"Failed to download image: {blob_name}")

print("Student IDs:", studentIds)

# Encoding the faces
print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding Complete")

# Save the encodings to a file
file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Saved")
