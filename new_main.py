import pika 
import cv2 
import numpy as np 
from db import CheckinManager
import threading

# cap = cv2.VideoCapture('rtsp://192.168.1.254:554/user=admin&password=&channel=3&stream=0.sdp?real_stream--rtp-caching=100')


def send_frame(frame, camID):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    frame = frame.astype(np.uint8)

    camera = np.ones((480,1,3)) * camID

    mes = np.hstack((frame, camera)).astype(np.uint8).tobytes()

    
    channel.basic_publish(exchange='',
        routing_key='frame_queue',
        body=mes,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))

    connection.close()

count_detect = 0
detect_delay = 2

import time 

class camThread(threading.Thread):
    def __init__(self, previewName, cam_channel, camID):
        threading.Thread.__init__(self)
        self.previewName = previewName
        self.cam_channel = cam_channel
        self.camID = camID
    def run(self):
        print("Starting " + self.previewName)
        camPreview(self.previewName, self.cam_channel, self.camID)

def camPreview(previewName, cam_channel, camID):
    count_detect = 0
    cv2.namedWindow(previewName)
    cam = cv2.VideoCapture(cam_channel)
    if cam.isOpened():  # try to get the first frame
        rval, frame = cam.read()
    else:
        rval = False

    while rval:
        start = time.time()
        cv2.imshow(previewName, frame)
        rval, frame = cam.read()
        if count_detect % detect_delay == 0:
            send_frame(frame, camID)
        key = cv2.waitKey(20)
        if key == 27:  # exit on ESC
            break
        
        count_detect += 1
        end = time.time()
        print(f"FPS : {float((end-start))}")

    cv2.destroyWindow(previewName)
    cam.release()

thread1 = camThread("Camera 1", 'rstp://',1)
thread2 = camThread("Camera 2", 'rstp://',2)
thread1.start()
thread2.start()

