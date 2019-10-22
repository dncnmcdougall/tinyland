import renderer
import context

from pythonosc import udp_client

localIP     = "127.0.0.1"
localPort   = 20001

client = udp_client.SimpleUDPClient(localIP, localPort)


class Renderer(renderer.Renderer):

    def __init__(self, width, height):
        self.width = width
        self.height = height

    def setup(self):
        print('Running OSC renderer.')

    def toggle_fullscreen(self):
        pass

    def show_calibration_markers(self):
        pass

    def render(self, ctx):
        """Publish the draw context via Open Sound Controller protocol.

        Args:
          ctx (context.DrawingContext): A context with shapes to draw
        """
        for shape in ctx.shapes:
            if isinstance(shape, context.Rectangle):
                # message format: 'shape/name/x/y/w/h/'
                message = 'rectangle/{}/{}/{}/{}/{}/'.format(shape.name, shape.center.x, shape.center.y, shape.width, shape.height)
                print(message)
                client.send_message(message, 'nonsense') # args is nonsense because dumb nodejs can't parse the args arggg.
            # elif isinstance(shape, context.Circle):
            #     print("Circle at x: {} y: {}".format(shape.center.x, shape.center.y))
            # elif isinstance(shape, context.Text):
            #     print("Text at x: {} y: {} content: {}".format(shape.center.x, shape.center.y, shape.content))
            # elif isinstance(shape, context.Image):
            #     print("Image at x: {} y: {} content: {}".format(shape.center.x, shape.center.y, shape.filepath))
            
            