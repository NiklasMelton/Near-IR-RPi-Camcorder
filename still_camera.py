import RPi.GPIO as GPIO
from picamera import PiCamera
import threading
import time
import os
import datetime
from subprocess import call

GPIO.setmode(GPIO.BCM)

class Camera:
    def __init__(self):
        self.camera = PiCamera(resolution=(1280, 720))
        self.camera.rotation = 180
        self.button_pin = 26
        # self.led_pin = 19
        self.led_pin = 13
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.led_pin, GPIO.OUT)
        GPIO.output(self.led_pin, False)
        GPIO.add_event_detect(self.button_pin, GPIO.FALLING, callback=self.button_callback, bouncetime=300)
        self.camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        GPIO.output(self.led_pin, True)

        self.lock = False

        self.record_dir = 'cam/'
        if not os.path.exists(self.record_dir):
            os.makedirs(self.record_dir)

    def capture(self):
        self.lock = True
        today = datetime.datetime.today()
        date_path = os.path.join(self.record_dir,today.strftime("%m_%d_%Y"))
        if not os.path.exists(date_path):
            os.makedirs(date_path)
        date_time = today.strftime("%H_%M_%S")
        file_name = os.path.join(date_path, 'near_IR_'+date_time+'.h264')
        print('saving to file ',file_name)
        GPIO.output(self.led_pin, False)
        self.camera.capture(file_name)
        time.sleep(0.5)
        GPIO.output(self.led_pin, True)
        self.lock = False


    def button_callback(self, channel):
        start_time = time.time()
        while GPIO.input(channel) == 0:  # Wait for the button up
            pass
        buttonTime = time.time() - start_time  # How long was the button down?
        if buttonTime < 2 and not self.lock:
            self.capture()
        if buttonTime >= 2:
            shutdown_blink(self.led_pin)
            shutdown()


def shutdown_blink(pin=23):
    GPIO.setup(pin, GPIO.OUT)
    for _ in range(5):
        GPIO.output(pin, True)
        time.sleep(0.3)
        GPIO.output(pin, False)
        time.sleep(0.3)

def wake_blink(pin=23):
    GPIO.setup(pin, GPIO.OUT)
    for _ in range(2):
        GPIO.output(pin, True)
        time.sleep(1)
        GPIO.output(pin, False)
        time.sleep(0.3)

def shutdown():
    call("sudo shutdown -h now", shell=True)
    GPIO.cleanup()
    exit()

if __name__ == '__main__':
    wake_blink()
    cam = Camera()
    while True:
        try:
            time.sleep(1)
        except:
            GPIO.cleanup()
            exit()



