import signal 
import multiprocessing as mp
import pika 
import sys
import cv2
import numpy as np 
from mtcnn.mtcnn import MTCNN
import pickle
import face_recognition
from utils import CentroidTracker
import time
import collections
from datetime import datetime
import csv
import os
import pickle
from db import CheckinManager

import yaml
CONFIG_PATH = 'config.yaml'
try:
    config_file = open(CONFIG_PATH, 'r')
    cfg = yaml.safe_load(config_file)
except:
    raise ("Error: Config file does not exist !")

CPU_COUNT = cfg['cpu_count']
DATABASE = cfg['database']
LABEL_PATH = cfg['label_path']
ENCODING_PATH = cfg['encoding_path']
KNN_MODEL = cfg['trained_model']
RETRAIN_DIR = cfg['retrain_images_dir']

with open(LABEL_PATH,'rb') as f:
	labels = list(np.load(f))

with open(KNN_MODEL,'rb') as f:
	knn = pickle.load(f)

with open(ENCODING_PATH,'rb') as f:
    encodings = list(np.load(f))

retrain_images_dir = '/home/baohoang235/face-check-in/retrain_images'

f = open('check_in_results.csv','r')
csv_reader = csv.reader(f, delimiter=',')

detector = MTCNN()
name = None
total_time = 0
total_detect = 0 

c = CheckinManager(DATABASE,2)

def create_worker():

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost'))

    channel = connection.channel()

    channel.queue_declare(queue='frame_queue', durable=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='frame_queue', on_message_callback=callback)

    channel.start_consuming()

    return callback

def callback(ch, method, properties, body):
    print("\n[INFO] Receiving ...")
    try:
        start = time.time()
        mes = np.frombuffer(body, dtype=np.uint8)
        mes = mes.reshape((480, 641, 3))
        
        camID = int(mes[0,640,0])

        mes = mes[:,:640,:]

        print(f"[INFO] Camera ID :  {camID}")

        faces = detector.detect_faces(mes)

        global csv_reader
        global name
        global c 
        global encodings 

        predictions = c.get_predictions(camID)

        faces_locations = []

        max_size = 0
        max_face = []
        max_index = 0
        face_frame = None

        for i,face in enumerate(faces):
            x,y,w,h = face["box"]
            faces_locations.append([y,x+w,y+h,x])
            if max_size < w * h:
                max_size = w * h
                max_face = [y,x+w,y+h,x]
                max_index = i
                face_frame = np.array(mes[y:y+h,x:x+w])

        if len(faces_locations) > 0:
            faces_encodings = face_recognition.face_encodings(mes, [max_face])
            results = knn.kneighbors(faces_encodings, n_neighbors=1)
            if results[0][0][0] < 0.4 and faces[max_index]["confidence"] > 0.96:
                c.add_prediction(labels[int(results[1][0][0])], camID)
            else:
                c.add_prediction("unknown", camID)
        
        predictions = c.get_predictions(camID)

        print(f'{mp.current_process().name} : {predictions}')
                
        if len(predictions) > 0:
            if len(predictions) < 5:
                print("Recognizing.....")
            else:
                predictions = predictions[-5:]
                counter = collections.Counter(predictions)
                (final_prediction, times) =  counter.most_common(1)[0]
                if times > 3:
                    checked = False
                    if final_prediction != "unknown":
                        name = str(final_prediction)

                        now = datetime.now()

                        date_time = now.strftime("%m/%d/%Y-%H:%M:%S")

                        time_stamp = int(datetime.timestamp(now))
                        
                        class_retrain_dir = os.path.join(os.getcwd(),RETRAIN_DIR, name)

                        if not os.path.exists(class_retrain_dir):
                            os.mkdir(class_retrain_dir)

                        cv2.imwrite(os.path.join(class_retrain_dir,'{}.jpg'.format(time_stamp)), 
                                                    face_frame)

                        checked = c.check(name, now)

                        if not checked:
                            c.add_result(name, date_time, os.path.join(class_retrain_dir,'{}.jpg'.format(time_stamp)))
                            print("\n[INFO] {} has been checked in successfully.\n".format(name))

                        encodings.append(faces_encodings)
                        labels.append(name)

                    else:
                        print("Unknown")
                        name = "Unknown"

                    predictions = []

        c.update_predictions(predictions, camID)
        end = time.time()
        print(f'Time processing: {end - start} s.')

        global total_detect 
        global total_time 
        total_detect += 1
        total_time += end-start

    except Exception as e:
        print(str(e))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
       
    ch.basic_ack(delivery_tag=method.delivery_tag)
    return 1

def exit_signal_handler(sig, frame):
    print('You pressed Ctrl+C.')
    sys.exit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_signal_handler)
    ctx = mp.get_context('spawn')
    process_list = []
    for i in range(CPU_COUNT):
        p = ctx.Process(target=create_worker, args=())
        process_list.append(p)
        
    for p in process_list:
        p.start()
    
    for p in process_list:
        p.join()

