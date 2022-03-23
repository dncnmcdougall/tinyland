import cv2
import importlib
import numpy as np
import toml
import sys
import time

import context
import snapshot

from snapshot import Corners, Image
from typing import Dict, Any, Optional, List
import numpy.typing as npt


def squaritude(c):
    _, _, w, h = cv2.boundingRect(c)
    if h > w:
        aspect = w / h
    else:
        aspect = h / w
    rectitude = cv2.contourArea(c) / (w * h)
    return aspect * rectitude


class Landscape:
    def __init__(self):
        self.camera:cv2.VideoCapture = None
        self.projector:Dict[str,Any] = {}
        self.homography = np.eye(3)

    def load_config(self, config_file):
        self.projector = toml.load(config_file)
        print(self.projector)

    def camera_to_projector_space(self, image):
        for i in range(5):
            try:
                image = cv2.warpPerspective(
                    image,
                    self.homography,
                    (
                        self.projector["PROJECTOR_WIDTH"],
                        self.projector["PROJECTOR_HEIGHT"],
                    ),
                )
                break
            except cv2.error:
                print("Warp perspective failed. Attempt #%s" % (i + 1))
                time.sleep(1)
                if i == 5:
                    print("Warp perspective failed for good 😭. Exiting early.")
                    sys.exit()

        if self.projector["FLIP_PROJECTION"]:
            image = cv2.flip(image, -1)
        return image

    def get_raw_frame(self):
        frame = self.camera.read()[1]

        # If we're at the end of the video, rewind. This comes into play when we're using a video file as input, as for testing offline.
        if frame is None and not self.projector["USE_CAMERA"]:
            self.camera.set(cv2.CAP_PROP_POS_MSEC, 0)
            frame = self.camera.read()[1]

        return frame

    def find_corners(self, frame):
        PROJECTOR_WIDTH = self.projector["PROJECTOR_WIDTH"]
        PROJECTOR_HEIGHT = self.projector["PROJECTOR_HEIGHT"]

        # Search for our calibration markers
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rv, frame_thresh = cv2.threshold(frame_gray, 185, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(frame_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        hierarchy = hierarchy[0]

        markers = []
        for i in range(len(contours)):
            # opencv contour hierarchy: [Next, Previous, First_Child, Parent]
            # https://docs.opencv.org/3.4/d9/d8b/tutorial_py_contours_hierarchy.html
            child_idx = hierarchy[i][2]
            next_child_idx = hierarchy[child_idx][1]

            # Look for contours with exactly one child of plausible size
            if child_idx != -1 and next_child_idx == -1:
                area = cv2.contourArea(contours[i])
                child_area = cv2.contourArea(contours[child_idx])

                if (
                    squaritude(contours[i]) > 0.75
                    and squaritude(contours[child_idx]) > 0.5
                    and child_area
                    and area / child_area < 10
                    and area / child_area > 2
                ):
                    markers.append(i)

        if len(markers) == 4:
            # Assume we've found our markers - take a convex hull and check that it's a quadrilateral
            all_points = []
            for c in [contours[i] for i in markers]:
                all_points.extend(c)
            boundary = cv2.convexHull(np.array(all_points))
            boundary = cv2.approxPolyDP(boundary, 25, True)
            # Not sure why this is necessary
            boundary = boundary[:, 0]
            if len(boundary) == 4:
                # This has to be the dumbest possible way to sort four points clockwise from top left
                point1 = [p for p in boundary if p[0] < PROJECTOR_WIDTH / 2 and p[1] < PROJECTOR_HEIGHT / 2]
                point2 = [p for p in boundary if p[0] > PROJECTOR_WIDTH / 2 and p[1] < PROJECTOR_HEIGHT / 2]
                point3 = [p for p in boundary if p[0] > PROJECTOR_WIDTH / 2 and p[1] > PROJECTOR_HEIGHT / 2]
                point4 = [p for p in boundary if p[0] < PROJECTOR_WIDTH / 2 and p[1] > PROJECTOR_HEIGHT / 2]
                if len(point1) == 1 and len(point2) == 1 and len(point3) == 1 and len(point4) == 1:
                    final_corners:Corners = np.array([point1[:], point2[:], point3[:], point4[:]])
                    # It's slightly hacky for us to mix up our state and our config in this way.
                    return final_corners
        return None

    def initialize_camera(self):
        if self.projector["USE_CAMERA"]:
            try:
                # Grab camera from config
                self.camera = cv2.VideoCapture(self.projector["VIDEO_CAPTURE_INDEX"])
            except KeyError:
                # If camera doesn't exist in config, prompt user to select one of the connected cameras.
                self.camera = select_camera()
            if "VIDEO_RESOLUTION" in self.projector:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.projector["VIDEO_RESOLUTION"][0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.projector["VIDEO_RESOLUTION"][1])
            if "VIDEO_FPS" in self.projector:
                self.camera.set(cv2.CAP_PROP_FPS, self.projector["VIDEO_FPS"])
            print("== final resolution ==")
            print("width: %s" % self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            print("height: %s" % self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print("FPS: %s" % self.camera.get(cv2.CAP_PROP_FPS))
        else:
            self.camera = cv2.VideoCapture(self.projector["VIDEO_FILE_PATH"])

    def get_snapshot(self):
        """Process self.camera image into a Snapshot.

        Returns:
          snap (snapshot.Snapshot): snapshot generated from self.camera image.
        """
        SRC_CORNERS:Corners = np.array(self.projector["SRC_CORNERS"])
        DEST_CORNERS:Corners = np.array(self.projector["DEST_CORNERS"])
        frame = self.get_raw_frame()
        if self.projector.get("CALIBRATE"):
            corners = self.find_corners(frame)
            if corners is not None:
                SRC_CORNERS = corners
                self.projector["SRC_CORNERS"] = corners
                self.projector["CALIBRATE"] = False
        self.homography, status = cv2.findHomography(SRC_CORNERS, DEST_CORNERS)

        if self.projector["IDENTIFY_ON_VIDEO"]:
            print('Identify on frame')
            snap = snapshot.Snapshot(frame, self.homography, on_image=False)
        image = self.camera_to_projector_space(frame)
        if not self.projector["IDENTIFY_ON_VIDEO"]:
            print('Identify on image')
            snap = snapshot.Snapshot(image, np.linalg.inv(self.homography), on_image=True)

        return snap, image, frame


def printXY(_a, x, y, _b, _c):
    print("x: ", x)
    print("y: ", y)


def get_key():
    key = cv2.waitKey(1)
    if key == -1:
        return None
    return chr(key & 0xFF)


def handle_keyevents(l, r):
    key = get_key()
    if key == "q":
        sys.exit()
    if key == "f":
        r.toggle_fullscreen()
    if key == "c":
        l.projector["CALIBRATE"] = True


def select_camera():
    """Get OpenCV VideoCapture camera. Prompt user if multiple cameras found.

    Returns:
      cv2.VideoCapture instance of the selected camera.
    """
    # Get list of all connected cameras
    cameras:List[cv2.VideoCapture] = []
    while True:
        cap = cv2.VideoCapture(len(cameras))
        _, frame = cap.read()
        if frame is not None:
            print("%s: %s" % (len(cameras), frame.shape))
            print(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            cameras.append(cap)
        else:
            break

    if len(cameras) == 0:
        print("No VideoCapture devices detected!")
        return None
    elif len(cameras) == 1:
        print("Found one camera, so using that one.")
        return cameras[0]
    else:
        # Open user flow to select camera
        print("Press n and p to cycle through connected cameras. Press s to select.")
        SELECT_CAM_WINDOW = "Select Camera"
        cv2.namedWindow(SELECT_CAM_WINDOW)
        cur_index = 0
        while True:
            # Handle keypress events
            key = cv2.waitKey(1)
            if key & 0xFF == ord("s"):
                cv2.destroyWindow(SELECT_CAM_WINDOW)
                print("selected camera %s" % cur_index)
                return cameras[cur_index]
            if key & 0xFF == ord("n"):
                cur_index = (cur_index - 1) % len(cameras)
            if key & 0xFF == ord("p"):
                cur_index = (cur_index - 1) % len(cameras)

            cv2.imshow(SELECT_CAM_WINDOW, cameras[cur_index].read()[1])


def run(render_ctx, render_direct):
    """Run a user's app function that represents a Tinyland application.

    This function runs a setup procedure and then the app loop:
    Setup:
      1. Set up the Landscape. The Landscape grabs images from the camera and
         processes them into snapshots for the app function
      2. Set up the Renderer. Import the desired rendering module and create
         the Renderer.
    App Loop:
      1. Handle top-level Tinyland keyevent like calibration control and quit.
      2. Grab a Snapshot from the Landscape.
      3. Either:
          a. display calibration image
          b. create DrawingContext and run app function with Snapshot and Context.
      4. Repeat.

    Args:
      app: a function that takes a Snapshot and a Context, and writes shapes to
        the context using its built in methods.
    """
    # Setup
    l = Landscape()
    l.load_config("./config.toml")
    cv2.namedWindow("Tinycam")
    cv2.setMouseCallback("Tinycam", printXY)  # Useful when setting projection config.
    print("Initialising camera... ", end=None)
    l.initialize_camera()
    print("Done")

    render_config = l.projector.get("RENDERER", "CV2")
    render_mod = importlib.import_module(f"{render_config.lower()}_renderer")
    # TODO: check that render_mod contains subclass definition of Renderer ABC
    r = render_mod.Renderer(l.projector["PROJECTOR_WIDTH"], l.projector["PROJECTOR_HEIGHT"])
    r.setup()

    # App loop
    while True:

        handle_keyevents(l, r)
        snap, image, frame = l.get_snapshot()

        if image is not None:
            SRC_CORNERS:Corners = np.array(l.projector["SRC_CORNERS"])
            debug:Image = np.copy(frame)
            items = snap.markers.items()
            if items:
                markers = [m for i in items for m in i[1]]
                ids:npt.NDArray[int] = np.array([m.id for m in markers])
                corners = [m.raw_corners for m in markers]
                cv2.aruco.drawDetectedMarkers(debug, corners, ids)
            debug = cv2.polylines(debug, pts=[SRC_CORNERS.astype(int)], isClosed=True, color=(255,255,255))

            cv2.imshow("Tinycam", debug)

        if l.projector.get("CALIBRATE"):
            r.show_calibration_markers()
        else:
            ctx = context.DrawingContext(l.projector["PROJECTOR_WIDTH"], l.projector["PROJECTOR_HEIGHT"])

            # Run the user defined app
            if render_direct is not None:
                image = render_direct(snap, image)

            render_ctx(snap, ctx)
            r.render(ctx, image)
