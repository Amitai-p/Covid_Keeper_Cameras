from Cameras import *
from flask import (
    Flask,
    Response)
from flask import jsonify
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
    list_images = get_images()
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
    while True:
        try:
            from waitress import serve
            serve(app, host="127.0.0.1", port=5000)
            # app.run(debug=True)
        except:
            a = 1
