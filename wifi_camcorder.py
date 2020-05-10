import os
from PyAccessPoint import pyaccesspoint
import time
import RPi.GPIO as GPIO
from picamera import PiCamera
import threading
import time
import os
import datetime
from subprocess import call
from utilities import Blinker

GPIO.setmode(GPIO.BCM)

class distributed_camcorder:
    def __init__(self):
        self.access_point = None
        self.type = 'client'
        self.red_led = Blinker(13,hz=0.5)
        self.green_led = Blinker(19,hz=0.25)
        self.green_led.start()
        self.red_led.start()
        self.red_led.resume()
        self.green_led.resume()
        time.sleep(5)
        self.green_led.pause()
        self.red_led.pause()

        if self.configure_network():
            led = self.green_led
        else:
            led = self.red_led
        led.change_freq(0.2)
        led.resume()
        time.sleep(3)
        led.pause()


    def create_access_point(self):
        os.popen("ifconfig wlan0 down")
        time.sleep(3)
        self.access_point = pyaccesspoint.AccessPoint(ssid='PiCam-net',password='spectral')
        self.access_point.start()
        time.sleep(3)
        return self.access_point.is_running()

    def configure_network(self):
        ontest = os.popen("ping -c 1 192.168.45.1").read()
        if ontest == '':
            print("No network available. Creating new network")
            if self.create_access_point():
                self.type = 'server'
                print('Network successfully created')
            else:
                print('Failed to create network. Defaulting to client')
                return False
        else:
            print(ontest)
            print("Connected successfully!")
        return True


if __name__ == '__main__':
    distributed_camcorder()