import numpy as np
import os, cv2, time, pytesseract, io, datetime, re, math, collections, json, traceback, psutil, mysql.connector
import  PIL
from PIL import Image, ImageEnhance
from pytesseract import Output
from pandas.core.frame import DataFrame
import pandas as pd
from datetime import datetime

connection_ip = '127.0.0.1'
connection_port = "5565"
connection_string = connection_ip + ":" + connection_port
latest_crash = "FALSE"


def check_boss_exists(date, x, y, boss_name, status):
    cnx = mysql.connector.connect(user=os.environ["MY_SQL_USERNAME"], password=os.environ["MY_SQL_PWD"], host='192.168.68.101', database='evony', auth_plugin='mysql_native_password')

    if(status == 'null'):
        query = "SELECT * FROM rb_bosses_queue WHERE date_added = %s AND x = %s AND y = %s AND name = %s"
        params = (date, x, y, boss_name)
    else:
        query = "SELECT * FROM rb_bosses_queue WHERE date_added = %s AND x = %s AND y = %s AND name = %s AND status = %s"
        params = (date, x, y, boss_name, status)

    cursor = cnx.cursor()
    cursor.execute(query, params)
    df = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
    cnx.close()
    if len(df) > 0:
        return df.loc[0,['status']]
    else:
        return 'NULL'

    
def insert_into_rb_boss_queue(distance, x, y, name, status, priority, hit_boss, roland, outcome, lost_power, self_initiated_aw, boss_level, type, slot_used, general_used):
        cnx = mysql.connector.connect(user=os.environ["MY_SQL_USERNAME"], password=os.environ["MY_SQL_PWD"], host='192.168.68.101', database='evony', auth_plugin='mysql_native_password')
        date_added = datetime.now().strftime("%Y-%m-%d")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = "INSERT INTO rb_bosses_queue VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (date_added, distance, x, y, name, status, priority, hit_boss, roland, current_datetime, current_datetime, outcome, lost_power, self_initiated_aw, boss_level, type, slot_used, general_used)

        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()
        cnx.close()


def update_boss_data(field, value, date, x, y, boss_name):
        cnx = mysql.connector.connect(user=os.environ["MY_SQL_USERNAME"], password=os.environ["MY_SQL_PWD"], host='192.168.68.101', database='evony', auth_plugin='mysql_native_password')
        query = "UPDATE rb_bosses_queue SET " + field + " = %s WHERE date_added = %s AND x = %s AND y = %s AND name = %s"
        params = (value, date, x, y, boss_name)
        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()
        cnx.close()


def update_all_disappeared_bosses(period=1, field="status",value="Alive"):
        cnx = mysql.connector.connect(user=os.environ["MY_SQL_USERNAME"], password=os.environ["MY_SQL_PWD"], host='192.168.68.101', database='evony', auth_plugin='mysql_native_password')
        query = "UPDATE rb_bosses_queue SET " + field + " = %s WHERE modified >= NOW() - INTERVAL %s HOUR and status = 'Disappeared'"
        params = (value, period)
        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()
        cnx.close()


def get_all_hitable_bosses_based_off_status(status, hit=1):
    cnx = mysql.connector.connect(user=os.environ["MY_SQL_USERNAME"], password=os.environ["MY_SQL_PWD"], host='192.168.68.101', database='evony', auth_plugin='mysql_native_password')
    query = "SELECT * FROM rb_bosses_queue WHERE status = %s and hit = %s order by priority asc, distance asc"
    params = (status, hit)

    cursor = cnx.cursor()
    cursor.execute(query, params)
    df = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
    cnx.close()
    return df


def detect_fix_evony_object_name(name):
    boss_list = pd.read_csv("./config/bosses.csv")
    bosses_names = boss_list['boss_name'].tolist()
    name = re.sub("^.+Lv","Lv",name)

    for boss in bosses_names:

        boss_array = boss.lower().split()
        words_found = 0
        
        for word in boss_array:
            if word.strip() in name.lower().strip():
                words_found = words_found + 1
        
        if words_found == len(boss_array):
            return boss

    return name


