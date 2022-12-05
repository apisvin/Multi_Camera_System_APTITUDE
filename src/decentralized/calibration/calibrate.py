from calibration.aruco import *
import cv2
import numpy as np
from calib3d import Point3D, Point2D
import pickle

def find_intersection(C, d, P, n):
    """
        Finds the intersection between a line and a plane.
        Arguments:
            C - a Point3D of a point on the line
            d - a non-normalized direction-vector of the line
            P - a Point3D on the plane
            n - the normal vector of the plane
        Returns the Point3D at the intersection between the line and the plane.
    """
    d = d.reshape((3,))
    P = P.reshape((3,))
    C = C.reshape((3,))
    n = n.reshape((3,))

    dotProduct = np.dot(n, d)
    w = C - P
    si = -np.dot(n, w) / dotProduct
    point3D = Point3D(w + si * d + P)
    assert isinstance(point3D, Point3D) 
    return point3D


class Calib():
    # The __init__ function is the constructor of Calib.
    # It is called each time we create a 'Calib' object.
    # The '*' in the arguments force to use keywords arguments instead of nameless values
    # The '**_' will be usefull later... it's for additional keywords arguments that are ignored here.
    def __init__(self, width, height, T, R, K, kc, **_):
        """
        Calib class is used to create a function that project 2D coordinate on the plane of the camera 
        on a 3D frame in the real world and inversely.
        Args : 
            width : width in pixel of the image frame
            height : heigth in pixel of the image frame
            T : translation matrix 
            R : rotation matrix
            K : intrinsic camera matrix 
            kc : distorsion coefficients
        """
        self.width = width
        self.height = height
        self.T = T
        self.R = R
        self.K = K
        self.P = K @ np.hstack((R, T))
        self.Pinv = np.linalg.pinv(self.P)
        self.Kinv = np.linalg.pinv(self.K)
        self.kc=kc
        
    def project_3D_to_2D(self, points3D: Point3D):
        """
            Using the calib object, project 3D points in the 2D image space.
            Arguments:
                points3D   - the 3D points to be projected
            Returns:
                The points in the 2D image space on which points3D are projected by calib
        """
        point2D = Point2D(self.P @ points3D.H)
        assert isinstance(point2D, Point2D), "Output of this method should be a Point2D object"
        return self.distort(point2D)
    
    def project_2D_to_3D(self, points2D: Point2D, Z: float):
        """
            Using the calib object, project 2D points in the 3D image space.
            Arguments:
                point2D    - the 2D points to be projected
                Z          - the Z coordinate of the 3D points
            Returns:
                The points in the 3D world for which the z=Z and that projects on points2D
        """
        points2D = self.rectify(points2D)
        C = Point3D(self.R.T @ self.T * -1)  # (0,0,0) of camera referential in global referential
        P3D = Point3D(self.Pinv @ points2D.H) # a 3D point 
        d = P3D - C
        P = Point3D(0,0,Z)
        n = np.array([[0,0,1]]).T
        points = find_intersection(C, d, P, n)
        assert isinstance(points, Point3D), "Output of this method should be a Point3D object"
        return points

    def distort(self, point2D):
        if np.any(self.kc):
            rad1, rad2, tan1, tan2, rad3 = self.kc.flatten()
            # Convert image coordinates to camera coordinates (with z=1 which is the projection plane)!
            point2D = Point2D(self.Kinv @ point2D.H)
            r2 = point2D.x*point2D.x + point2D.y*point2D.y
            delta = 1 + rad1*r2 + rad2*r2*r2 + rad3*r2*r2*r2    #radial component
            dx = np.array([[
                2*tan1*point2D.x*point2D.y + tan2*(r2 + 2*point2D.x*point2D.x),
                2*tan2*point2D.x*point2D.y + tan1*(r2 + 2*point2D.y*point2D.y)
            ]]).T                                               #tangential component
            point2D = Point2D(point2D*delta + dx)
            # Convert camera coordinates to pixel coordinates !
            point2D = Point2D(self.K @ point2D.H)
        return point2D

    def rectify(self, point2D): #to be modified
        if np.any(self.kc):
            rad1, rad2, tan1, tan2, rad3 = self.kc.flatten()

            point2D = Point2D(self.Kinv @ point2D.H)

            r2 = point2D.x*point2D.x + point2D.y*point2D.y
            rad_comp = 1 + rad1*r2 + rad2*r2*r2 + rad3*r2*r2*r2

            #with the approximation
            tang_comp_x = 2*tan1*point2D.x*point2D.y + tan2 * (r2 + 2*point2D.x**2)
            tang_comp_y = 2*tan2*point2D.x*point2D.y + tan1 * (r2 + 2*point2D.y**2)

            xu = (point2D.x - tang_comp_x)/rad_comp
            yu = (point2D.y - tang_comp_y)/rad_comp

            point2D = Point2D(self.K @ Point2D(xu,yu).H)
        return point2D
        
    @classmethod
    def load(cls, filename):
        """
            Loads a calib object from a file (using the pickle library)
            Argument:
                filename   - the file that stores the calib object
            Returns:
                The calib object      
        """
        with open(filename, "rb") as f:
            return cls(**pickle.load(f))
    
    @property
    def dict(self):
        """
            Gets a dictionnary representing the calib object (allowing easier serialization)
        """
        return {k: getattr(self,k) for k in self.__dict__.keys()}

    def dump(self, filename):
        """
            Saves the current calib object to a file (using the pickle library)
            Argument:
                filename    - the file that will store the calib object
        """
        with open(filename, "wb") as f:
            pickle.dump(self.dict, f)





