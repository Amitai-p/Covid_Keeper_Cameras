from Cameras import *
from flask import (
    Flask,
    Response)
from flask import jsonify, request
import json, os, signal

# Create the application instance
app = Flask(__name__, template_folder="templates")


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
    # list_images = get_images()
    if request.headers['authentication'] == config["PASSWORD_MANAGER"]:

        list_images = get_images()
    else:
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


def run_server():
    import socket
    my_ip = socket.gethostbyname(socket.gethostname())
    my_port = 5000
    while True:
        try:
            from waitress import serve
            serve(app, host=my_ip, port=my_port)
            # app.run(debug=True)
        except:
            a = 1
