import numpy as np
import os, cv2, time, pytesseract, io, datetime, re, math, collections, json, traceback, psutil
import  PIL
from PIL import Image, ImageEnhance
from pytesseract import Output
from pandas.core.frame import DataFrame
import pandas as pd

latest_crash = 0
iterations = 0
num_of_similar_filesizes = 0
file_size_tmp = 0

def get_location(img, target_image, more_than_one):
    result = cv2.matchTemplate(img, target_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    w = target_image.shape[1]
    h = target_image.shape[0]

    threshold = .60
    yloc, xloc = np.where(result >= threshold)

    for (x, y) in zip(xloc, yloc):
        cv2.rectangle(img, (x, y), (x + w, y + h), (0,255,255), 2)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles

def reset_game():
    global num_of_similar_filesizes

    with open('./config/crash_status.txt', 'w', errors='ignore') as f:
        f.write("TRUE")
    f.close

    time.sleep(5)

    os.system("adb -s 127.0.0.1:5565 shell input keyevent 66")
    time.sleep(2)

    os.system("adb -s 127.0.0.1:5565 shell input keyevent 66")
    time.sleep(2)

    for i in range(20):
        try:
            os.system("adb -s 127.0.0.1:5565 shell am stack remove " + str(i))
        except:
            a = 1
    time.sleep(5)

    os.system("adb -s 127.0.0.1:5565 shell am start -n com.topgamesinc.evony/com.topgamesinc.androidplugin.UnityActivity")
    time.sleep(45)

    with open('./config/crash_status.txt', 'w', errors='ignore') as f2:
        f2.write("FALSE")
    f.close

    time.sleep(5)
    num_of_similar_filesizes = 0


def check_bluestack_freeze_new():
    global filesize
    global num_of_similar_filesizes
    global iterations
    global file_size_tmp
    evony_app_page = 0

    try:
        gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
        evony_app_logo = cv2.imread('./base_images/game/bluestack_logo.png', cv2.IMREAD_UNCHANGED)
        evony_app_page = len(get_location(gameplay_img, evony_app_logo, False))
    except:
        print("Error performing image recognition")
    finally:    
        curr_time = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)
        crashed = 0

        file_size_new = 0
        filesize_diff = 0

        file_size_new = os.path.getsize('./base_images/screenshots/capture_rb_screencap.png')
        file_size_prev = file_size_tmp

        filesize_diff = abs(file_size_tmp - file_size_new)
        if(filesize_diff < 15000):
            num_of_similar_filesizes += 1
            file_size_tmp = file_size_new
        else:
            file_size_tmp = file_size_new
            num_of_similar_filesizes = 0

        print("iterations=" + str(iterations) + "," + "num_of_similar_filesizes=" + str(num_of_similar_filesizes) + ",filesize=" + "[" + "file_size_prev=" + str(file_size_prev) + "," + "file_size_new=" + str(file_size_new) + "," + "filesize_diff=" + str(filesize_diff) + "]")

        if(num_of_similar_filesizes >= 10 or evony_app_page > 0):
            crashed = 1
        else:
            crashed = 0

    return crashed


def main():
    res = check_bluestack_freeze_new()
    print("Result: " + str(res))
    if(res == 1):
        reset_game()
    else:
        print("Has not crashed - sleeping 20 seconds")
        time.sleep(20)

if __name__ == "__main__":
    while(True):
        main()
