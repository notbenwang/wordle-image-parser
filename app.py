from flask import Flask, request, render_template
from automation import ImageTool

app = Flask(__name__)
variable = 21
def array_to_string(arr):
    string = ""
    for i, item in enumerate(arr):
        string += item
        if i != len(arr) - 1:
            string += ", "
    return string


def startup():
    reader = ImageTool()
    default_url = "wordle_images/image_497.jpg"
    return reader, default_url

reader, default_url = startup()

@app.route('/', methods=['POST', 'GET'])
def index():
    global default_url
    if request.method == 'POST':
        # print(request.files['file_input'])
        file = request.files['file']
        default_url = file.filename 
        print(default_url)
    return render_template("app.html", default_url=default_url)
