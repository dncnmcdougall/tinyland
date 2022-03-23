import cv2
from snapshot import ArucoDict

for i in range(1, 20):
    markerImage = cv2.aruco.drawMarker(ArucoDict, i, 200, 1)
    print(markerImage)
    cv2.imwrite("marker%s.png" % i, markerImage)
