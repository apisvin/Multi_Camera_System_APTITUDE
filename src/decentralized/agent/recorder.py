import cv2
import csv
import logging
from agent.agent import Agent
import time


class Recorder(Agent):
    
    def __init__(self, stopFlag, dicqueue, rec_path = "/home/pi/Multi_Camera_System_APTITUDE/results/video.avi", time_path = "/home/pi/Multi_Camera_System_APTITUDE/results/time_video.csv"):
        """
        Recorder is the recording agent. It records the video flux in a file during its life span.
        Args : 
            stopFlag : flag to stop executing thread 
            neighbourhood : a class containing all neighbours of the agent
            dicqueue : distionnary containing queues for inter-thread communication
            rec_path : path in which the video is recorded
            time_path : path in which the time of each frame is recorded
        """
        self.stopFlag  = stopFlag
        self.dicqueue  = dicqueue
        self.rec_path  = rec_path
        self.time_path = time_path
        
    def launch(self):
        """
        Launch the recording.
        """
        # Sizing frames
        width = 1920
        height = 1088
        fps=5
        cap = cv2.VideoCapture(-1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer= cv2.VideoWriter(self.rec_path,
                                fourcc,
                                fps,
                                (width,height))
        logging.info("recorder begins at time = {}".format(time.time()))
        
        with open(self.time_path, "w") as time_file:
            header = ["time"]
            writer_time = csv.DictWriter(time_file, fieldnames=header)
            writer_time.writeheader()
        
            while self.stopFlag.is_set()==False:
                ret, frame = cap.read()
                if(ret):
                    writer.write(frame)
                    writer_time.writerow({'time' : time.time()})
                    #cv2.imshow('frame',frame)
                    #cv2.waitKey(1)
        logging.info("end recorder at time = {}".format(time.time()))
        writer.release()
        cap.release()
        cv2.destroyAllWindows()