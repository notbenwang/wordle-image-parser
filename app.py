from flask import Flask, render_template
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

@app.route('/')
def index():
    return render_template("app.html", default_url=default_url)
