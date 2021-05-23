from Cameras import *
from flask import (
    Flask,
    Response)
from flask import jsonify, request
import json, os, signal

# Create the application instance
app = Flask(__name__, template_folder="templates")


# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser ULR
    localhost:5000/

    :return:        the rendered template 'home.html'
    """

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