def take_screenshot_enhanced(loc, image_name):
    os.system('adb -s ' + connection_string + ' shell screencap -p /sdcard/' + image_name + '.png')
    os.system('adb -s ' + connection_string + ' pull /sdcard/' + image_name + '.png ' + loc + image_name + '.png')


def detect_text_local(img):
    try:
        img = cv2.imread("./base_images/screenshots/" + img + ".png", cv2.IMREAD_UNCHANGED)
        gray = get_grayscale(img)
        thresh = thresholding(gray)
        return pytesseract.image_to_string(thresh)
    except:
        traceback.print_exc()
        return "NULL"
    

def check_if_evony_has_crashed():

    crashed = "FALSE"
    evony_app_page = 0

    try:
        gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
        evony_app_logo = cv2.imread('./base_images/game/bluestack_logo.png', cv2.IMREAD_UNCHANGED)
        evony_app_page = len(get_location(gameplay_img, evony_app_logo, False))
    except:
        crashed = "FALSE"

    with open('./config/crash_status.txt', 'r', errors='ignore') as f:
        crashed = f.readlines()[0]

    if(evony_app_page > 0):
        crashed = "TRUE"
    
    return crashed


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

def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

def click_location_on_screen(x, y):
    os.system('adb -s ' + connection_string + ' shell input tap ' + str(x) + ' ' + str(y))

def click_coordinate_search():
    os.system('adb -s ' + connection_string + ' shell input tap 560 1690')

def execute_key_process(key, num_of_it):
    for i in range(num_of_it):
        os.system('adb -s ' + connection_string + ' shell input keyevent ' + key)

def execute_text_input_process(text):
    os.system('adb -s ' + connection_string + ' shell input text ' + str(text))


def go_to_specified_coordinates(x, y):
    click_coordinate_search()
    time.sleep(0.1)
    click_location_on_screen(375, 1040)
    execute_key_process("KEYCODE_DEL", 4)
    time.sleep(0.1)
    execute_text_input_process(x)
    time.sleep(0.1)
    click_location_on_screen(800, 1050)
    click_location_on_screen(800, 1050)
    execute_key_process("KEYCODE_DEL", 4)
    time.sleep(0.1)
    execute_text_input_process(y)
    click_location_on_screen(550, 1200)
    click_location_on_screen(550, 1200)
    time.sleep(2)


def on_main_page_check():
    time.sleep(1)
    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    main_page_check = cv2.imread('./base_images/game/main_page_check.png', cv2.IMREAD_UNCHANGED)
    main_page = len(get_location(gameplay_img, main_page_check, False))
    return main_page


def perform_game_reset_seq():
    time.sleep(2)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    evony_app_logo = cv2.imread('./base_images/game/bluestack_logo.png', cv2.IMREAD_UNCHANGED)
    evony_app_page = len(get_location(gameplay_img, evony_app_logo, False))

    if(evony_app_page > 0):
        click_location_on_screen(1717,181)
        time.sleep(5)

    time.sleep(5)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    double_down_button_purchase_img = cv2.imread('./base_images/game/double_down_button_purchase.png', cv2.IMREAD_UNCHANGED)
    double_down_page = len(get_location(gameplay_img, double_down_button_purchase_img, False))

    if(double_down_page > 0):
        click_location_on_screen(954,432)
        time.sleep(5)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    purchase_page_check = cv2.imread('./base_images/game/cross_button_purchase.png', cv2.IMREAD_UNCHANGED)
    purchase_page = len(get_location(gameplay_img, purchase_page_check, False))

    if(purchase_page > 0):
        click_location_on_screen(1030, 51)
        time.sleep(1)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    castle_page_check = cv2.imread('./base_images/game/world_button.png', cv2.IMREAD_UNCHANGED)
    castle_page = len(get_location(gameplay_img, castle_page_check, False))

    if(castle_page > 0):
        click_location_on_screen(985, 1820)
        time.sleep(3)

    click_location_on_screen(500, 1830)
    time.sleep(0.5)
    click_location_on_screen(670, 120)
    time.sleep(0.5)
    click_location_on_screen(41, 41)
    time.sleep(2)
    update_all_disappeared_bosses()


