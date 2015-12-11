from ..xplane_constants import *
from .xplane_object import XPlaneObject

# Class: XPlaneLine
# A Line/Curve
# This class is not in use yet.
#
# Extends:
#   <XPlaneObject>
class XPlaneLine(XPlaneObject):
    def __init_(self,object):
        super(object)
        self.indices = [0,0]
        self.type = XPLANE_OBJECT_TYPE_LINE

        self.getWeight(9000)
