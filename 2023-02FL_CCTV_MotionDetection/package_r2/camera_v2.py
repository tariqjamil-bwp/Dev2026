import cv2
import time
import database
from datetime import datetime
import os
from motion_v2 import motionDetection, objectDetection, objectDetection_yolo
from config import cfg

def gen_frames(cam_id):
    cameras = database.CCTV_DB().get_CCTV_List()
    settings = database.SETTINGS_DB().get_settings_Dict()

    storagePath = str(settings['filePath'] + '\\')
    fourcc = cv2.VideoWriter_fourcc(*cfg.video.Encoder)
    start_time = time.time()

    for cctv in cameras:
        
        if int(cctv.doc_id) == int(cam_id):
            cap = cv2.VideoCapture(f'{cctv["protocol"]}://{cctv["username"]}:{cctv["password"]}@{cctv["ip"]}:{cctv["port"]}')
            time.sleep(1)
            print("Started  @  : " + str(datetime.now().strftime("%Y-%m-%d-%H%M%S")))
            
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))    #frame_width = int(cap.get(3))
            frame_height= int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))   #frame_height= int(cap.get(4))
            if frame_width <10 or frame_height < 10:
                print('Camera Errro, exiting...', frame_width, frame_height)
                break
            
            dimensions = (int(frame_width * cfg.video.Scale), int(frame_height * cfg.video.Scale) )
            
            fileName = storagePath + "\\" + str(cctv.doc_id) + "\\" + str(
                datetime.now().strftime("%Y-%m-%d-%H%M%S")) + ".avi"
                        
            if not os.path.isdir(storagePath + "\\" + str(cctv.doc_id)):
                os.makedirs(storagePath + "\\" + str(cctv.doc_id))
                        
            out = cv2.VideoWriter(fileName, fourcc, cfg.video.Fps, dimensions)

            recordDuration = int(settings['vidDuration']) * 60
            print("Record Duration : " + str(recordDuration))

            while True:
                now = time.time()
                success, frame = cap.read()  # read the camera frame
                elapsed = round(now - start_time)
                
                if not success:
                    cap.release()
                    ## Tries to reset !!
                    cap = cv2.VideoCapture(f'{cctv["protocol"]}://{cctv["username"]}:{cctv["password"]}@{cctv["ip"]}:{cctv["port"]}')
                    print("Stopped @  : " + str(datetime.now().strftime("%Y-%m-%d-%H%M%S")))

                else:
                    the_frame = frame.copy()
                    if cfg.video.Scale < 1.0:   # rescale if rescale factor is set (lower than 1)
                        the_frame = cv2.resize(frame, dimensions, interpolation=cv2.INTER_AREA)  # rescaling using opencv
                    try:
                        if elapsed < recordDuration:  
                            if elapsed > 1.5: # motion detection starts  #TJ .. bounding boxes drawn prior to saving
                                #the_frame, motion = motionDetection(frameX, the_frame, disp=True)  #TJ
                                the_frame, motion = objectDetection(the_frame, disp=True)
                                #the_frame, motion = objectDetection_yolo(the_frame, disp=True)
                                if not(cfg.video.Flag):
                                    print('human or motion detected:', motion > 0)
                                pass
                        
                            out.write(the_frame) #TJ write after all the processing, 
                            frameX = the_frame # TJ > saving frame for motion detection  tracking for motionDetection function

                        else:
                            #out.write(rescaled_frame)  #TJ
                            out.release()
                            print("Record Saved : " + fileName, elapsed)
                            
                            print("Starting new ...")
                            fileName = storagePath + "\\" + str(cctv.doc_id) + "\\" + str(
                                datetime.now().strftime("%Y-%m-%d-%H%M%S")) + ".avi"
                            #out = cv2.VideoWriter(fileName, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10,
                            #                      (frame_width, frame_height))
                            out = cv2.VideoWriter(fileName, fourcc, cfg.video.Fps, dimensions)
                            #initializing timer                       
                            start_time = time.time()
                      
                    except Exception as e:
                        print("Error Rised : "+ str(e))

                    ret, buffer = cv2.imencode('.jpg', the_frame)   # the frame can be replaced with rescaled_frame if related to disk storage
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + the_frame + b'\r\n')
    
    return "Camera not found"