#!/usr/bin/python3
# TCP Client for Object Flow Detection
import sys
import socket
import numpy as np
import cv2
import queue, threading, time
import pickle
import math

class VideoCaptureBuffer:

  def __init__(self, name):
    self.cap = cv2.VideoCapture(name)
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
      ret, frame = self.cap.read()
      if not ret:
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()   # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.q.put(frame)

  def read(self):
    return self.q.get()




class TCP_client:

    def __init__(self, HOST, PORT, ITERATIONS):
        self.HOST = HOST
        self.PORT = PORT
        self.ITERATIONS = ITERATIONS
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()
        self.cam = VideoCaptureBuffer(0)

    def connect_to_server(self):
        print(socket.gethostbyname('BlackPanther-Linux.local'))
        print('Connecting to', self.HOST, 'on PORT', self.PORT)
        while True:
            try:
                # self.client.settimeout(10)
                self.client.connect((self.HOST, self.PORT))
                print('Connection to server established')
                break
            except Exception as e:
                # print(e)
                # print('Could not connect to server on', self.HOST, 'PORT:',self.PORT)
                pass

    def send_shortMSG(self, type = None):
        if type == 'packet_size':
            sample_packet = self.send_longMSG(get_packet_size = True)
            sample_packet_size = len(pickle.dumps(sample_packet))
            # print('Packet size to be sent:',sample_packet_size)
            packet = {'DID':'packet_size', 'ITERATIONS':self.ITERATIONS, 'PAYLOAD':sample_packet_size}
            self.client.send(pickle.dumps(packet))
            self.recieve_from_server(supression = True)
        elif type == 'end_process':
            packet = {'DID':'end_process','PAYLOAD':None}
            self.client.send(pickle.dumps(packet))
        else:
            print('Unknown type for short MSG.')
            self.close_client()

    def send_longMSG(self, get_packet_size = False):
        if get_packet_size:
            payload = self.generate_payload()
            packet = {'DID':'frame', 'PAYLOAD':payload}
            return packet
        else:
            k = 0
            while True:
                payload = self.generate_payload()
                packet = {'DID':'frame','PAYLOAD':payload}
                packet_pickled = pickle.dumps(packet)
                # print('Size of package to be sent:',len(packet_pickled))
                self.client.send(packet_pickled)
                k += 1
                if k == self.ITERATIONS: break
                self.recieve_from_server(supression = True)

    def generate_payload(self):
        frame = self.cam.read()
        frame = cv2.flip(frame,-1)
        return frame

    def recieve_from_server(self, supression = True):
        packet_from_server = self.client.recv(4096)
        if not supression:
            print(pickle.loads(packet_from_server))

    def close_client(self):
        try:
            self.client.close()
            print('Connection to server closed')
        except:
            print('Could not properly close client')
            quit()


# Specify the HOST and PORT used by server
# HOST = '127.0.0.1'
HOST = '10.0.0.2'
# HOST = '127.0.1.1'
# HOST = 'BlackPanther-Linux'
PORT = 65433

# Specify how many frames the client should send
ITERATIONS = 0

# Create the connection object and connect to server
connection = TCP_client(HOST, PORT, ITERATIONS)

# Send SM to server specifying the packet size and iterations
connection.send_shortMSG(type = 'packet_size')

# Start LM communication with server, specifying number of iterations
connection.send_longMSG(get_packet_size = False)

# Close the client
connection.close_client()
