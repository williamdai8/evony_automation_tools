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

cnx = mysql.connector.connect(
    user=os.environ["MY_SQL_USERNAME"],
    password=os.environ["MY_SQL_PWD"],
    host='192.168.68.101',
    database='evony',
    auth_plugin='mysql_native_password')


def check_boss_exists(date, x, y, boss_name, status):

    if(status == 'null'):
        query = "SELECT * FROM rb_bosses_queue WHERE date_added = %s AND x = %s AND y = %s AND name = %s"
        params = (date, x, y, boss_name)
    else:
        query = "SELECT * FROM rb_bosses_queue WHERE date_added = %s AND x = %s AND y = %s AND name = %s AND status = %s"
        params = (date, x, y, boss_name, status)

    cursor = cnx.cursor()
    cursor.execute(query, params)
    df = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
    if len(df) > 0:
        return df.loc[0,['status']]
    else:
        return 'NULL'

    
def insert_into_rb_boss_queue(distance, x, y, name, status, priority, hit_boss, roland, outcome, lost_power, self_initiated_aw, boss_level, type, slot_used, general_used):
        
        date_added = datetime.now().strftime("%Y-%m-%d")
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = "INSERT INTO rb_bosses_queue VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        params = (date_added, distance, x, y, name, status, priority, hit_boss, roland, current_datetime, current_datetime, outcome, lost_power, self_initiated_aw, boss_level, type, slot_used, general_used)

        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()


def update_boss_data(field, value, date, x, y, boss_name):
        query = "UPDATE rb_bosses_queue SET " + field + " = %s WHERE date_added = %s AND x = %s AND y = %s AND name = %s"
        params = (value, date, x, y, boss_name)
        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()


def update_all_disappeared_bosses(period=1, field="status",value="Alive"):
        query = "UPDATE rb_bosses_queue SET " + field + " = %s WHERE modified >= NOW() - INTERVAL %s HOUR"
        params = (value, period)
        cursor = cnx.cursor()
        cursor.execute(query, params)
        cnx.commit()


def get_all_hitable_bosses_based_off_status(status, hit=1):

    query = "SELECT * FROM rb_bosses_queue WHERE status = %s and hit = %s order by priority asc, distance asc"
    params = (status, hit)

    cursor = cnx.cursor()
    cursor.execute(query, params)
    df = pd.DataFrame(cursor.fetchall(), columns=cursor.column_names)
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


