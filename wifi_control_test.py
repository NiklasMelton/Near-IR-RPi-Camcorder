import os
from PyAccessPoint import pyaccesspoint
import time

def create_access_point():
    access_point = pyaccesspoint.AccessPoint(ssid='PiCam-net',password='spectral')
    access_point.start()
    time.sleep(5)
    if access_point.is_running():
        print('access point up')
        time.sleep(60)
    print('shutting down access point')
    access_point.stop()


if __name__ == '__main__':
    user = os.popen("whoami").read()
    if 'root' not in user:
        print('Must be root.')
        exit()
    status = os.popen("ifconfig wlan0 up").read()
    if 'No such device' in status:
        print('Missing wireless device.')
        exit()
    winame = "wlan0"
    print("Wireless device enabled!")
    print("Checking for available wireless networks...")
    stream = os.popen("iwlist " + winame + " scan")
    print("Available Networks:")
    networksfound = 0
    for line in stream:
        if "ESSID" in line:
            networksfound += 1
            print(" " + line.split('ESSID:"', 1)[1].split('"', 1)[0])
    if networksfound == 0:
        print
        "Looks like we didn't find any networks in your area. Exiting..."
        quit()
    network = 'MeltonHome'
    tpass = ''
    connectstatus = os.popen("iwconfig " + winame + " essid " + network + " key s:" + tpass)
    print("Connecting...")
    ontest = os.popen("ping -c 1 google.com").read()
    if ontest == '':
        print("Connection failed. (Bad pass?)")
        exit()
    print("Connected successfully!")