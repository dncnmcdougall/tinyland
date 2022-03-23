import tinyland
from MarkerProgram import UnknownMarker, RectangleMarker, MarkerProgram
import numpy as np

from context import Size

unknown = UnknownMarker()
programs = {
4: RectangleMarker()
}

unknown.initialiseImage();
for program in programs.items():
    program[1].initialiseImage()

def run(snap, image):
    [rows, cols, _] = image.shape
    # Draw shapes to context based on data in snapshot
    for id, markers in snap.markers.items():
        program:MarkerProgram = unknown
        if id in programs:
            program = programs[id]
        program.render(id)
        for marker in markers:
            prog_image = program.finaliseImage(marker.corners, Size(cols, rows))
            prog_sum =( prog_image[:,:,0] + prog_image[:,:,1] + prog_image[:,:,2])>0
            image = np.where( np.stack([prog_sum,prog_sum, prog_sum], axis=-1), prog_image, image)

    return image

def app(snap, ctx):
    # Draw shapes to context based on data in snapshot
    for id, markers in snap.markers.items():
        for marker in markers:
            ctx.rect(marker.center.x, marker.center.y, 5, 5)
            ctx.text(marker.center.x, marker.center.y + 10, str(marker.id))
    pass


if __name__ == "__main__":

    tinyland.run(app, run)
