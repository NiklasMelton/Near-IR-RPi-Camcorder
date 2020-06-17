import os
import pyaccesspoint
import time
import RPi.GPIO as GPIO
from picamera import PiCamera
import threading
import time
import os
import json
import datetime
from subprocess import call
import socket
import numpy as np
from utilities import Blinker, Clock

GPIO.setmode(GPIO.BCM)

class distributed_camcorder:
    def __init__(self):
        self.access_point = None
        self.type = 'client'
        self.red_led = Blinker(13,hz=5)
        self.green_led = Blinker(19,hz=5)
        self.green_led.start()
        self.red_led.start()

        self.server_sock = None
        self.client_socks = dict()
        self.tick_times = dict()
        self.tock_times = dict()
        self.client_clock_times = dict()
        self.average_latency = dict()
        self.sock_response_tracker = dict()

        self.max_c = 8

        self.available_enumerations = list(range(self.max_c))[::-1]

        self.camera_settings = {
            'iso': 400,
            'shutter_speed': None,
            'rg': 0.5,
            'bg': 0.5,
        }
        self.next_shutter = None
        self.clock = Clock()

        self.start_up()

    def start_up(self):
        self.thinking_blink()
        if self.configure_network():
            self.affirmitive_blink()
        else:
            self.negative_blink()
            exit()
        if type == 'server':
            self.start_server()
            self.affirmitive_blink()
        else:
            if self.connect_to_server():
                self.connected_blink()
            else:
                self.negative_blink()

    def affirmitive_blink(self,t=3, freq=5):
        self.green_led.change_freq(freq)
        self.green_led.resume()
        time.sleep(t)
        self.green_led.pause()

    def negative_blink(self,t=3, freq=5):
        self.red_led.change_freq(freq)
        self.red_led.resume()
        time.sleep(t)
        self.red_led.pause()

    def connected_blink(self,t=3):
        self.negative_blink(t=2,freq=10)
        self.affirmitive_blink(t=4,freq=10)

    def thinking_blink(self,t=3):
        self.red_led.change_freq(2)
        self.green_led.change_freq(2)
        self.red_led.resume()
        self.green_led.resume()
        time.sleep(t)
        self.red_led.pause()
        self.green_led.pause()

    def create_access_point(self):
        # os.popen("ifconfig wlan0 down")
        # time.sleep(5)
        # os.popen("ifconfig wlan0 up")
        self.access_point = pyaccesspoint.AccessPoint(ssid='PiCam-Net',password='spectral')
        self.access_point.stop()
        self.access_point.start()
        time.sleep(5)
        return self.access_point.is_running()

    def configure_network(self):
        ontest = os.popen("ping -c 1 192.168.45.1").read()
        transmission = [x for x in ontest.split('\n') if 'packets transmitted' in x]
        if transmission:
            _, _, loss, _ = transmission[0].split(', ')
            transmission_rate = 1. - float(loss.split('%')[0]) / 100.
        else:
            transmission_rate = 0.0
        if transmission_rate == 0.:
            print("No network available. Creating new network")
            if self.create_access_point():
                self.type = 'server'
                print('Network successfully created')
            else:
                print('Failed to create network. Defaulting to client')
                return False
        else:
            print('Transmission Rate:',transmission_rate)
            print("Connected successfully!")
        return True

    def connect_to_server(self):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.connect(('192.168.45.1', '6969'))
            return True
        except Exception as E:
            print(E)
            del self. server_sock
            self.server_sock = None
            return False

    def start_server(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.bind(('0.0.0.0', '6969'))

    def listen(self):
        self.server_sock.listen(5)
        while True:
            client, address = self.server_sock.accept()
            client.settimeout(60)
            self.client_socks[address] = {'client': client, 'cid': self.available_enumerations.pop()}
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()

    def listen_to_client(self,client, address):
        while True:
            try:
                data = client.recv(1024)
                if data:
                    # Set the response to echo back the recieved data
                    self.process_messages(data,address)
                else:
                    raise ConnectionError('Client disconnected')
            except:
                client.close()
                with threading.Lock():
                    self.available_enumerations.append(self.client_socks[address]['cid'])
                    del self.client_socks[address]
                return False

    def synchronize_server(self, display=False):
        for address, client_sock in self.client_socks.items():
            self.sock_response_tracker[address] = False
            if address not in self.average_latency:
                self.average_latency[address] = 0
            self.tick_times[address] = time.time()
            client_sock['client'].send('tick')
        self.client_clock_times['localhost'] = self.clock.check()
        self.sock_response_tracker['localhost'] = True
        self.average_latency['localhost'] = 0


        t0 = time.time()
        while not all(self.sock_response_tracker.values()) and (time.time()-t0) < 3:
            time.sleep(0.05)

        adjusted_clock_times = {addr: self.client_clock_times[addr] + self.average_latency[addr] for addr in self.client_socks.keys() if self.sock_response_tracker[addr]}
        t2 = time.time()
        average_adjusted_clock_time = np.mean([ct + (t2 - self.tock_times[addr]) for addr,ct in adjusted_clock_times.items()])


        clock_times_to_send = {addr: average_adjusted_clock_time + avg_lat for addr,avg_lat in self.average_latency.items}
        for addr, client_sock in enumerate(self.client_socks):
            client_sock.send('{set_clock: {}}'.format((time.time() - t2) + clock_times_to_send[addr]))
        self.clock.set(average_adjusted_clock_time + (time.time() - t2))

        if display:
            for addr, t1 in adjusted_clock_times:
                print('Address: {} ---- DT: {}'.format(addr,abs(average_adjusted_clock_time-t1)))


    def process_messages(self,msg,cid=None):
        msg = json.loads(msg.decode("utf8").rstrip())
        if 'tick' in msg:
            self.server_sock.send("{'tock':{} }".format(self.clock.check()))
        else:
            outgoing_payload = '{'
            if 'tock' in msg and cid:
                with threading.Lock():
                    latency = 0.5*(time.time() - self.tick_times[cid])
                    payload = float(msg['tock'])
                    self.client_clock_times[cid] = float(payload)
                    self.sock_response_tracker[cid] = True
                    if self.average_latency[cid]:
                        self.average_latency[cid] = 0.9*self.average_latency[cid] + 0.1*latency
                    else:
                        self.average_latency[cid] = float(latency)

            elif 'set_time' in msg:
                payload = float(msg['set_time'])
                with threading.Lock():
                    self.clock.set(payload)
                outgoing_payload += 'set_time_confirmation: True, '

            elif 'set_shutter' in msg:
                payload = float(msg['set_shutter'])
                with threading.Lock():
                    self.next_shutter = float(payload)
                if self.next_shutter > self.clock.check():
                    outgoing_payload += 'set_shutter_confirmation: True, '
                else:
                    outgoing_payload += 'set_shutter_confirmation: False, '


            elif 'set_wb' in msg:
                a,b = msg['set_awb'].split(',')
                with threading.Lock():
                    self.set_white_balance(float(a),float(b))
                outgoing_payload += 'set_wb_confirmation: True, '

            elif 'set_iso' in msg:
                a = msg['set_iso']
                with threading.Lock():
                    self.set_iso(int(a))
                outgoing_payload += 'set_iso: True, '

            elif 'set_exposure' in msg:
                a = msg['set_exposure']
                with threading.Lock():
                    self.set_exposure(int(a))
                outgoing_payload += 'set_exposure: True, '


            elif 'set_shutter_confirmation' in msg and not msg['set_shutter_confirmation']:
                with threading.Lock():
                    self.next_shutter = None
                    self.cancel_current_recording()


    def cancel_current_recording(self):
        pass




if __name__ == '__main__':
    dc = distributed_camcorder()
    time.sleep(5)
    dc.synchronize_server(display=True)
    time.sleep(5)
    dc.synchronize_server(display=True)
    time.sleep(5)
    dc.synchronize_server(display=True)
    time.sleep(5)
    dc.synchronize_server(display=True)
    time.sleep(10)
    # os.popen("shutdown 0")