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




def synchronize(client_socks,average_latency=None,clock=None):
    if clock is None:
        clock = Clock()
    n_c = len(client_socks)+1
    clock_times = -np.ones(n_c)
    rec_times = -np.ones(n_c)
    latency = np.zeros(n_c)
    mask = np.ones(n_c,dtype=bool)
    for ci, client_sock in enumerate(client_socks):
        t0 = time.time()
        client_sock.send('tick')
        data = ''
        t1 = 0
        while 'tock' not in data and (t1-t0) < 10:
            data = client_sock.recv(1024)
            t1 = time.time()
        if 'tock' in data:
            data = data.split('-')
            clock_times[ci] = float(data[1])
            latency[ci] = t1-t0
            rec_times[ci] = t1
        else:
            mask[ci] = 0

    adjusted_clock_times = clock_times[mask] + 0.5*latency[mask]
    clock_times[-1] = clock.check()
    t2 = time.time()
    rec_times[-1] = t2
    updated_average_adjusted_clock_time = np.mean(adjusted_clock_times + (t2-rec_times[mask]))
    if average_latency is None:
        if np.sum(mask):
            latency[not mask] = np.mean(latency[mask])
        else:
            latency = np.zeros(n_c)
        average_latency = latency
    else:
        average_latency *= 0.97
        average_latency += 0.03 * latency

    clock_times_to_send = updated_average_adjusted_clock_time + 0.5*average_latency
    for ci, client_sock in enumerate(client_socks):
        client_sock.send('set-{}'.format((time.time()-t2)+clock_times_to_send[ci]))
    clock.set(updated_average_adjusted_clock_time+(time.time()-t2))

    return average_latency







