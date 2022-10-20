import numpy as np
import cv2
from calib3d import Point3D, Point2D


arucoDict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)    #The ArUco dictionary we are using. 50 unique aruco with 4x4 pixels

def detect_aruco(image, nb_aruco):
    #(source : https://www.pyimagesearch.com/2020/12/21/detecting-aruco-markers-with-opencv-and-python/)
    """
        input : 
            image : The input image that we want to detect ArUco markers in
        
        output : 
            topLeft : the position (x,y) of the top left corner of all detected aruco
            ids : number associated to the aruco
            image : modified image that contain marks representing the upper left corner of aruco 
    """
    arucoParams = cv2.aruco.DetectorParameters_create() #The ArUco parameters used for detection (unless you have a good reason to modify the parameters, the default parameters returned by cv2.aruco.DetectorParameters_create are typically sufficient)
    (corners, ids, rejected) = cv2.aruco.detectMarkers(image, arucoDict,parameters=arucoParams)
    #corners: A list containing the (x, y)-coordinates of our detected ArUco markers
    #ids : The ArUco IDs of the detected markers


    topLeft = np.zeros((nb_aruco, 1, 2), dtype='float32') #array containing all the top left corner position
    id_aruco = np.zeros((nb_aruco,))
    i=0
    # detect all aruco
    if len(corners) == nb_aruco:
        # flatten the ArUco IDs list
        ids = ids.flatten()
        # loop over the detected ArUCo corners
        for (markerCorner, markerID) in zip(corners, ids):
            # extract the marker corners (which are always returned in
            # top-left, top-right, bottom-right, and bottom-left order)
            corners = markerCorner.reshape((4, 2))
            #(topLeft, topRight, bottomRight, bottomLeft) = corners
            topLeft[i] = corners[0]
            id_aruco[i] = markerID
            i+=1
            position = (int(corners[0][0]), int(corners[0][1]))
            positionText = (int(corners[0][0]), int(corners[0][1])-15)
            image = cv2.circle(image, position, 12, (0, 0, 255), -1)
            image = cv2.putText(image, str(markerID), positionText, cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 2)
        

    return (topLeft, ids, image)


def generate_aruco(nb_aruco, destination):
    """
        input : 
            nb_aruco : number of aruco figure to generate
            destination : path to the destination folder where aruco are located
        output : 

    """
    #SOURCE / https://www.pyimagesearch.com/2020/12/14/generating-aruco-markers-with-opencv-and-python/
    arucoParams = cv2.aruco.DetectorParameters_create()
    position = np.zeros((nb_aruco,3))

    for i in range(nb_aruco):
        position[i,] = (i//np.sqrt(nb_aruco),i%np.sqrt(nb_aruco),0)
        tag = np.zeros((300, 300, 1), dtype="uint8")                    #create buffer for aruco (300x300)
        cv2.aruco.drawMarker(arucoDict, i, 300, tag, 1)                 #aruco number = 3
        tag = cv2.putText(tag, str(i), (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.imwrite(destination+str(i)+".png", tag)


def match_aruco(aruco_3D, ids_3D, aruco_2D, ids_2D):
    """
    inputs : 
        - aruco_3D = listes des positions dans l'espace 3D
        - ids_3D = listes des numeros correspondant aux aruco_3D
        - aruco_2D = listes des positions dans l'espace 2D
        - ids_2D = listes des numeros correspondant aux aruco_2D
    outputs : 
        - aruco_3D = listes des positions dans l'espace 3D
        - aruco_2D = listes des positions dans l'espace 2D dans le meme ordre que aruco_3D
    """
    if(np.array_equal(np.sort(ids_3D), np.sort(ids_2D))):
        index_aruco_3D = np.argsort(ids_3D)
        index_aruco_2D = np.argsort(ids_2D)
        aruco_3D = aruco_3D[index_aruco_3D]
        aruco_2D = aruco_2D[index_aruco_2D]

    return (aruco_3D, aruco_2D)

def create_3D_position(nb_aruco, length):
    """
        inputs :
            nb_aruco : number of aruco symbol that can be seen by camera 
            length : total length of the square formed by aruco symbol
        output : 
            position : array of 3D positions of each aruco symbol 
    """
    position = np.zeros((nb_aruco,3))
    for i in range(nb_aruco):
        position[i,] = ( length/(i//np.sqrt(nb_aruco)+1), length/(i%np.sqrt(nb_aruco)), 0 )
    return position


def test():
    generate_aruco(25, "aruco_image/")

    image = cv2.imread('test.png')

    (topLeft, ids, newimage) = detect_aruco(image, 4)

    cv2.imwrite("aruco_detetcted.png", newimage)

    x = np.array([0, 1])
    y = np.array([0, 1])
    z = np.array([0, 0])
    aruco_3D = Point3D(x,y,z)
    print(aruco_3D)
    ids_3D = np.array([12,22])

    x = np.array([150, 250])
    y = np.array([150, 250])
    aruco_2D = Point2D(x,y)
    print(aruco_2D)
    ids_2D = np.array([22,12])

    print(match_aruco(aruco_3D, ids_3D, aruco_2D, ids_2D))

#test()
 