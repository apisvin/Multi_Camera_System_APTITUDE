"""
Copyright (c) 2021-2022 UCLouvain, ICTEAM
Licensed under GPL-3.0 [see LICENSE for details]
Written by Jonathan Samelson (2021-2022)
Modified by Arthur Pisvin (2022)
"""

from pytb.detection.bboxes.bboxes_2d_detector.bboxes_2d_detector import BBoxes2DDetector
from pytb.output.bboxes_2d import BBoxes2D

from timeit import default_timer
import cv2
import numpy as np
import logging

log = logging.getLogger("aptitude-toolbox")

BINARY_THRESHOLD_ABOVE_50PC_OF_HISTOGRAM = 18  # 24 # The threshold in the graysale image for deciding if a deviation from the background is an object or not, relative to the point in the histogram under which 50 percent of total intensity can be found

class BackgroundSubtractor(BBoxes2DDetector):

    def __init__(self, proc_parameters: dict):
        """Initializes the detector with the given parameters.

        Args:
            proc_parameters (dict): A dictionary containing the BackgroundSubstractor detector parameters
        """
        super().__init__(proc_parameters)
        # From cv2.approxPolyDP: Specifies the approximation accuracy. 
        # This is the maximum distance between the original curve and its approximation.
        self.contour_thresh = proc_parameters["params"].get("contour_thresh", 3)

        # The minimum intensity of the pixels in the foreground image.
        self.intensity = proc_parameters["params"].get("intensity", 50)

        log.debug("BackgroundSubtractor {} implementation selected.".format(self.pref_implem))
        if self.pref_implem == "mean" or self.pref_implem == "median":
            # If the pref_implem is "mean" or "median", the results will be based on the mean or median
            # values of the previous images. 
            self.max_last_images = proc_parameters["params"].get("max_last_images", 50)
            self.last_images = []

        elif self.pref_implem == "frame_diff":
            # If the pref_implem is "frame_diff", the results will be solely based on the previous image.
            self.prev_image = None

        elif self.pref_implem == "frame_diff_2":
            self.max_last_images = proc_parameters["params"].get("max_last_images", 100)
            self.last_images = []
            self.background = []
            self.counter_images = 0

        else:
            assert False, "[ERROR] Unknown implementation of BackgroundSubtractor: {}".format(self.pref_implem)

    def detect(self, frame: np.array) -> BBoxes2D:
        """Performs an inference using a background subtraction method on the given frame.

        Args:
            frame (np.array): The frame to infer detections from a background substractor.

        Returns:
            BBoxes2D: A set of 2D bounding boxes identifying the detected objects.
        """
        img_sub = None

        # Convert the frame to the gray-scale representation
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        start = default_timer()

        if self.pref_implem == "mean" or self.pref_implem == "median":
            self.last_images.append(frame_gray)
            if len(self.last_images) == self.max_last_images + 1:
                self.last_images.pop(0)

            # Obtain mean or median values of the previous images
            if self.pref_implem == "mean":
                background_image = np.mean(np.array(self.last_images), axis=0).astype(np.uint8)
            else:
                background_image = np.median(np.array(self.last_images), axis=0).astype(np.uint8)
            
            # Get the difference between the current image and the previous images (that should describes the background)
            foreground_image = cv2.absdiff(frame_gray, background_image)

            # Keep the most important difference, where the pixels has a higher value than self.intensity,
            # to remove the noise.
            img_sub = np.where(foreground_image > self.intensity, frame_gray, np.array([0], np.uint8))

        elif self.pref_implem == "frame_diff":
            # If no previous image, return an empty result.
            if self.prev_image is None:
                self.prev_image = frame_gray
                return BBoxes2D(0, np.array([]), np.array([]), np.array([]), frame.shape[1], frame.shape[0])
            
            # Otherwise, take the difference with the previous image.
            else:
                foreground_image = cv2.absdiff(self.prev_image, frame_gray)
                img_sub = np.where(foreground_image > self.intensity, frame_gray, np.array([0], np.uint8))
                self.prev_image = frame_gray

        elif self.pref_implem == "frame_diff_2":
            if self.background == []: #first iterations, no background
                self.last_images.append(frame_gray)
                if len(self.last_images) >= self.max_last_images:
                    self.background = np.median(np.array(self.last_images), axis=0).astype(np.uint8)
                    print("background computed")

            else: #background exists and self.last_images is full
                self.last_images.pop(0)
                self.last_images.append(frame_gray)
                """
                if self.counter_images > self.max_last_images: #recompute background
                    self.background = np.median(np.array(self.last_images), axis=0).astype(np.uint8)
                    print("background computed")
                    cv2.imshow("background", self.background)
                    self.counter_images = 0
                """
                #dynamic background
                self.background = np.median(np.array(self.last_images), axis=0).astype(np.uint8)
                cv2.imshow("background", self.background)

                frame_background_removed = cv2.absdiff(self.background, frame_gray)
                blur_frame_background_removed = cv2.blur(frame_background_removed, (10, 10))
                hist_item = cv2.calcHist([blur_frame_background_removed], [0], None, [256], [0, 256])
                binary_threshold = np.argwhere(np.abs(np.cumsum(hist_item)-0.50*np.cumsum(hist_item)[-1]) == np.min(np.abs(np.cumsum(hist_item)-0.50*np.cumsum(hist_item)[-1])))[0][0] + BINARY_THRESHOLD_ABOVE_50PC_OF_HISTOGRAM
                ret, img_sub = cv2.threshold(blur_frame_background_removed, binary_threshold, 255, cv2.THRESH_BINARY)  # Making the-background removed image binary
                cv2.imshow("blur_frame_background_removed", blur_frame_background_removed)
                
                self.counter_images+=1
                
                

        else:
            assert False, "[ERROR] Unknown implementation of BackgroundSubtractor: {}".format(self.pref_implem)

        bboxes = []
        # Find the contours of different objects that can be seen in the foreground image.
        contours = cv2.findContours(img_sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if img_sub is not None:
            for i in range(len(contours[0])):
                if contours[1][0, i, 3] == -1:
                    x, y, w, h = cv2.boundingRect(contours[0][i])
                    frame = cv2.rectangle(frame, (x, y), (x+w, y+h), (0,0,255), 1)
            cv2.imshow("contours with hierarchy", frame)
        for cont in contours[0]:
            poly = cv2.approxPolyDP(cont, self.contour_thresh, True)
            x, y, w, h = cv2.boundingRect(poly)
            bboxes.append([x, y, w, h])
        end = default_timer()

        return BBoxes2D(end-start, np.array(bboxes), np.zeros(len(bboxes)).astype(int),
                        np.ones(len(bboxes)), frame.shape[1], frame.shape[0])
