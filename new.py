import cv2
from fer import FER
import matplotlib.pyplot as plt 

import numpy as np
import os
import requests
from decouple import config
import json
import utility
from selenium import webdriver
import time
import re
import shutil
from datetime import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
from PIL import ImageFilter 

def resize_vid():
 
    cap = cv2.VideoCapture('Face.mp4')
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi',fourcc, 5, (1280,720))
    
    while True:
        ret, frame = cap.read()
        if ret == True:
            b = cv2.resize(frame,(1280,720),fx=0,fy=0, interpolation = cv2.INTER_CUBIC)
            out.write(b)
        else:
            break
        
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def convert_vid_to_frames():
    

    vidcap = cv2.VideoCapture('output.avi')
    success,image = vidcap.read()
    count = 0
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    while success:
        try:
            if count % 100 == 0:
                cv2.imwrite(f"screengrab/frame-{count}.jpg" , image)     # save frame as JPEG file      
            success,image = vidcap.read()
        except KeyboardInterrupt:
            files_to_delete = os.listdir("screengrab")
            for file in files_to_delete:
                os.remove(f"screengrab/{file}")
            raise KeyboardInterrupt
        if count % 100 == 0:
            print(f'{length - count} frames to go')
        count += 1

def read_emotion_from_frame(image_name):
    image_path = f"screengrab/{image_name}"
    img = cv2.imread(image_path)
    detector = FER()
    name = detector.detect_emotions(img)
    return name[0] if len(name) else None

def get_best_screengrab(list_of_images):
    final_images = []
    for image in list_of_images:
        print(f"File {image} checked")
        emotion_values = read_emotion_from_frame(image)
        if emotion_values:
            if emotion_values['emotions']['surprise'] > 0.3 or emotion_values['emotions']['happy'] > 0.3:
                try:
                    final_images.append([image, emotion_values['emotions']])
                    with open("best_images.json", "w") as newFile:

                        json.dump(final_images, newFile, indent = 6)
                except:
                    print(emotion_values)
    return final_images

def get_best_images(list_of_images):
    check_file = os.path.join(os.getcwd(), "best_images.json")
    best_images_exists = os.path.exists(check_file)
    if best_images_exists:
        with open("best_images.json", 'r') as best_images_file:
            reader = best_images_file.read()
            json_data = json.loads(reader)
            best_images = [x[0] for x in json_data]
            return best_images
    files = get_best_screengrab(list_of_images)
    best_images = [x[0] for x in files]
    return best_images
    

def code_to_image(code):
    options = webdriver.ChromeOptions()
    
    # options.add_argument("--headless")
    # options.add_argument("--disable-gpu")
    initial_path = os.path.join(os.getcwd(), "code_image")
    prefs = {
            "download.default_directory": initial_path ,
            "download.prompt_for_download": False,
            # "download.directory_upgrade": True,
            # "safebrowsing.enabled": True
                    }
    options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=options)

    data  = {
        # "backgroundColor": "rgba(144, 19, 254, 100)",
        "code": f"{code}",
        "theme": "dracula",
        "exportSize": "4x",
        "language":"python"
    }

    validatedBody = utility.validateBody(data)
    carbonURL = utility.createURLString(validatedBody)

    driver.get(carbonURL)
    element = driver.find_element_by_xpath('//*/span[contains(text(), "export")]/..')
    element.click()
    time.sleep(3)
    filename = max([initial_path + "\\" + f for f in os.listdir(initial_path)],key=os.path.getctime)
    filename_for_save = f"carbon-{datetime.today().day}.png"
    shutil.move(filename,os.path.join(initial_path, filename_for_save))

def remove_bg(image_name):
    api_key = config('API_KEY')
    response = requests.post(
    'https://api.remove.bg/v1.0/removebg',
    files={'image_file': open(f"screengrab/{image_name}", 'rb')},
    data={'size': 'auto'},
    headers={'X-Api-Key': api_key},
    )
    
    if response.status_code == requests.codes.ok:
        with open(f'removed_bg/{image_name}.png', 'wb') as out:
            out.write(response.content)
    else:
        print("Error:", response.status_code, response.text)

def remove_all_files_bg(list_of_images):
    try:
        os.makedirs("removed_bg")
    except:
        pass
    removed_bg_files = os.listdir("removed_bg")
    if removed_bg_files:
        return
    for x in list_of_images:
        remove_bg(x)

def get_code():
    try:
        os.makedirs("code_image")
    except:
        pass

    code_dir = os.listdir("code_image")
    if len(code_dir):
        return
    with open("test.py", 'r') as code_file:
        reader = code_file.read()
        reader = re.sub("\n", "%250A", reader)
        code_to_image(reader)

def get_rand_location():
    pass


def combine_code_screengrab_text(text, foreground_image):
    code_dir_files = os.listdir("code_image")
    background = Image.open(f"code_image/{code_dir_files[0]}")
    foreground = Image.open(f"removed_bg/{foreground_image}")
    
    background = background.filter(ImageFilter.GaussianBlur(2))
    font_size = 200
    for index, lines in enumerate(text):
        font_size = lines['size']
        spacingTop = lines['spacingTop']
        text = lines['text']
        txt = Image.new("RGBA", background.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt)
        fnt = ImageFont.truetype("Anton-Regular.ttf", font_size)
        draw.text((300, spacingTop), text ,font=fnt, fill=(255, 255, 255, 255), stroke_width = 20, stroke_fill = (0,0,0))
        background = Image.alpha_composite(background, txt)
    foreground = foreground.resize(size=(1920, 1080))
    background.paste(foreground, (1100,400), foreground)
    background = background.resize((1280,720))
    background.save(f"{foreground_image}-combined.png")


def main():
    files_in_current_dir = os.path.exists("output.avi")
    if not files_in_current_dir:
        resize_vid()
    try:
        os.makedirs("screengrab")
    except:
        pass
    screen_grabs = os.listdir("screengrab")
    if not len(screen_grabs):
        convert_vid_to_frames()
    best_grabs = get_best_images(screen_grabs)
    remove_all_files_bg(best_grabs)
    get_code()
    removed_bg_images = os.listdir("removed_bg")

    text = [
        {"text": "Creating Youtube", "color" : (255,255,255), "spacingTop": 50, "size" : 250},
        {"text": "Thumbnails", "color" : (255,0,0), "spacingTop": 300, "size" : 370},
        {"text": "Automatically", "color" : (255,255,255), "spacingTop": 750, "size" : 250}
    ]
    for image in removed_bg_images:
        combine_code_screengrab_text(text, image)

    

if __name__ == '__main__':
    main()