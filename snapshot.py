import cv2.aruco as aruco
from collections import namedtuple
import numpy as np
import numpy.typing as npt

from typing import Dict, List, Union


# Convenience class that allows indexing as well as x and y attribute access
XYPoint = namedtuple("XYPoint", ["x", "y"])
Image = npt.NDArray[int]
Corners = npt.NDArray[int]

ArucoDict = aruco.getPredefinedDictionary(aruco.DICT_APRILTAG_36H11)

def transform(H, pt):
    pt1 = np.array([pt[0], pt[1], 1.])
    pt1 = pt1.reshape(3, 1)
    pt2 = np.dot(H, pt1)
    pt2 = pt2/pt2[2]
    return np.array([pt2[0,0], pt2[1,0]], dtype=pt.dtype)


class Marker:
    """Base class for any detected physical objects.

Args:
x (int): x coordinate of center point
y (int): y coordinate of center point
Attribiutes:
center (XYPoint): center point of marker
"""

    def __init__(self, x, y):
        self.center = XYPoint(x, y)


class ArucoMarker(Marker):
    def __init__(self, id, corners, raw_corners):
        [center_x, center_y] = np.median([np.array(corners[0,0]), np.array(corners[0,3])], axis=0)
        super().__init__(center_x, center_y)
        self.id = int(id)
        self.tl = XYPoint(*corners[0,0])
        self.tr = XYPoint(*corners[0,1])
        self.bl = XYPoint(*corners[0,2])
        self.br = XYPoint(*corners[0,3])
        self.corners = corners
        self.raw_corners = raw_corners
        self.rotation = np.degrees(np.arctan((self.tl.y - self.bl.y) / (self.tl.x - self.bl.x)))


class Snapshot:
    """Current state of physical markers on the landscape.

Processes an image array and pulls out marker information for the user.

Args:
image (numpy.ndarray): A W x H x 3 matrix representing the image
to process.
Attributes:
markers (dict<int, list<ArucoMarker>>): maps marker id to list of marker
objects that match that id.
"""

    def __init__(self, image, homography, on_image=False):
        self.image = image
        self.markers = self.detect_aruco(homography, on_image)

    def detect_aruco(self, H, on_image) -> Dict[int, List[ArucoMarker]]:
        # Aruco - Find markers
        aruco_markers = aruco.detectMarkers(self.image, ArucoDict)
        corners = aruco_markers[0]
        ids = aruco_markers[1]
        markers:Dict[int, List[ArucoMarker]] = {}
        if ids is None:
            return markers
        for aruco_id, corner in zip(ids, corners):
            id_key = int(aruco_id[0])
            [tl, tr, br, bl] = corner[0]
            markers[id_key] = markers.get(id_key, [])
            if on_image:
                markers[id_key].append(ArucoMarker(id_key, 
                    np.array([[tl,tr,br,bl]]),
                    np.array([[transform(H,tl), transform(H,tr), 
                        transform(H,br), transform(H,bl)]])
                    )
                )
            else:
                markers[id_key].append(ArucoMarker(id_key, 
                    np.array([[transform(H,tl), transform(H,tr), 
                        transform(H,br), transform(H,bl)]]),
                    np.array([[tl,tr,br,bl]])
                    )
                )
        return markers
