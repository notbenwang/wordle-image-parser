import cv2
import pytesseract
from PIL import Image, ImageOps
from matplotlib import pyplot as plt
import difflib
import numpy as np
import math
from wordle_config import Config
from datetime import datetime, timedelta

# Prep Possible Word Bank
CONFIG = Config()

def auto_correct(word, closest=1):
        closest_word = difflib.get_close_matches(word.lower(), CONFIG.word_bank, n=closest, cutoff=0.6)
        if closest_word:
            return closest_word[closest-1].upper()
        else:
            return "-----"

def filename_to_image(filename):
    return Image.open(filename)

def image_to_text(img, threshold_value=200, display_image=False, crop = None):
    if crop:
        img = img.crop(crop)
    img_gray = ImageOps.grayscale(img)
    img_binary = img_gray.point(lambda p: p > threshold_value and 255)
    text = pytesseract.image_to_string(img_binary, config='--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    initial_text = text.split()
    text = text.split()
    for i,word in enumerate(text):
        if word.lower() not in CONFIG.word_bank:
            text[i] = auto_correct(word)
    if display_image:
        plt.imshow(img_binary)
        plt.show()
    return initial_text, text, img_binary

def get_box_points(img, display_image = False):
    # METHOD: Converts filename to image, then "detects" all square boxes
    # RETURNS: point coords, bounding "boxes" of points, image cropped coordinates best fit to the points

    # Convert image to cv2 and apply filters
    img_gray = ImageOps.grayscale(img)
    threshold_value = 20
    img_binary = img_gray.point(lambda p: p > threshold_value and 255)
    numpy_img = np.array(img_binary)
    cv2_img = cv2.cvtColor(numpy_img, cv2.COLOR_RGB2BGR)
    gray_cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    _, thresh_cv2_img = cv2.threshold(gray_cv2_img, 127, 255, cv2.THRESH_BINARY)

    # find contours (cv2 detecting possible shapes)
    contours, _ = cv2.findContours(thresh_cv2_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    points = []
    point_approxs = []
    
    # Analyze contours
    i = 0
    for contour in contours:
        if i == 0: # Ignore the bounding box
            i = 1
            continue
        i += 1
        # Approximate the shape
        approx = cv2.approxPolyDP( 
            contour, 0.01 * cv2.arcLength(contour, True), True) 
        # Check if quadrilateral
        if len(approx) == 4: 
            # Check if square
            side_lengths = []
            for i in range(4):
                pt1 = approx[i][0]
                pt2 = approx[(i + 1) % 4][0]
                side_length = np.linalg.norm(pt1 - pt2)
                side_lengths.append(side_length)
            tolerance = 0.1
            # if approximately all sides equal (ie if square)
            if all(abs(side_lengths[i] - side_lengths[(i + 1) % 4]) < tolerance * min(side_lengths) for i in range(4)):
                # Find center of shape
                M = cv2.moments(contour) 
                if M['m00'] != 0.0: 
                    x = int(M['m10']/M['m00']) 
                    y = int(M['m01']/M['m00']) 
                    if (x,y) not in points:
                        points.append((x,y)) # Add point if not already there
                        point_approxs.append(approx)
                        if display_image:
                            cv2.circle(cv2_img, (x,y), radius=10, color=(255, 0, 0), thickness=2)
    
    cropped_coords = get_crop_coords(points)
    
    if display_image:
        plt.imshow(cv2_img)
        plt.show()
    return points, point_approxs, cropped_coords

def get_crop_coords(points, average_width=None):
    min_dist = 10000000000000000
    top_left = None
    max_dist = -1
    bottom_right = None
    for point in points:
        dist = math.sqrt(point[0]**2 + point[1]**2)
        if dist < min_dist:
            min_dist = dist
            top_left = point
        if dist > max_dist:
            bottom_right = point
            max_dist = dist
    if average_width:
        padding = int(average_width/2)
    else:
        padding = min(top_left[0],top_left[1])
    cropped_coords = (top_left[0]-padding, top_left[1]-padding, bottom_right[0]+padding, bottom_right[1] + padding) # left, upper, right, lower
    return cropped_coords

def knn(x,y,width,img):
    # go to top right of box
    x = round(x-width/2)
    y = round(y-width/2)
    colors = {}
    # iterate around the box and classify
    for dx in range(width):
        for dy in range(width):
            point_x = x + dx
            point_y = y + dy
            color = img[point_y][point_x]
            color = (color[0], color[1], color[2])
            if color not in colors:
                colors[color] = 1
            else:
                colors[color] += 1
    # return the closest neighbor
    return max(colors,key=colors.get)

def get_box_colors(img, points=None, average_width=25, display_image = False):
    if not points:
        points, point_approxs, _ = get_box_points(img)
        average_width = get_average_width(point_approxs)
        if len(points) != 30:
            points = correct_box_points(points)

    # Get image and convert to pixel data
    rgb_img = img.convert('RGB')
    pixel_data = np.array(rgb_img)

    # run knn on each point
    colors = []
    color_count = {}
    for i, point in enumerate(points):
        color = knn(point[0], point[1], average_width, pixel_data)
        colors.append(color)
        if color not in color_count:
            color_count[color] = 1
        else:
            color_count[color] += 1
    
    if display_image:
        plt.imshow(img)
        plt.show()
    return colors, color_count

def get_average_width(point_approxs):
    average_width = 0
    for approx in point_approxs:
        side_length_sum = 0
        for i in range(4):
            pt1 = approx[i][0]
            pt2 = approx[(i + 1) % 4][0]
            side_length = np.linalg.norm(pt1 - pt2)
            side_length_sum += side_length
        side_length_average = side_length_sum / 4
        average_width += side_length_average
    average_width = round( average_width / (len(point_approxs)) )
    return average_width

def array_of_keys_to_dict(arr):
    dict = {}
    for item in arr:
        if item not in dict:
            dict[item] = 0 
    return dict

def correct_box_points(points):
    sorted_points = sorted(points, key=lambda point: (point[0], point[1]))
    if len(sorted_points) == 30:
        return sorted_points
    else:        
        columns = get_column_values(sorted_points)
        rows = get_row_values(sorted_points)
        
        if len(sorted_points) > 30:
            column_dict = array_of_keys_to_dict(columns)
            row_dict = array_of_keys_to_dict(rows)
            for point in sorted_points:
                x, y = point[0], point[1]
                diff_columns = [abs(x - key) for key in columns]
                diff_rows = [abs(y - key) for key in rows]
                closest_column = columns[diff_columns.index(min(diff_columns))]
                closest_row = rows[diff_rows.index(min(diff_rows))]
                column_dict[closest_column] += 1
                row_dict[closest_row] += 1
            sorted_column_dict = sorted(column_dict.items(), key=lambda item: item[1], reverse=True)
            columns = [item[0] for item in sorted_column_dict[:5]]
            sorted_row_dict = sorted(row_dict.items(), key=lambda item: item[1], reverse=True)
            rows = [item[0] for item in sorted_row_dict[:6]]
        
        estimated_points = []
        for i in range(len(rows)):
            for j in range(len(columns)):
                estimated_points.append((columns[j],rows[i]))
        return sorted(estimated_points, key=lambda point: (point[0], point[1]))

def get_column_values(points, threshold=5):
    columns = []
    threshold = 5
    for point in points:
        col_index = len(columns) - 1
        point_x = point[0]
        if col_index == -1:
            columns.append(point_x)
        else:
            if point_x - columns[col_index] > threshold or point_x - columns[col_index] < -threshold:
                columns.append(point_x)
    return columns

def get_row_values(points, threshold=5):
    rows = []
    threshold = 5
    for point in points:
        point_y = point[1]
        if closest_y(point_y, rows, threshold) == -1:
            rows.append(point_y)
    return rows

def closest_y(y, ys, threshold):
    for i, yi in enumerate(ys):
        if y - yi < threshold and y - yi > -threshold:
            return i
    return -1

def translate_color_count(rgb_colors):
    YELLOW = (177, 161, 76)
    GREEN = (96, 139, 85)
    BLACK = (18, 18, 18)
    GRAY = (58, 58, 60)
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (181,181,181)
    COLOR_MAP = {(177, 161, 76):"yellow", (96, 139, 85):"green", (18, 18, 18):"black", (58, 58, 60):"gray", (255, 255, 255):"white", (181, 181, 181):"gray"}
    results = {}
    COLORS = [BLACK, GRAY, YELLOW, GREEN, WHITE, LIGHT_GRAY]
    for rgb in list(rgb_colors.keys()):
        value = rgb_colors[rgb]
        min_dist = 10000000000000000000
        rgb_color = BLACK
        for COLOR in COLORS:
            dist = math.sqrt((rgb[0]-COLOR[0])**2 + (rgb[1]-COLOR[1])**2 + (rgb[2]-COLOR[2])**2)
            if dist < min_dist:
                min_dist = dist
                rgb_color = COLOR
        color = COLOR_MAP[rgb_color]
        if color not in results:
            results[color] = value
        else:
            results[color] += value
    return results

def translate_colors(rgb_colors, display_matrix=False):
    YELLOW = (177, 161, 76)
    GREEN = (96, 139, 85)
    BLACK = (18, 18, 18)
    GRAY = (58, 58, 60)
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (181,181,181)
    COLORS = [BLACK, GRAY, YELLOW, GREEN, WHITE, LIGHT_GRAY]
    COLOR_MAP = {(177, 161, 76):"yellow", (96, 139, 85):"green", (18, 18, 18):"black", (58, 58, 60):"gray", (255, 255, 255):"white", (181, 181, 181):"gray"}
    grid = []
    for rgb in rgb_colors:
        min_dist = 10000000000000000000
        rgb_color = BLACK
        for COLOR in COLORS:
            dist = math.sqrt((rgb[0]-COLOR[0])**2 + (rgb[1]-COLOR[1])**2 + (rgb[2]-COLOR[2])**2)
            if dist < min_dist:
                min_dist = dist
                rgb_color = COLOR
        color = COLOR_MAP[rgb_color]
        grid.append(color)
    
    number_of_rows = int(len(rgb_colors) / 5)
    matr = [[0] * 5 for _ in range(number_of_rows)]
    for j in range(5):
        for i in range(number_of_rows):
            matr[i][j] = grid[j*number_of_rows + i]
    
    if display_matrix:
        for line in matr:
            print(line)
    return matr

from colorama import Fore

def print_color_result(words, colors):
    # FOR TESTING IN THIS FILE
    DICT = {"yellow":Fore.YELLOW, "green":Fore.GREEN, "gray":Fore.LIGHTBLACK_EX, "black":Fore.BLACK, "white":Fore.WHITE}
    for j,word in enumerate(words):
        for i,letter in enumerate(word):
            color = DICT[colors[j][i]]
            print(color + letter,end="")
        print()
    if len(words) < 6:
        diff = 6 - len(words)
        for i in range(diff):
            print(Fore.BLACK + "XXXXX")
    print(Fore.RESET)
def print_results(text, color_grid):
    # FOR TESTING IN THIS FILE
    loss = False
    if len(text) < 6:
        score = len(text)
    elif len(text) == 6:
        score = 7 if "gray" in color_grid[-1] else 6
    if score == 7:
        print("It seems like you lost. Sorry.")
        loss = True
    if loss:
        answer = ""
        while (len(answer) != 5):
            answer = input("What was the solution for this wordle? ").upper()
    else:
        answer = text[-1]
    
    wordle_num = CONFIG.db.getNumber(answer)
    
    if wordle_num == -1:
        print(f"This answer, {answer}, could not be found in the database.")
        return -1
    info = CONFIG.db.getInfo(wordle_num)
    
    if int(wordle_num) > 626:
        print(f"Wordle: {info['num']}, Date: {info['date']}")
        print(f"You scored a {score} for this wordle.")
        if loss:
            print(f"It looks like around {100-info['cumulative'][-1]}% of people also lost this Wordle. That sucks!")
        else:
            if (score > 1):
                print(f"This places you in the top {info['cumulative'][score-2]}-{info['cumulative'][score-1]}% (sample size: {info['sample']})")
            else:
                print(f"This places you in the top 0-{info['cumulative'][score-1]}% (sample size: {info['sample']})")
        print(f"Distribution of Wordle {info['num']} is {info['individual']}")
        index = info['individual'].index(max(info['individual']))
        print(f"{info['individual'][index]}% of people guessed this wordle in {index + 1} guesses")
    else:
        print(f"No distribution data for {answer}, as it was before Wordle 626.")
        print(f"Wordle: {wordle_num}, Date: {info['date']}")  
    return 

def determine_score(text, color_grid):
    if len(text) < 6:
        return len(text)
    if len(text) > 6:
        return -1
    if "gray" not in color_grid[-1]:
        return 6
    return 7
    

class WordleStatistic():
    def __init__(self, filename, img, detected_points, estimated_points, avg_width, cropbox, text, color_grid, text_img, initial_text) -> None:
        self.filename = filename
        self.img = img
        self.detected_points = detected_points
        self.estimated_points = estimated_points
        self.avg_width = avg_width
        self.cropbox = cropbox
        self.text = text
        self.color_grid = color_grid
        self.text_img = text_img
        self.initial_text = initial_text
class Result():
    def __init__(self, outcome, score, answer, text, puzzle_number, puzzle_data):
        self.outcome = outcome
        self.score = score
        self.answer = answer
        self.guesses = text
        self.puzzle_number = puzzle_number
        self.puzzle_data = puzzle_data

    def data_to_string(self):
        date_str = '2021-06-19'
        date = datetime.strptime(date_str, '%Y-%m-%d')
        new_date = date + timedelta(int(self.puzzle_number))
        return f"Wordle: {self.puzzle_number}, Date: {new_date.date()}"
        

class ImageTool():
    def __init__(self) -> None:
        self.config = Config()    
    
    def get_wordle_statistics_from_src(self, filename) -> WordleStatistic:
        img = filename_to_image(filename)
        return self.get_wordle_statistics_from_img(filename, img)
    
    def get_wordle_statistics_from_img(self, filename, img) -> WordleStatistic:
        points, point_approxs, _ = get_box_points(img)
        average_width = get_average_width(point_approxs)
        estimated_points = correct_box_points(points)
        cropbox = get_crop_coords(estimated_points)
        initial_text, text, text_img = image_to_text(img, crop=cropbox)
        colors, color_count = get_box_colors(img, points=estimated_points, average_width=average_width, display_image=False)
        color_grid = translate_colors(colors, display_matrix=False)
        return WordleStatistic(filename, img, points, estimated_points, average_width, cropbox, text, color_grid, text_img, initial_text)

    def get_data(self, text, color_grid) -> Result:
        score = determine_score(text, color_grid)
        if score == -1:
            return None
        if score == 7:
            return False
        answer = text[-1]
        wordle_num = self.config.db.getNumber(answer)
        info = self.config.db.getInfo(wordle_num)
        return Result(True, score, answer, text, wordle_num, info)

if __name__ == "__main__":

    while (True):
        num = input("Insert File: ")
        filename = f"wordle_images/image_{num}.jpg"
        points, point_approxs, _ = get_box_points(filename)
        average_width = get_average_width(point_approxs)
        estimated_points = correct_box_points(points)

        cropbox = get_crop_coords(estimated_points)
        _, text, _ = image_to_text(filename, display_image=False, crop=cropbox)
        colors, color_count = get_box_colors(filename, points=estimated_points, average_width=average_width, display_image=False)
        color_grid = translate_colors(colors, display_matrix=False)

        print(f"Detected boxes: {len(points)}")
        print_color_result(text, color_grid)
        color_count = translate_color_count(color_count)
        print_results(text, color_grid)
