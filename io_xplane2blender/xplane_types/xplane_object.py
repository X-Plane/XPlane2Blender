import bpy
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_types.xplane_attributes import XPlaneAttributes

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
    def __init__(self, blenderObject:bpy.types.Object):
        self.type = '' # type: Optional[str]
        self.blenderObject = blenderObject

        #This is assaigned and tied together in in XPlaneBone's constructor
        self.xplaneBone = None
        self.name = blenderObject.name # type: str
        self.datarefs = {} # type: Dict[str,str]
        self.bakeMatrix = None
        
        self.attributes = XPlaneAttributes()
        self.cockpitAttributes = XPlaneAttributes()
        self.animAttributes = XPlaneAttributes()
        self.conditions = []

        if hasattr(self.blenderObject.xplane, 'lod'):
            self.lod = self.blenderObject.xplane.lod
        else:
            self.lod = (False, False, False, False)

        if hasattr(self.blenderObject, 'type'):
            self.type = self.blenderObject.type
        else:
            self.type = None

        if hasattr(self.blenderObject.xplane, 'datarefs'):
            for i, dataref in self.blenderObject.xplane.datarefs.items():
                self.datarefs[dataref.path] = dataref

        self.getWeight()

    def collect(self):
        assert self.xplaneBone is not None, "xplaneBone must not be None!"

        # add custom attributes
        self.collectCustomAttributes()

        # add anim attributes from datarefs and custom anim attributes
        self.collectAnimAttributes()

        # add conditions
        self.collectConditions()

        self.attributes.order()
        self.animAttributes.order()
        self.cockpitAttributes.order()

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
                if attr.reset:
                    commands.addReseter(attr.name, attr.reset)
                self.attributes.add(XPlaneAttribute(attr.name,attr.value,attr.weight))

    def collectAnimAttributes(self):
        # add custom anim attributes
        for attr in self.blenderObject.xplane.customAnimAttributes:
            self.animAttributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

        # add anim attributes from datarefs
        for dataref in self.blenderObject.xplane.datarefs:
            # show/hide animation
            if dataref.anim_type in (ANIM_TYPE_SHOW, ANIM_TYPE_HIDE):
                name = 'ANIM_' + dataref.anim_type
                value = (dataref.show_hide_v1, dataref.show_hide_v2, dataref.path)
                self.animAttributes.add(XPlaneAttribute(name, value))

    #TODO: This needs to be renamed!!! This is just terrible. This doesn't actually get anything, it sets self.weight!
    # Method: getWeight
    #
    # Parameters:
    #   defaultWeight - (default = 0)
    #
    # Returns:
    #   int - The weight of this object.
    def getWeight(self, defaultWeight:int = 0):
        weight = defaultWeight

        if hasattr(self.blenderObject.xplane, 'override_weight') and self.blenderObject.xplane.override_weight:
            weight = self.blenderObject.xplane.weight
        else:
            # add max weight of attributes
            max_attr_weight = 0

            for attr in self.attributes:
                if self.attributes[attr].weight > max_attr_weight:
                    max_attr_weight = self.attributes[attr].weight

            for attr in self.cockpitAttributes:
                if self.cockpitAttributes[attr].weight > max_attr_weight:
                    max_attr_weight = self.cockpitAttributes[attr].weight

            weight += max_attr_weight

        self.weight = weight

    def collectConditions(self):
        if self.blenderObject.xplane.conditions:
            self.conditions = self.blenderObject.xplane.conditions

    # Returns OBJ code for this object
    def write(self):
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        o = ''

        xplaneFile = self.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        if debug:
            o += "%s# %s: %s\tweight: %d\n" % (indent, self.type, self.name, self.weight)

        o += commands.writeReseters(self)

        for attr in self.attributes:
            o += commands.writeAttribute(self.attributes[attr], self)

        # if the file is a cockpit file write all cockpit attributes
        if xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT:
            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        return o
