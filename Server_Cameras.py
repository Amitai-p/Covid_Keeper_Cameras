from Cameras import *
from flask import (
    Flask,
)

import json

# Create the application instance
app = Flask(__name__, template_folder="templates")

import hashlib


# Get password and return the hash of this string.
def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


# Load the secret key for the cameras and the manager.
def load_key():
    """
    Loads the key named `secret.key` from the current directory.
    """
    return open(PATH_TO_SECRET_KEY, "rb").read()


NAME_IMAGE = 'img'


# Get the images for sending to storage for the manager.
def get_images_for_sending():
    list_images = get_images()
    data = {}
    for i in range(len(list_images)):
        key = NAME_IMAGE + str(i)
        data[key] = base64.encodebytes(list_images[i]).decode('utf-8')
    result = json.dumps(data)
    from cryptography.fernet import Fernet
    key = load_key()
    # Encode the message.
    encoded_message = result.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)
    print("result: ", encrypted_message)
    result = encrypted_message
    return result


# Run the server so that the cameras will listen when they have to send images to the manager.
def run_server():
    import time
    time.sleep(5)
    while True:
        try:
            # Lock the mutex of the DB.
            mutex.acquire()
            flag = b.get_camera_config_flag()
            # Unlock the mutex of the DB.
            mutex.release()
            print("flag sending to storage:", flag)
            if int(flag) == 1:
                images = get_images_for_sending()
                # Lock the mutex of the DB.
                mutex.acquire()
                b.upload_images_txt_to_storage(images)
                b.set_camera_config_flag_from_camera()
                # Unlock the mutex of the DB.
                mutex.release()
            import time
            # Wait for the next round.s
            time.sleep(1)
        except:
            pass