def find_calib(image, aruco_3D, ids_3D, nb_aruco=25, verbose=False):
    """
        input : 
            - image :       filename of the image containing aruco symbol
            - aruco_3D :    array of 3D coordinates of aruco
            - ids_3D :      ids of each aruco in corresponding order
            - nb_aruco :    number of aruco on image
        output : 
            - calib :       calib object 
            - points2D :    2D-coordinates of aruco symbol on image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape

    # Find 2D coordinate of arucos on image
    (aruco_2D, ids_2D, _) = detect_aruco(image, nb_aruco)

    #match 3D and 2D coordinate knowing ids
    (aruco_3D, aruco_2D) = match_aruco(aruco_3D, ids_3D, aruco_2D, ids_2D)

    if verbose:
        print("find_calib")
        print("aruco_2D = ", aruco_2D)

        print("aruco_3D = ", aruco_3D)
    
    # Find calibration parameters using the 3D points and their position in 2D
    # (the rotation matrix must be converted because we don't use the same convention as cv2)
    # kc is not used currently, you'll see later what it does.
    _, K, kc, r, t = cv2.calibrateCamera([aruco_3D], [aruco_2D], (width, height), None, None)
    
    # retrive `T` and `R` that follow our convention using `t` and `r` output by the `cv2` function
    T = t[0]
    R = cv2.Rodrigues(r[0])[0]
    
    if verbose:
        print("kc={}".format(kc))
        print("K={}".format(K))
        print("R={}".format(R))
        print("T={}".format(T))
    
    calib = Calib(width=width, height=height, T=T, R=R, K=K, kc=kc)
        
    return calib, aruco_2D

def draw_repere(image, calib, length=1):
    """
        inputs : 
            - image : original image
            - calib : Calib class corresponding to the image 
            - length : length of each axis 
        output : 
            - image : original image modified with repere 
    """
    origine =   calib.project_3D_to_2D(Point3D(0,0,0)).astype("int").reshape(2,)
    x =         calib.project_3D_to_2D(Point3D(length,0,0)).astype("int").reshape(2,)
    y =         calib.project_3D_to_2D(Point3D(0,length,0)).astype("int").reshape(2,)
    z =         calib.project_3D_to_2D(Point3D(0,0,length)).astype("int").reshape(2,)

    image = cv2.line(image, origine, x, (255, 0, 0), 4)
    image = cv2.putText(image, "x", x, cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 0, 0), 2)
    image = cv2.line(image, origine, y, (0, 100, 150), 4)
    image = cv2.putText(image, "y", y, cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 100, 150), 2)
    image = cv2.line(image, origine, z, (0, 75, 0), 4)
    image = cv2.putText(image, "z", z, cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 75, 0), 2)
    
    
    return image


def create_pickle():
    """
    From image_calibration.png containing 9 aruco markers, construct Calib class and store it in calib.pickle
    """
    image = cv2.imread('/home/pi/Multi_Camera_System_APTITUDE/src/local_data/image_calibration.png')

    aruco_3D = np.array([[0.,0.,0.],
                        [100.,0.,0.],
                        [0.,100.,0.],
                        [-100.,0.,0.],
                        [0.,-100.,0.],
                        [100.,100.,0.],
                        [-100.,100.,0.],
                        [-100.,-100.,0.],
                        [100.,-100.,0.]], dtype='float32')
    ids_3D = np.array([0,10,12,14,16,18,20,22,24])
    (calib, _) = find_calib(image, aruco_3D, ids_3D, nb_aruco=9, verbose=False)

    calib.dump("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/calib.pickle")
    #calib = Calib.load("_.pickle")
    
    image_repere = draw_repere(image, calib, 50)
    cv2.imwrite("/home/pi/Multi_Camera_System_APTITUDE/src/local_data/image_repere.png", image_repere)

def create_repere():

    image = cv2.imread('/home/pi/TFE_data/images_labo/calibration.png')

    calib = Calib.load("/home/pi/TFE_data/pickle/calib.pickle")

    image_repere = draw_repere(image, calib, length=50)

    cv2.imwrite("/home/pi/TFE_dataimages_labo/repere.png", image_repere)

    return calib

#create_pickle("agent1")
#create_repere("agent1")
def test():
    image = cv2.imread('images_labo/agent2_repere.png')
    print(image.shape)
    x = image.shape[0]//8
    y = image.shape[1]//4

    calib = Calib.load("pickle/calib_agent2.pickle")

    image = cv2.circle(image, (y,x), 8, (0, 0, 255), -1)
    cv2.imwrite("test_calib.png", image)

    print(calib.project_2D_to_3D(Point2D(y,x), Z=0))

#test()
#create_pickle("agent1")
#create_repere("agent2")