def check_evony_status():
    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    purchase_page_check = cv2.imread('./base_images/game/bluestack_error_freeze_msg.png', cv2.IMREAD_UNCHANGED)
    purchase_page = len(get_location(gameplay_img, purchase_page_check, False))

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    purchase_page_check_2 = cv2.imread('./base_images/game/evony_logo_app_memu.png', cv2.IMREAD_UNCHANGED)
    purchase_page_2 = len(get_location(gameplay_img, purchase_page_check_2, False))

    if(purchase_page > 0):
        return 1
    elif(purchase_page_2 > 0):
        return 2
    else:
        return 0


def check_if_reset_occurred():
    time.sleep(1)
    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    purchase_page_check = cv2.imread('./base_images/game/cross_button_purchase.png', cv2.IMREAD_UNCHANGED)
    purchase_page = len(get_location(gameplay_img, purchase_page_check, False))

    time.sleep(1)
    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    castle_page_check = cv2.imread('./base_images/game/world_button.png', cv2.IMREAD_UNCHANGED)
    castle_page = len(get_location(gameplay_img, castle_page_check, False))

    purchase_page = purchase_page + castle_page
    return purchase_page


def attack_monster(present, alliance_war):
        global monster_escape
        x = -1
        cmd = "adb -s " + connection_string + " shell input tap " + str(520) + " " + str(920)
        os.system(cmd)
        time.sleep(2)
        
        cmd = "adb -s " + connection_string + " shell input tap " + str(275) + " " + str(775)
        os.system(cmd)
        time.sleep(2)
        try:
            take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
            time.sleep(1)

            image_match_file = ''
            if(alliance_war == 1):
                image_match_file = './base_images/game/alliance_war_button.png'
            else:
                image_match_file = './base_images/game/non_alliance_war_button.png'

            gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
            target_img = cv2.imread(image_match_file, cv2.IMREAD_UNCHANGED)
            w = target_img.shape[1]
            h = target_img.shape[0]
            rec = get_location(gameplay_img, target_img, 1)
            
            #Click the attack button on the battle monster screen.
            cmd = "adb -s " + connection_string + " shell input tap " + str(rec[0][0]+rec[0][2]/2) + " " + str(rec[0][1]+rec[0][3]/2)
            os.system(cmd)
            time.sleep(0.5)
            cmd = "adb -s " + connection_string + " shell input tap " + str(345) + " " + str(1000)
            os.system(cmd)

            time.sleep(1)
            if(present == 5):
                cmd = "adb -s " + connection_string + " shell input tap " + str(595) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
            elif(present == 4):
                cmd = "adb -s " + connection_string + " shell input tap " + str(467) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
            elif(present == 1):
                cmd = "adb -s " + connection_string + " shell input tap " + str(100) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
                cmd = "adb -s " + connection_string + " shell input tap " + str(100) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
            elif(present == 2):
                cmd = "adb -s " + connection_string + " shell input tap " + str(225) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
                cmd = "adb -s " + connection_string + " shell input tap " + str(225) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
            elif(present == 3):
                cmd = "adb -s " + connection_string + " shell input tap " + str(345) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
                cmd = "adb -s " + connection_string + " shell input tap " + str(345) + " " + str(215)
                os.system(cmd)
                time.sleep(1)
                
            x = 100
            time.sleep(1)
            cmd = "adb -s " + connection_string + " shell input tap " + str(800) + " " + str(1850)
            os.system(cmd)
        except:
            print("Monster has escaped!")
            monster_escape = 1
            x == -1
        finally:
            x == -1
        return x