def collect_new_monsters_from_AC():
    boss_list = pd.read_csv("./config/bosses.csv")
    alliance_war = 0
    bosses_names = boss_list['boss_name'].tolist()

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)

    ac_chat = cv2.imread('./base_images/game/alliance_chat_image.png', cv2.IMREAD_UNCHANGED)
    on_ac_chat_currently = len(get_location(gameplay_img, ac_chat, False))

    if(on_ac_chat_currently == 0):
        click_location_on_screen(515, 1825)
        click_location_on_screen(670, 110)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    txt = detect_text_local("capture_rb_screencap").split('\n')
    if(txt != 'NULL'):
        line_c = 0
        for line in txt:
            try:
                if re.search("^.+K:.+X:.+", line):

                    if "Alliance War" in line:
                        alliance_war = '1'
                    elif "shared Coordinates" in line:
                        alliance_war = '0'
                    else:
                        alliance_war = '0'

                    boss = ''
                    if(")" in txt[line_c + 1]):
                        boss = line + " " + txt[line_c + 1]
                    else:
                        boss = line

                    found = re.sub("started an Alliance War: | Join Now|shared Coordinates: ","",boss)
                    found = found.replace("(Boss)","Boss")

                    boss_name = found.split("(")[0]
                    boss_name = detect_fix_evony_object_name(boss_name)

                    coords = found.split("(")[1]
                    coords = re.sub("X:|Y:|K:|\)","",coords)
                    coords = re.split(" |,",coords)
                    
                    if(alliance_war == '1'):
                        print("Found (Alliance War): " + found + " - " + '"' + boss_name + '"')
                    else:
                        print("Found (Boss Share): " + found + " - " + '"' + boss_name + '"')
                    j = 0
                    for i in coords:
                        coords[j] = ''.join(c for c in i if c.isdigit())
                        j+=1
                        if(coords[2] == ''):
                            coords[2] = coords[3]
                        distance = round(math.sqrt((576-int(coords[1]))**2 + (767-int(coords[2]))**2)) + 5

                    boss_exists = check_boss_exists(datetime.now().strftime('%Y-%m-%d'), coords[1], coords[2], boss_name, 'null')

                    boss_detail = boss_list.query("boss_name == @boss_name").reset_index()
                    hitboss = str(boss_detail.loc[0, 'hit'])
                    hitbosslvl = str(boss_detail.loc[0, 'boss_level'])
                    hitbosstype = boss_detail.loc[0,'type']
                    priority = int(boss_detail.loc[0,'priorities'])

                    if(boss_exists == 'Alive' and alliance_war == '1'):
                        update_boss_data("status", "Alliance Warred", datetime.now().strftime('%Y-%m-%d'), coords[1], coords[2], boss_name)
                        update_boss_data("modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.now().strftime('%Y-%m-%d'), coords[1], coords[2], boss_name)
                        alliance_war = '0'
                    elif(boss_exists == 'NULL' and alliance_war == '1'):
                        insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Alliance Warred - Not in DB', 999, hitboss, -1, '', 0, '2', hitbosslvl, hitbosstype, 0, 'TBA')
                    elif(boss_exists == 'Dead' and alliance_war == '1'):
                        insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Alliance Warred - Self', 999, hitboss, -1, '', 0, '2', hitbosslvl, hitbosstype, 0, 'TBA')
                        alliance_war = '0'                     
                    elif(boss_exists == 'NULL' and alliance_war == '0'):
                        if(boss_name in bosses_names):
                            if(distance <= 450):
                                if(priority > 0 and priority < 999):
                                    insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Alive', priority, hitboss, -1, '', 0, '1', hitbosslvl, hitbosstype, 0, 'TBA')
                                    print(boss_name + " added!")
                                else:
                                    insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Criteria', 999, hitboss, -1, '', 0, '0', hitbosslvl, hitbosstype, 0, 'TBA')
                                    print(boss_name + " does not meet criteria")
                            else:
                                insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Distance', 888, hitboss, -1, '', 0, '0', hitbosslvl, hitbosstype, 0, 'TBA')
                                print(boss_name + " exceed Rallybot Range!")
                        else:
                            insert_into_rb_boss_queue(distance, coords[1], coords[2], boss_name, 'Non-Boss', 999, 0, -1, '', 0, '0', 0, "None", 0, "None")
                            print(boss_name + " does not meet criteria")
                    else:
                        print("Duplicate Monster / Boss not in DB")
            except:
                a = 1
                # traceback.print_exc()
            line_c += 1
        return
    else:
        return


def attack_monster(present):
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
            gameplay_img = cv2.imread('./base_images/screenshots/capture_rb_screencap.png', cv2.IMREAD_UNCHANGED)
            target_img = cv2.imread('./base_images/game/alliance_war_button.png', cv2.IMREAD_UNCHANGED)
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
            time.sleep(3)
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
    sleep_counter = attack_monster(general_no)

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
    slots = 4
    global latest_crash
    generals_slots = pd.read_csv("./config/slots.csv").query('num_of_slots == @slots').reset_index().loc[0,"included_slots"].split(",")

    #Jiggles the screen a little so the doesn't provide a false positive back to the crash detector
    click_location_on_screen(550, 1580)
    time.sleep(1)
    x_axis = ' shell input swipe 430 300 430 900'
    os.system('adb -s ' + connection_string + x_axis)
    time.sleep(2)

    take_screenshot_enhanced("./base_images/screenshots/", "capture_rb_screencap")
    latest_crash = check_if_evony_has_crashed()
    print("HAS EVONY CRASHED? " + latest_crash)

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
                time.sleep(5)
        time.sleep(5)
    else:
        time.sleep(15)


if __name__ == "__main__":
    while(True):
        main()