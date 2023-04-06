import numpy as np
import os, cv2, time, pytesseract, io, datetime, re
from PIL import Image, ImageEnhance
import sys

connection_string = '127.0.0.1:' + sys.argv[1]
starting_x = sys.argv[2]
starting_y = sys.argv[3]
agent_id = sys.argv[4]

input_filename = "capture_monster_hunter_" + agent_id + ".png"

def take_screenshot():
    os.system('adb -s ' + connection_string + ' shell screencap -p /sdcard/' + "capture_monster_hunter.png")
    os.system('adb -s ' + connection_string + ' pull /sdcard/capture_monster_hunter.png ./base_images/screenshots/' + input_filename)

def click_location_on_screen(x, y):
    os.system('adb -s ' + connection_string + ' shell input tap ' + str(x) + ' ' + str(y))  

def click_coordinate_search():
    os.system('adb -s ' + connection_string + ' shell input tap 453 1415')

def execute_key_process(key, num_of_it):
    for i in range(num_of_it):
        os.system('adb -s ' + connection_string + ' shell input keyevent ' + key)

def execute_text_input_process(text):
    os.system('adb -s ' + connection_string + ' shell input text ' + text)


def get_location(img, target_image, target_name):
    result = cv2.matchTemplate(img, target_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    w = target_image.shape[1]
    h = target_image.shape[0]

    threshold = .65
    yloc, xloc = np.where(result >= threshold)

    for (x, y) in zip(xloc, yloc):
        cv2.rectangle(img, (x, y), (x + w, y + h), (0,255,255), 2)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles


def get_location_2():

    gameplay_img = cv2.imread('./base_images/screenshots/' + input_filename, cv2.IMREAD_UNCHANGED)
    target_img = cv2.imread("./base_images/game/share_button.png", cv2.IMREAD_UNCHANGED)

    result = cv2.matchTemplate(gameplay_img, target_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    w = target_img.shape[1]
    h = target_img.shape[0]

    threshold = .55
    yloc, xloc = np.where(result >= threshold)

    for (x, y) in zip(xloc, yloc):
        cv2.rectangle(gameplay_img, (x, y), (x + w, y + h), (0,255,255), 2)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles


def get_location_3(img, target_image, more_than_one):
    result = cv2.matchTemplate(img, target_image, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    w = target_image.shape[1]
    h = target_image.shape[0]

    threshold = .70
    yloc, xloc = np.where(result >= threshold)

    for (x, y) in zip(xloc, yloc):
        cv2.rectangle(img, (x, y), (x + w, y + h), (0,255,255), 2)

    rectangles = []
    for (x, y) in zip(xloc, yloc):
        rectangles.append([int(x), int(y), int(w), int(h)])

    rectangles, weights = cv2.groupRectangles(rectangles, 1, 0.2)
    return rectangles


def go_to_specified_coordinates(x, y):
    click_coordinate_search()
    time.sleep(0.1)
    click_location_on_screen(300, 850)
    execute_key_process("KEYCODE_DEL", 4)
    time.sleep(0.1)
    execute_text_input_process(x)
    time.sleep(0.1)
    click_location_on_screen(650, 850)
    click_location_on_screen(650, 850)
    execute_key_process("KEYCODE_DEL", 4)
    time.sleep(0.5)
    execute_text_input_process(y)
    click_location_on_screen(450, 1000)
    click_location_on_screen(450, 1000)
    time.sleep(2)

# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def detect_text_local():
    img = cv2.imread("./base_images/screenshots/" + input_filename, cv2.IMREAD_UNCHANGED)
    gray = get_grayscale(img)
    thresh = thresholding(gray)
    return pytesseract.image_to_string(thresh)


def check_for_issues(y_axis):
    take_screenshot()
    gameplay_img = cv2.imread('./base_images/screenshots/' + input_filename, cv2.IMREAD_UNCHANGED)
    evony_app_logo = cv2.imread('./base_images/game/go_back_button.png', cv2.IMREAD_UNCHANGED)
    evony_app_page = len(get_location_3(gameplay_img, evony_app_logo, False))

    if(evony_app_page > 0):
        click_location_on_screen(70,75)
        time.sleep(2)
        os.system('adb -s ' + connection_string + y_axis)
        time.sleep(2)

    take_screenshot()
    gameplay_img = cv2.imread('./base_images/screenshots/' + input_filename, cv2.IMREAD_UNCHANGED)
    double_down_button_purchase_img = cv2.imread('./base_images/game/red_cross_button.png', cv2.IMREAD_UNCHANGED)
    double_down_page = len(get_location_3(gameplay_img, double_down_button_purchase_img, False))

    if(double_down_page > 0):
        click_location_on_screen(1008,345)
        time.sleep(2)
        os.system('adb -s ' + connection_string + y_axis)
        time.sleep(2)


    take_screenshot()
    gameplay_img = cv2.imread('./base_images/screenshots/' + input_filename, cv2.IMREAD_UNCHANGED)
    go_back_small_button = cv2.imread('./base_images/game/go_back_small_button.png', cv2.IMREAD_UNCHANGED)
    go_back_small_button_bool = len(get_location_3(gameplay_img, go_back_small_button, False))

    if(go_back_small_button_bool > 0):
        click_location_on_screen(34,41)
        time.sleep(2)
        os.system('adb -s ' + connection_string + y_axis)
        time.sleep(2)


def hunt_monster_2(direction):
    bosses = ['Behemoth.png','Golden_Goblin.png','Hydra.png','Cerberus.png','Kamaitachi.png','Witch.png','Ymirs.png','Knight_Bayard.png','Fafnir.png']
    bosses_names = ['Behemoth','Golden Goblin','Hydra','Cerberus','Kamaitachi','Witch','Ymirs','Knight Bayard','Fafnir']
    bosses_names_abbrev = ['Behemoth','Golden Goblin','Hydra','Cerberus','Kamaitachi','Witch','Ymirs','Knight Bayard','Fafnir']

    jiggle = ' shell input swipe 430 900 430 850'

    if(direction == 0):
        x_axis = ' shell input swipe 430 900 430 300'
        y_axis = ' shell input swipe 800 800 200 800'
    else:
        x_axis = ' shell input swipe 430 900 430 300'
        y_axis = ' shell input swipe 200 800 800 800'

    time.sleep(2)
    for i in range(50):
        try:
            time.sleep(2)
            take_screenshot()
            for boss,bnames,bnames_abbrev in zip(bosses,bosses_names,bosses_names_abbrev):

                gameplay_img = cv2.imread('./base_images/screenshots/' + input_filename, cv2.IMREAD_UNCHANGED)
                boss_img = cv2.imread('./base_images/bosses/' + boss, cv2.IMREAD_UNCHANGED)
                num_monster_found = get_location(gameplay_img, boss_img, bnames)
                print("Searching for " + bnames + " - Found: " + str(num_monster_found))

                if(len(num_monster_found) > 0):
                    x_loc = num_monster_found[0][0] + round(num_monster_found[0][2]/2)
                    y_loc = num_monster_found[0][1] + round(num_monster_found[0][3]/2)
                    print("Found: " + bnames + " | " + "X="+str(x_loc) + ",Y="+str(y_loc))

                    click_location_on_screen(x_loc, y_loc)
                    time.sleep(1)
                    take_screenshot()
                    attack_loc = get_location_2()
                    x_loc = attack_loc[0][0] + round(attack_loc[0][2])
                    y_loc = attack_loc[0][1] + round(attack_loc[0][3]/2)
                    click_location_on_screen(x_loc, y_loc)
                    time.sleep(0.25)
                    click_location_on_screen(450, 750)
                    time.sleep(0.25)
                    click_location_on_screen(600, 950)
                    time.sleep(0.5)
            i = i+1
            os.system('adb -s ' + connection_string + y_axis)
            time.sleep(1)
        except Exception as e:
            i = i+1
            os.system('adb -s ' + connection_string + y_axis)
            time.sleep(1)
            
    os.system('adb -s ' + connection_string + y_axis)
    time.sleep(1)
    os.system('adb -s ' + connection_string + x_axis)

def main():
    go_to_specified_coordinates(starting_x, starting_y)
    for i in range(100):
        if(i % 2 == 0):
            hunt_monster_2(0)
        else:
            hunt_monster_2(1)

if __name__ == "__main__":
    while(True):
        main()