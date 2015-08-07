import bpy
from ..xplane_config import getDebug
from ..xplane_helpers import *
from .xplane_attributes import XPlaneAttributes
from .xplane_attribute import XPlaneAttribute

# Class: XPlaneObject
# A basic object
#
# Sublcasses:
#   <XPlaneBone>
#   <XPlaneArmature>
#   <XPlaneLight>
#   <XPlaneLine>
#   <XPlanePrimitive>
class XPlaneObject():
    # Property: blenderObject
    # The blender object this <XPlaneObject> refers to.

    # Property: name
    # string - Name of this object. The same as the <object> name.

    # Property: type
    # string - Type of the object. Mostly the same as the <object> type.

    # Property: datarefs
    # dict - The keys are the dataref paths and the values are references to <XPlaneDatarefs>.

    # Property: bakeMatrix
    # Matrix - The matrix this object was baked with. See <XPlaneMesh.getBakeMatrix> for more information.

    # Property: location
    # list - [x,y,z] With world location

    # Property: angle
    # list - [x,y,z] With world angle

    # Property: scale
    # list - [x,y,z] With world scale

    # Property: locationLocal
    # list - [x,y,z] With local location

    # Property: angleLocal
    # list - [x,y,z] With local angle

    # Property: scaleLocal
    # list - [x,y,z] With local scale

    # Property: vectors
    # Vector of vectors - (vx,vy,vz) With orientation of each rotational axis.

    # Property: id
    # int - A unique id

    # Property: weight
    # int - (default = 0) The object weight. Higher weight will write the object later in OBJ.

    # Property: lod
    # vector - (False,False,False) with levels of details this object is in

    # Constructor: __init__
    #
    # Parameters:
    #   blenderObject - A Blender object
    def __init__(self, blenderObject):
        self.type = ''
        self.blenderObject = blenderObject
        self.xplaneBone = None
        self.name = blenderObject.name
        self.datarefs = {}
        self.bakeMatrix = None
        self.id = int(blenderObject.as_pointer())
        self.attributes = XPlaneAttributes()
        self.cockpitAttributes = XPlaneAttributes()
        self.animAttributes = XPlaneAttributes()
        self.conditions = []

        if hasattr(self.blenderObject.xplane, 'lod'):
            self.lod = self.blenderObject.xplane.lod
        else:
            self.lod = (False, False, False)

        if hasattr(self.blenderObject, 'type'):
            self.type = self.blenderObject.type
        else:
            self.type = None

        if hasattr(self.blenderObject.xplane, 'datarefs'):
            for i, dataref in self.blenderObject.xplane.datarefs.items():
                self.datarefs[dataref.path] = dataref

        self.getWeight()

    def collect():
        pass

    # Method: hasAnimAttributes
    # Checks if the object has animation attributes.
    #
    # Returns:
    #   bool - True if object has animtaion attributes, False if not.
    def hasAnimAttributes(self):
        return (hasattr(self, 'animAttributes') and len(self.animAttributes) > 0)

    def collectCustomAttributes(self):
        xplaneFile = self.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        for attr in self.blenderObject.xplane.customAttributes:
            if attr.reset:
                commands.addReseter(attr.name, attr.reset)
            self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

        if hasattr(self.blenderObject, "data") and hasattr(self.blenderObject.data, "xplane") and hasattr(self.blenderObject.data.xplane, "customAttributes"):
            for attr in self.blenderObject.data.xplane.customAttributes:
                self.attributes.add(XPlaneAttribute(attr.name,attr.value,attr.weight))
                self.reseters[attr.name] = attr.reset

    def collectAnimAttributes(self):
        # add custom anim attributes
        for attr in self.blenderObject.xplane.customAnimAttributes:
            self.animAttributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

        # add anim attributes from datarefs
        for dataref in self.blenderObject.xplane.datarefs:
            # show/hide animation
            if dataref.anim_type in ("show", "hide"):
                name = 'ANIM_'+dataref.anim_type
                value = (dataref.show_hide_v1, dataref.show_hide_v2, dataref.path)
                self.animAttributes.add(XPlaneAttribute(name, value))

    # Method: getWeight
    #
    # Returns:
    #   int - The weight of this object.
    def getWeight(self):
        weight = 0

        if hasattr(self.blenderObject.xplane, 'override_weight') and self.blenderObject.xplane.override_weight:
            weight = self.blenderObject.xplane.weight
        else:
            # TODO: set initial weight in constructor
            if self.type=='LIGHT':
                weight = 10000
            elif self.type=='LINE':
                weight = 9000
            else:
                if hasattr(self, 'material'):
                    for i in range(0, len(bpy.data.materials)):
                        if len(self.blenderObject.data.materials) > 0 and self.blenderObject.data.materials[0] == bpy.data.materials[i]:
                            weight = i

            # add max weight of attributes
            max_attr_weight = 0

            for attr in self.attributes:
                if self.attributes[attr].weight > max_attr_weight:
                    max_attr_weight = self.attributes[attr].weight

            for attr in self.cockpitAttributes:
                if self.cockpitAttributes[attr].weight > max_attr_weight:
                    max_attr_weight = self.cockpitAttributes[attr].weight

            weight += max_attr_weight

            # add 1000 to weight on animated objects, so they are all grouped
            # TODO: decide if this is neccessary as it would interrupt grouping by material and animations are fairly cheap.
#            if self.animated():
#                weight+=1000

        self.weight = weight

    def collectConditions(self):
        if self.blenderObject.xplane.conditions:
            self.conditions = self.blenderObject.xplane.conditions

    # Returns OBJ code for this object
    def write(self):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ''

        if debug:
            o += "%s# %s: %s\tweight: %d\n" % (indent, self.type, self.name, self.weight)

        return o
