import os

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