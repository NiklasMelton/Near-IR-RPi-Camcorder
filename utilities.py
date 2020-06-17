import numpy as np
import time
import RPi.GPIO as GPIO
import threading
import time

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

    def change_freq(self,hz):
        self.time = 0.5/hz

class Clock:
    def __init__(self,t=None):
        if t is None:
            t = time.time()
        self.ref_time = t
        self.set_time = t

    def set(self,t,set_time=None):
        if set_time is None:
            self.set_time = time.time()
        else:
            self.set_time = set_time
        self.ref_time = t

    def check(self):
        return self.ref_time + (time.time() - self.set_time)









