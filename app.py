from flask import Flask, request, render_template, flash
from automation import ImageTool
from PIL import Image, ImageDraw
import io
import base64 
import os
# from flask_modals import Modal

app = Flask(__name__)
# modal = Modal(app)

def array_to_string(arr):
    string = ""
    for i, item in enumerate(arr):
        string += item
        if i != len(arr) - 1:
            string += ", "
    return string


def startup():
    # Do these actions on startup
    reader = ImageTool()
    default_url = "static/wordle_images/image_497.jpg"
    wordle_statistic = reader.get_wordle_statistics_from_src(default_url)
    results = reader.get_data(wordle_statistic.text, wordle_statistic.color_grid)
    return reader, default_url, wordle_statistic, results

reader, default_url, wordle_statistic, results = startup()

app.secret_key = os.urandom(12)

@app.route('/', methods=['POST', 'GET'])
def index():
    global default_url, results, wordle_statistic
    
    if request.method == 'POST':
        # Convert input file into PIL and src
        file = request.files['file']
        buffer = io.BytesIO()
        file.save(buffer)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        img_pil = Image.open(buffer)
        img_src = f'data:image/png;base64,{base64_image}'
        
        
        try:
            uploaded_wordle_statistic = reader.get_wordle_statistics_from_img(file.filename, img_pil)
            uploaded_results = reader.get_data(uploaded_wordle_statistic.text, uploaded_wordle_statistic.color_grid)
        
        # Flash error message
        except:
            flash(f"An image was uploaded, but there was an error parsing image: {file.filename}")
            return render_template("app.html", default_url=default_url, img_src="static/wordle_images/image_497.jpg",
                            results=results, wordle_statistic=wordle_statistic)
        if not uploaded_wordle_statistic or not uploaded_results:
            flash(f"An image was uploaded, but there was an error parsing image: {file.filename}")
            return render_template("app.html", default_url=default_url, img_src="static/wordle_images/image_497.jpg",
                            results=results, wordle_statistic=wordle_statistic)

        # Return input file
        return render_template("app.html", default_url=file.filename, img_src=img_src, results=uploaded_results, wordle_statistic=uploaded_wordle_statistic)
    
    # Return default
    return render_template("app.html", default_url=default_url, img_src="static/wordle_images/image_497.jpg",
                            results=results, wordle_statistic=wordle_statistic)
