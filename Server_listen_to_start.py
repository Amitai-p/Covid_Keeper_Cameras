import threading

from Starter_Cameras import start_all, stop_all
from flask import (
    Flask, request,
    render_template,
    jsonify, Response)

# Create the application instance
app = Flask(__name__, template_folder="templates")


# Create a URL route in our application for "/"
@app.route('/', methods=['POST'])
def home():
    data = request.values.dicts[1]
    print(data)
    if data['action'] == 'start':
        print('start all')
        x = threading.Thread(target=start_all)
        x.start()
    if data['action'] == 'stop':
        print('stop all')
        x = threading.Thread(target=stop_all)
        x.start()
    print("send response")
    return Response("ok")


# def send_actions():
# url = 'http://127.0.0.1:5008/'
# # data = json.dumps("start")
# data = {'action': 'stop'}
# # data = {'action': 'start'}
# x = requests.post(url, data=data)
# print(x)

def main():
    while True:
        try:
            from waitress import serve
            serve(app, host="127.0.0.1", port=5008)
            # app.run(debug=True)
        except:
            a = 1


if __name__ == '__main__':
    main()
