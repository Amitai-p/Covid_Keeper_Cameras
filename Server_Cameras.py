from Cameras import *
from flask import (
    Flask,
    render_template,
    jsonify, Response)

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
    # return render_template('./home.html')
    # print(get_images())
    # main_list = ["1", "2", "3", "4"]
    # return jsonify(main_list)
    list_images = get_images()
    # print(list_images)
    data = {}
    for i in range(len(list_images)):
        key = 'img' + str(i)
        # data[key] = base64.encodebytes(list_images[i]).decode('utf-8')
        data[key] = base64.encodebytes(list_images[i]).decode('utf-8')
        # data[key] = list_images[i]
    result = json.dumps(data)
    print("result:   ", result)
    return Response(result)


def run_server():
    while True:
        try:
            from waitress import serve
            serve(app, host="127.0.0.1", port=5000)
            # app.run(debug=True)
        except:
            a = 1
