import bpy
import mathutils

from typing import Dict, List, Optional
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute
from io_xplane2blender.xplane_types.xplane_attributes import XPlaneAttributes
from io_xplane2blender.xplane_types import xplane_bone

class XPlaneObject():
    """
    An object in the XPlane2Blender collection tree,
    tied with the Blender Object it is based off.
    """
    def __init__(self, blenderObject: bpy.types.Object)->None:
        self.blenderObject = blenderObject

        #This is assaigned and tied together in in XPlaneBone's constructor
        self.xplaneBone = None # type: Optional[xplane_bone.XPlaneBone]
        self.name = blenderObject.name # type: str
        self.type = self.blenderObject.type # type: str
        self.datarefs = {} # type: Dict[str,str]
        self.bakeMatrix = None # type: Optional[mathutils.Matrix]

        self.attributes = XPlaneAttributes()
        self.cockpitAttributes = XPlaneAttributes()
        self.animAttributes = XPlaneAttributes()
        self.conditions = [] # type: List[io_xplane2blender.xplane_props.XPlaneCondition]

        self.lod = self.blenderObject.xplane.lod
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
