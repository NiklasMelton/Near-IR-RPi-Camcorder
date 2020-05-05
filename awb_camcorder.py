import picamera.array
import numpy as np
from time import sleep
import RPi.GPIO as GPIO
from picamera import PiCamera
import threading
import time
import os
import datetime
from subprocess import call

GPIO.setmode(GPIO.BCM)

class Blinker(threading.Thread):
    def __init__(self, pin, hz=1):
        threading.Thread.__init__(self)
        self.state = False
        self.time = 0.5/hz
        self.pin = pin
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, False)
        self.daemon = True  # Allow main to exit even if still running.
        self.paused = True  # Start out paused.
        self.cond = threading.Condition()

    def run(self):
        while True:
            with self.cond:
                if self.paused:
                    self.cond.wait()
            self.state = not self.state
            GPIO.output(self.pin,self.state)
            time.sleep(self.time)

    def pause(self):
        self.state = False
        GPIO.output(self.pin, self.state)
        with self.cond:
            self.paused = True

    def resume(self):
        with self.cond:
            self.paused = False
            self.cond.notify()

class Camcorder:
    def __init__(self):
        self.camera = PiCamera()
        awb(self.camera)
        self.camera.rotation = 180
        self.button_pin = 26
        # self.led_pin = 19
        self.led_pin = 13
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.button_pin, GPIO.FALLING, callback=self.button_callback, bouncetime=300)
        self.blinker = Blinker(self.led_pin)
        self.blinker.start()


        self.record_state = False
        self.record_dir = 'cam/'
        if not os.path.exists(self.record_dir):
            os.makedirs(self.record_dir)

    def start_record(self):
        today = datetime.datetime.today()
        date_path = os.path.join(self.record_dir,today.strftime("%m_%d_%Y"))
        if not os.path.exists(date_path):
            os.makedirs(date_path)
        date_time = today.strftime("%H_%M_%S")
        file_name = os.path.join(date_path, 'near_IR_'+date_time+'.h264')
        print('recording to file ',file_name)
        self.camera.start_recording(file_name,format='h264')
        self.record_state = True
        self.blinker.resume()


    def stop_record(self):
        self.camera.stop_recording()
        self.record_state = False
        self.blinker.pause()

    def button_callback(self, channel):
        start_time = time.time()
        while GPIO.input(channel) == 0:  # Wait for the button up
            pass
        buttonTime = time.time() - start_time  # How long was the button down?
        if self.record_state:
            self.stop_record()
        elif buttonTime < 2:
            self.start_record()
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

def awb(camera):
    camera.resolution = (1280, 720)
    camera.iso = 300
    sleep(2)
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    camera.awb_mode = 'off'
    # Start off with ridiculously low gains
    rg, bg = (0.5, 0.5)
    camera.awb_gains = (rg, bg)
    with picamera.array.PiRGBArray(camera, size=(128, 72)) as output:
        # Allow 30 attempts to fix AWB
        for i in range(30):
            # Capture a tiny resized image in RGB format, and extract the
            # average R, G, and B values
            camera.capture(output, format='rgb', resize=(128, 72), use_video_port=True)
            r, g, b = (np.mean(output.array[..., i]) for i in range(3))
            print('R:%5.2f, B:%5.2f = (%5.2f, %5.2f, %5.2f)' % (
                rg, bg, r, g, b))
            # Adjust R and B relative to G, but only if they're significantly
            # different (delta +/- 2)
            if abs(r - g) > 2:
                if r > g:
                    rg -= 0.1
                else:
                    rg += 0.1
            if abs(b - g) > 1:
                if b > g:
                    bg -= 0.1
                else:
                    bg += 0.1
            camera.awb_gains = (rg, bg)
            output.seek(0)
            output.truncate()


if __name__ == '__main__':
    wake_blink()
    cam = Camcorder()
    while True:
        try:
            time.sleep(10)
        except:
            GPIO.cleanup()
            exit()