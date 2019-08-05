import cv2

cap1 = cv2.VideoCapture('rtsp://192.168.1.254:554/user=admin&password=&channel=3&stream=0.sdp?real_stream--rtp-caching=100')
cap2 = cv2.VideoCapture('rtsp://192.168.1.254:554/user=admin&password=&channel=2&stream=0.sdp?real_stream--rtp-caching=100')

while(True):
    ret, frame = cap1.read()

    ret2, frame2 = cap2.read()
    if not ret or not ret2:
        break 

    print("[INFO] Success")

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break 

cap1.release()
cap2.release()
cv2.destroyAllWindows()
    

