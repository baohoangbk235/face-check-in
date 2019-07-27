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

with open('/home/baohoang235/infore-check-in/Bao/trained/1/labels.npy','rb') as f:
	labels = np.load(f)

with open('/home/baohoang235/infore-check-in/Bao/trained/1/trained_knn_model.clf','rb') as f:
	knn = pickle.load(f)

f = open('check_in_results.csv','r')
csv_reader = csv.reader(f, delimiter=',')

detector = MTCNN()
name = None
total_time = 0
total_detect = 0 

c = CheckinManager('/home/baohoang235/infore-check-in/database.db')
c.delete_predictions

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
        mes = mes.reshape((480, 640, 3))
        faces = detector.detect_faces(mes)

        global csv_reader
        global name
        global c  

        predictions = c.get_predictions()

        new_predictions = []

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
                new_predictions.append(labels[int(results[1][0][0])])
            else:
                new_predictions.append("unknown")
        
        c.add_predictions(new_predictions)
        predictions = c.get_predictions()

        print(f'{mp.current_process().name} : {predictions}')
                
        if len(predictions) > 0:
            if len(predictions) < 5:
                print("Recognizing.....")
            else:
                counter = collections.Counter(predictions)
                (final_prediction, times) =  counter.most_common(1)[0]
                if times > 3:
                    checked = 0
                    if final_prediction != "unknown":
                        name = str(final_prediction)

                        now = datetime.now()

                        print(name)
                        
                        for row in reversed(list(csv_reader)):
                            date_time_obj = datetime.strptime(str(row[1]), '%m/%d/%Y-%H:%M:%S')
                            delay_check_in = int((now - date_time_obj).total_seconds())
                            if delay_check_in > 300:
                                break
                            else:
                                if row[0] ==  str(name):
                                    checked = 1
                                    print(f"[INFO] {str(row[0])} You have checked in recently!")
                                    break
                        print(delay_check_in)

                        date_time = now.strftime("%m/%d/%Y-%H:%M:%S")

                        time_stamp = int(datetime.timestamp(now))
                            
                        cv2.imwrite(os.path.join(os.getcwd(),'images','{}.jpg'.format(time_stamp)), 
                                                    face_frame)

                        row = [name, date_time, f'{time_stamp}.jpg']

                        if not checked:
                            with open('check_in_results.csv','a') as writeFile:
                                writer = csv.writer(writeFile)
                                writer.writerow(row)
                                print("[INFO]Check-in information has been saved into csv!")

                    else:
                        print("Unknown")
                        name = "Unknown"

                    predictions = []

        c.update_predictions(predictions)
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
    p1 = ctx.Process(target=create_worker, args=())
    p2 = ctx.Process(target=create_worker, args=())
    p3 = ctx.Process(target=create_worker, args=())

    p1.start()
    p2.start()
    p3.start()
    
    p1.join()
    p2.join()
    p3.join()
    f.close()
