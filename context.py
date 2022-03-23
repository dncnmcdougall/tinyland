from collections import namedtuple

from typing import List


# Convenience class that allows indexing as well as x and y attribute access
XYPoint = namedtuple("XYPoint", ["x", "y"])
Size = namedtuple("Size", ["width", "height"])
Colour = namedtuple("Colour", ["r", "g", "b"])


# BGR color values
BLACK = Colour(0, 0, 0)
WHITE = Colour(255, 255, 255)
BLUE = Colour(255, 0, 0)
GREEN = Colour(0, 255, 0)
RED = Colour(0, 0, 255)
CYAN = Colour(255, 255, 0)
MAGENTA = Colour(255, 0, 255)
YELLOW = Colour(0, 255, 255)


class Shape:
    """Base class for shapes to draw on the landscape."""

    def __init__(self, x:int, y:int, color:Colour):
        self.center = XYPoint(x, y)
        self.color = color


class Circle(Shape):
    def __init__(self, x:int, y:int, radius:int, color:Colour):
        super().__init__(x, y, color)
        self.radius = radius


class Rectangle(Shape):
    def __init__(self, x:int, y:int, width:int, height:int, rotation:float, color:Colour):
        super().__init__(x, y, color)
        self.width = width
        self.height = height
        self.rotation = rotation


class Text(Shape):
    def __init__(self, x:int, y:int, content:str, color:Colour, size:Size):
        super().__init__(x, y, color)
        self.content = str(content)
        self.size = size


class Image(Shape):
    def __init__(self, filepath, x, y, width, height):
        super().__init__(x, y, color=BLACK)
        self.width = width
        self.height = height
        self.filepath = filepath


class DrawingContext:
    """Context with all information to project a drawing onto the landscape.

    Args:
        width (int): width of the drawing
        height (int): height of the drawing
    Attributes:
        width (int): width of the drawing
        height (int): height of the drawing
        shapes (list<Shape>): shapes to draw
    """

    def __init__(self, width:int, height:int):
        self.width = width
        self.height = height
        self.shapes:List[Shape] = []

    def rect(self, x, y, width, height, rotation=0, color=WHITE):
        self.shapes.append(Rectangle(x, y, width, height, rotation, color))

    def circle(self, x, y, radius, color=WHITE):
        self.shapes.append(Circle(x, y, radius, color))

    def text(self, x, y, content, color=WHITE, size=2):
        self.shapes.append(Text(x, y, content, color, size))

    def image(self, filepath, x, y, width, height):
        self.shapes.append(Image(filepath, x, y, width, height))
