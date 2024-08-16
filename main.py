from nicegui import app, ui, events
from automation import ImageTool
import io
import random
from PIL import Image, ImageDraw
import base64 

reader = ImageTool()

def array_to_string(arr):
    string = ""
    for i, item in enumerate(arr):
        string += item
        if i != len(arr) - 1:
            string += ", "
    return string

@ui.page('/')

def index():
    for url in app.urls:
        ui.link(url, target=url)

    ui.page_title("Wordle Image Parser")
    ui.label("Wordle Image Parser")
    
    with ui.row():
        number_input = ui.input("Manual Search")
        ui.button('Run Manual', on_click=lambda: run_automation(rand=False))
        ui.button('Random Image', on_click=lambda: run_automation(rand=True))
    
        file_upload_dialog = ui.dialog()
        with file_upload_dialog:
            ui.upload(on_upload=lambda e: handle_upload(e),
                on_rejected=lambda: ui.notify('Rejected!'),
                max_file_size=1_000_000).classes('max-w-full').props('accept=".png, image/*"')
        ui.button('Upload File', on_click=lambda:file_upload_dialog.open())

    default_url = "wordle_images/image_497.jpg"
    
    global wordle_statistic
    wordle_statistic = reader.get_wordle_statistics_from_src(default_url)
    results = reader.get_data(wordle_statistic.text, wordle_statistic.color_grid)
    
    img_path_label = ui.label(f"URL: {default_url}")
    results_label = ui.label(results.date_to_string())
    debug_dialog = ui.dialog() 
    with ui.row():
        wordle_image = ui.image(default_url).style('width: 300px; height: auto;')
    
    debug_checkboxes = []
    debug_images = []
    debug_labels = []
    checkbox_labels = ["Detected Points", "Estimated Points", "Cropbox", "Detect Text Filter"]
    
    with debug_dialog as dialog, ui.card().classes('w-300 h-128'):
        ui.label('Debug Dialog')
        with ui.column():
            for i in range(4):
                checkbox = ui.checkbox(checkbox_labels[i])
                debug_labels.append(ui.label())
                debug_image = ui.image().style('width: 250px; height: auto;')
                debug_image.set_visibility(False)               
                debug_checkboxes.append(checkbox)
                debug_images.append(debug_image)
            debug_checkboxes[0].on_value_change(lambda e: toggle_image(0, e.value))
            debug_checkboxes[1].on_value_change(lambda e: toggle_image(1, e.value))
            debug_checkboxes[2].on_value_change(lambda e: toggle_image(2, e.value))
            debug_checkboxes[3].on_value_change(lambda e: toggle_image(3, e.value))
            ui.button('Apply Settings', on_click=lambda:debug_dialog.close())
    ui.button('Debug Dialog', on_click=lambda:debug_dialog.open())
    
    guesses_label = ui.label( array_to_string(wordle_statistic.text))
    global data_labels
    data_labels = []
    data_column = ui.column()
    with data_column:
        for line in results.data_to_string():
            data_labels.append(ui.label(line))
    
    def update_data_labels(lines):
        global data_labels
        data_column.clear()
        data_labels.clear()
        with data_column:
            for line in lines:
                data_labels.append(ui.label(line))

    def toggle_image(index, visible):
        global wordle_statistic
        if debug_images[index].source != wordle_statistic.filename and debug_images[index] != pillow_image_to_src(wordle_statistic.img):
            load_debug_image(index)
        debug_images[index].set_visibility(visible)

    def load_debug_image(index):
        if index < 0 or index > 3:
            return
        img = wordle_statistic.img
        
        match(index): 
            case 0: # Detected Points
                detected_points = wordle_statistic.detected_points
                cpy = img.copy()
                draw = ImageDraw.Draw(cpy)
                point_radius = 10
                for point in detected_points:
                    shape = [point[0] - point_radius, point[1] - point_radius, point[0] + point_radius, point[1] + point_radius]
                    draw.ellipse(shape, fill='red', outline='red')
                debug_labels[index].text = f"Number of Detected Points: {len(detected_points)}"
                pass
            case 1: # Estimated Points
                estimated_points = wordle_statistic.estimated_points
                cpy = img.copy()
                draw = ImageDraw.Draw(cpy)
                point_radius = 10
                for point in estimated_points:
                    shape = [point[0] - point_radius, point[1] - point_radius, point[0] + point_radius, point[1] + point_radius]
                    draw.ellipse(shape, fill='red', outline='red')
                pass
            case 2: # Crop Image
                cpy = img.copy()
                cropbox = wordle_statistic.cropbox
                draw = ImageDraw.Draw(cpy)
                shape = [cropbox[0], cropbox[1], cropbox[2], cropbox[3]]
                draw.rectangle(shape, outline='cyan', width = 5)
                pass
            case 3:
                debug_images[index].set_source(pillow_image_to_src(wordle_statistic.text_img))
                debug_labels[index].text = f"Initial Text: {array_to_string(wordle_statistic.initial_text)}"
                return
        debug_images[index].set_source(pillow_image_to_src(cpy))
    
    def run_automation(rand=False):
        global wordle_statistic
        for debug_image in debug_images:
            debug_image.source = ""
        if rand: # Get random image from test images
            img_path = f"wordle_images/image_{random.randint(0,1424)}.jpg"
        else: # Handle input argument and get image path
            if not number_input.value:
                return ui.notify('Field not entered.', type='warning')
            try:
                int(number_input.value)
            except:
                return ui.notify('Field must be a number', type='warning')
            if int(number_input.value) < 0:
                return ui.notify('Field must be greater than 0', type='warning')
            elif int(number_input.value) > 1424:
                return ui.notify('Field must be less than 1424 (test images only go up to 1424)', type='warning')
            img_path = f"wordle_images/image_{number_input.value}.jpg"
        
        img_path_label.text = "URL: " + img_path
        wordle_image.set_source(img_path)
        wordle_statistic = reader.get_wordle_statistics_from_src(img_path)
        guesses_label.text = array_to_string(wordle_statistic.text)
        results = reader.get_data(wordle_statistic.text, wordle_statistic.color_grid)
        results_label.text = results.date_to_string()
        
        update_debug_images()
        update_data_labels(results.data_to_string())
    
    def update_debug_images():
        for i, checkbox in enumerate(debug_checkboxes):
            if checkbox.value:
                load_debug_image(i)
    
    def pillow_image_to_src(img):
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f'data:image/png;base64,{base64_image}'

    def handle_upload(e: events.UploadEventArguments):
        global wordle_statistic
        
        image_pil = Image.open(io.BytesIO(e.content.read()))
        image_src = pillow_image_to_src(image_pil)
        
        file_upload_dialog.close()
    
        try:
            wordle_statistic = reader.get_wordle_statistics_from_img(e.name, image_pil)
            results = reader.get_data(wordle_statistic.text, wordle_statistic.color_grid)
        except:
            print("ERROR")
            ui.notify("Error occurred when uploading image.", type='negative')
            return
        
        if not wordle_statistic or not results:
            ui.notify("Error occurred when uploading image.", type='negative')
            return
        ui.notify(f'Uploaded {e.name}')
        wordle_image.set_source(image_src)

        guesses_label.text = array_to_string(wordle_statistic.text)
        img_path_label.text = "URL: " + wordle_statistic.filename
        
        results_label.text = results.date_to_string()
        update_data_labels(results.data_to_string())
        update_debug_images()

ui.run()