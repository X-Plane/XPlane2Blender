from .xplane_object import XPlaneObject

# Class: XPlaneLight
# A Light
#
# Extends:
#   <XPlaneObject>
class XPlaneLight(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this light.

    # Property: color
    # list - [r,g,b] Color taken from the original Blender light. Can change depending on <lightType>.

    # Property: energy
    # float - Energy taken from Blender light.

    # Property: lightType
    # string - Type of the light taken from <XPlaneLampSettings>.

    # Property: size
    # float - Size of the light taken from <XPlaneLampSettings>.

    # Property: lightName
    # string - Name of the light taken from <XPlaneLampSettings>.

    # Property: params
    # string - Parameters taken from <XPlaneLampSettings>.

    # Property: dataref
    # string - Dataref path taken from <XPlaneLampSettings>.

    # Constructor: __init__
    #
    # Parameters:
    #   object - A Blender object
    def __init__(self,object):
        super(XPlaneLight,self).__init__(object)
        self.indices = [0,0]
        self.color = [object.data.color[0],object.data.color[1],object.data.color[2]]
        self.energy = object.data.energy
        self.type = 'LIGHT'
        self.lightType = object.data.xplane.type
        self.size = object.data.xplane.size
        self.lightName = object.data.xplane.name
        self.params = object.data.xplane.params
        self.uv = object.data.xplane.uv
        self.dataref = object.data.xplane.dataref

        # change color according to type
        if self.lightType=='flashing':
            self.color[0] = -self.color[0]
        elif self.lightType=='pulsing':
            self.color[0] = 9.9
            self.color[1] = 9.9
            self.color[2] = 9.9
        elif self.lightType=='strobe':
            self.color[0] = 9.8
            self.color[1] = 9.8
            self.color[2] = 9.8
        elif self.lightType=='traffic':
            self.color[0] = 9.7
            self.color[1] = 9.7
            self.color[2] = 9.7

        self.getCustomAttributes()
        self.getAnimAttributes()

        self.getWeight()

        self.getCoordinates()
        self.getAnimations()
