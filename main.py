import pika 
import cv2 
import numpy as np 
from db import CheckinManager
import threading

# cap = cv2.VideoCapture('rtsp://192.168.1.254:554/user=admin&password=&channel=3&stream=0.sdp?real_stream--rtp-caching=100')
cap_list = []
cap = cv2.VideoCapture(0)
cap_list.append(cap)
c = CheckinManager('/home/baohoang235/face-check-in/database.db')

def send_frame(frame, camera_channel):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # for (top, right, bottom, left, match) in face_locations_match:
    #     face_frame = frame[top:bottom, left:right, :]
    
    # mes = frame.astype(np.uint8).tobytes()

    frame = frame.astype(np.uint8)

    camera = np.ones((480,1,3)) * camera_channel

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

while(True):
    start = time.time()
    for cap in cap_list:
        ret, frame = cap.read()

        if not ret:
            break 

        frame = cv2.resize(frame, (640,480))

        if count_detect % detect_delay == 0:
            send_frame(frame, 0)

            # predictions, locations = c.get_predictions()

            # if len(locations) > 0:
            #     for face_location in locations:
            #         top, right, bottom, left = face_location
            #         cv2.rectangle(frame, (left,top), (right, bottom), (0,255,0), 2)

        
    end = time.time()

    count_detect += 1

    print(f"FPS : {float((end-start))}")

    cv2.imshow('frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
