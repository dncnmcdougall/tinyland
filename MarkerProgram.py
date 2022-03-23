import cv2
import numpy as np
from typing import Dict, List
import numpy.typing as npt

from context import DrawingContext, XYPoint, Size, WHITE, GREEN, RED
from snapshot import Corners, Image


class MarkerProgram:
    def __init__(self, marker_width:int, size:Size, marker_position:XYPoint):
        self.marker_width = marker_width
        self.size = size
        self.marker_position = marker_position

        self.tl=XYPoint(int(self.marker_position.x*self.size.width), int(self.marker_position.y*self.size.height))
        self.br=XYPoint(int(self.tl.x+self.marker_width), int(self.tl.y+self.marker_width))
        self.tr=XYPoint(int(self.br.x), int(self.tl.y))
        self.bl=XYPoint(int(self.tl.x), int(self.br.y))
        self.corners:Corners = np.array([[self.tl,self.tr,self.br,self.bl]])

    def initialiseImage(self):
        self.image:Image = np.zeros((self.size.height, self.size.width, 3), np.uint8)

    def finaliseImage(self, marker_corners:Corners, output_size:Size) -> Image:

        homography, status = cv2.findHomography(self.corners, marker_corners, cv2.RANSAC)

        return cv2.warpPerspective(self.image, homography, output_size)

    def render(self, id:int) -> None:
        pass

class UnknownMarker(MarkerProgram):
    def __init__(self):
        super().__init__(100, Size(100,100), XYPoint(0,0))

    def render(self, id:int) -> None:
        self.image = cv2.rectangle(self.image, (0,1), (self.size.width-1, self.size.height-1), RED, thickness=cv2.FILLED)
        self.image = cv2.putText( self.image,
            str(id), self.bl,
            cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 3, cv2.LINE_AA,)

class RectangleMarker(MarkerProgram):
    def __init__(self):
        super().__init__(25, Size(100,50), XYPoint(0.25,0.25))

    def render(self, id:int) -> None:
        self.image = cv2.rectangle(self.image, (1,1), (self.size.width-1, self.size.height-1), WHITE)
        self.image = cv2.rectangle(self.image, self.tl, self.br, GREEN)