def initiate_rally(target, general_no, general_name):
    print("Currently killing: " + target["name"] + " at location " + str(target["x"]) + " " + str(target["y"]) + " as a distance of " + str(target["distance"]) + "KM")
    go_to_specified_coordinates(target["x"], target["y"])
    time.sleep(2)
    sleep_counter = attack_monster(general_no, int(target["alliance_war"]))

    if(sleep_counter != -1):
        update_boss_data("status", "Dead", target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("slot_used", str(general_no), target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("general_used", general_name, target["date_added"], int(target["x"]), int(target["y"]), target["name"])
    else:
        update_boss_data("status", "Disappeared", target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("slot_used", str(general_no), target["date_added"], int(target["x"]), int(target["y"]), target["name"])
        update_boss_data("general_used", general_name, target["date_added"], int(target["x"]), int(target["y"]), target["name"])
    return sleep_counter


def determine_if_slot_is_open(slot_num):
    time.sleep(2)
    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    roland_img = cv2.imread('./base_images/generals/roland_rally_pic.png', cv2.IMREAD_UNCHANGED)
    theo_img = cv2.imread('./base_images/generals/theo_rally_pic.png', cv2.IMREAD_UNCHANGED)
    scorpio_img = cv2.imread('./base_images/generals/scropio_rally_pic.png', cv2.IMREAD_UNCHANGED)
    simone_img = cv2.imread('./base_images/generals/simone_rally_pic.png', cv2.IMREAD_UNCHANGED)
    no_general_img = cv2.imread('./base_images/generals/marching_blank_general.png', cv2.IMREAD_UNCHANGED)
    aethelflaed_img = cv2.imread('./base_images/generals/aethelflaed_rally_pic.png', cv2.IMREAD_UNCHANGED)

    res = 0

    if(slot_num == 1): res = len(get_location(gameplay_img, theo_img, False))
    elif(slot_num == 2): res = len(get_location(gameplay_img, scorpio_img, False))
    elif(slot_num == 3): res = len(get_location(gameplay_img, simone_img, False))
    elif(slot_num == 4): res = len(get_location(gameplay_img, roland_img, False))
    elif(slot_num == 5): res = len(get_location(gameplay_img, aethelflaed_img, False))

    return int(res)


def hit_boss(slot):
    boss_list = pd.read_csv("./config/bosses.csv")
    boss_df = get_all_hitable_bosses_based_off_status('Alive')
    boss_df = pd.merge(boss_df, boss_list, how="left", left_on="name", right_on="boss_name")

    boss_df_primary = boss_df.query("`{0}` == 1".format("slot_" + str(slot) + "_primary")).reset_index()
    boss_df_secondary = boss_df.query("`{0}` == 1".format("slot_" + str(slot) + "_secondary")).reset_index()

    if(len(boss_df_primary) == 0):
        boss_to_hit = boss_df_secondary.iloc[0,:]
    else:
        boss_to_hit = boss_df_primary.iloc[0,:]
    return boss_to_hit


def main():
    slots = 5
    global latest_crash
    generals_slots = pd.read_csv("./config/slots.csv").query('num_of_slots == @slots').reset_index().loc[0,"included_slots"].split(",")

    # #Jiggles the screen a little so the doesn't provide a false positive back to the crash detector
    # click_location_on_screen(550, 1580)
    # time.sleep(1)
    # x_axis = ' shell input swipe 430 300 430 900'
    # os.system('adb -s ' + connection_string + x_axis)
    # time.sleep(2)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    latest_crash = check_if_evony_has_crashed()
    print("HAS EVONY CRASHED? " + latest_crash)

    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
    share_chat_screen = cv2.imread('./base_images/game/share_chat_screen.png', cv2.IMREAD_UNCHANGED)
    share_chat_screen_res = len(get_location(gameplay_img, share_chat_screen, False))
    print(share_chat_screen_res)

    if(share_chat_screen_res >= 1):
        click_location_on_screen(965, 335)

    if("FALSE" in latest_crash):
        if(check_if_reset_occurred() > 0):
            perform_game_reset_seq()
            click_location_on_screen(670, 110)
        else:
            try:
                boss_df = get_all_hitable_bosses_based_off_status('Alive')
                general_to_slots_map = pd.read_csv("./config/general_to_slots_mapping.csv")
                if(len(boss_df.index) > 0):
                    for slot in generals_slots:
                        general = int(slot)
                        general_name = general_to_slots_map.query("slot_id == @general").reset_index().loc[0,"general"]

                        if(int(determine_if_slot_is_open(general)) == 0):
                            try:
                                initiate_rally(hit_boss(general), general, general_name)
                            except:
                                continue
            except:
                traceback.print_exc()
                print("Most likely queue is empty - Sleeping for 15 seconds")
                time.sleep(1)
        time.sleep(5)
    else:
        time.sleep(5)


if __name__ == "__main__":
    while(True):
        main()