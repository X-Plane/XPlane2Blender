# File: xplane_anim.py
# Defines X-Plane animation data types.

import bpy
import math
import mathutils
import struct
from bpy.props import *
from collections import OrderedDict
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_ui import showError,showProgress

# Class: XPlaneAnimBone
# Animation primitive
class XPlaneAnimBone():

    # Constructor: __init__
    #
    # Parameters:
    #   xplaneObject - <XPlaneObject>
    #   parent - (optional) parent <XPlaneAnimBone>
    def __init__(self, xplaneObject = None, parent = None):
        self.xplaneObject = xplaneObject
        self.parent = parent
        self.children = []

    def write(self):
        # TODO: implement
        pass
