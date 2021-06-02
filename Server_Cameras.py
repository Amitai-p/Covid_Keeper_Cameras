from Cameras import *
from flask import (
    Flask,
    Response)
from flask import jsonify, request
import json, os, signal

# Create the application instance
app = Flask(__name__, template_folder="templates")

import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def load_key():
    """
    Loads the key named `secret.key` from the current directory.
    """
    return open("secret.key", "rb").read()


# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/

    :return:        the rendered template 'home.html'
    """
    print("in home")

    try:
        if hash_password(request.headers['authentication']) == config["PASSWORD_MANAGER"]:
            list_images = get_images()
    except:
        list_images = []
    data = {}
    for i in range(len(list_images)):
        key = 'img' + str(i)
        data[key] = base64.encodebytes(list_images[i]).decode('utf-8')
    result = json.dumps(data)
    print("result:   ", result)
    from cryptography.fernet import Fernet
    key = load_key()
    encoded_message = result.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)
    # frame = Fernet.encrypt(frame)
    print("frame: ", encrypted_message)
    result = encrypted_message
    return Response(result)


@app.route('/stop_server', methods=['GET'])
def stopServer():
    print("stopppp")
    os.kill(os.getpid(), signal.SIGINT)
    print("get pid")
    return jsonify({"success": True, "message": "Server is shutting down..."})


def get_images_for_sending():
    list_images = get_images()
    data = {}
    for i in range(len(list_images)):
        key = 'img' + str(i)
        data[key] = base64.encodebytes(list_images[i]).decode('utf-8')
    result = json.dumps(data)
    print("result:   ", result)
    from cryptography.fernet import Fernet
    key = load_key()
    encoded_message = result.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)
    print("frame: ", encrypted_message)
    result = encrypted_message
    return result


def run_server():
    # import socket
    # my_ip = socket.gethostbyname(socket.gethostname())
    # my_ip = '46.19.86.1'
    # my_port = 5000
    import time
    time.sleep(5)
    while True:
        try:
            # from waitress import serve
            # serve(app, host=my_ip, port=my_port)
            mutex.acquire()
            flag = b.get_camera_config_flag()
            mutex.release()
            print("flaggg:", flag)
            if int(flag) == 1:
                images = get_images_for_sending()
                mutex.acquire()
                b.upload_images_txt_to_storage(images)
                b.set_camera_config_flag_from_camera()
                mutex.release()
            import time
            time.sleep(1)
            # app.run(debug=True)
        except:
            a = 1
