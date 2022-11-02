import cv2
from agent.agent import Agent


class Recorder(Agent):
    
    def __init__(self, stopFlag, dicqueue):
        self.stopFlag = stopFlag
        self.dicqueue = dicqueue
        self.rec_path = "/home/pi/Multi_Camera_System_APTITUDE/results/video.avi"
        
    def launch(self):
        # Sizing frames
        width = 1920
        height = 1088
        fps=60
        cap = cv2.VideoCapture(-1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        #cap.set(cv2.CAP_PROP_FPS, fps)
        
        #set buffersize to display without delay
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        writer= cv2.VideoWriter(self.rec_path,
                                fourcc,
                                fps,
                                (width,height))
        print("recorder begins")
        while self.stopFlag.is_set()==False:
            ret, frame = cap.read()
            if(ret):
                writer.write(frame)
                cv2.imshow('frame',frame)
                cv2.waitKey(1)
        print("end recorder")
        writer.release()
        cap.release()
        cv2.destroyAllWindows()