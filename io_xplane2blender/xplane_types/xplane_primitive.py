from ..xplane_config import getDebug
from .xplane_object import XPlaneObject
from .xplane_material import XPlaneMaterial

# Class: XPlanePrimitive
# A Mesh object.
#
# Extends:
#   <XPlaneObject>
class XPlanePrimitive(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this object.

    # Property: material
    # XPlaneMaterial - A <XPlaneMaterial>

    # Property: faces
    # XPlaneFaces - Instance of <XPlaneFaces> with all face of this mesh. Currently not in use. This should be used when commands will work on a per face basis.

    # Property: attributes
    # dict - Object attributes that will be turned into commands with <XPlaneCommands>.
    
    # Property: cockpitAttributes
    # dict - Object attributes for cockpit settings, that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines basic <attributes> and <cockpitAttributes>, Creates <material>, runs <getManipulatorAttributes>, <getLightLevelAttributes>, <XPlaneObject.getCoordinates> and <XPlaneObject.getAnimations>.
    #
    # Parameters:
    #   blenderObject - A Blender object
    def __init__(self, blenderObject):
        super(XPlanePrimitive,self).__init__(blenderObject)
        self.type = 'PRIMITIVE'
        self.indices = [0, 0]
        self.material = XPlaneMaterial(self)
        self.export_mesh = blenderObject.xplane.export_mesh
        self.faces = None

        self.getWeight()

    def collect(self):
        # add custom attributes
        self.collectCustomAttributes()

        # add anim attributes from datarefs and custom anim attributes
        self.collectAnimAttributes()

        # add manipulator attributes
        self.collectManipulatorAttributes()

        # add conditions
        self.collectConditions()

        self.attributes.order()
        self.animAttributes.order()
        self.cockpitAttributes.order()

        if self.material:
            self.material.collect()

    # Method: collectManipulatorAttributes
    # Defines Manipulator attributes in <cockpitAttributes> based on settings in <XPlaneManipulator>.
    def collectManipulatorAttributes(self):
        attr = 'ATTR_manip_'
        value = True

        if self.blenderObject.xplane.manip.enabled:
            manip = self.blenderObject.xplane.manip
            type = self.blenderObject.xplane.manip.type
            attr+=type
            if type=='drag_xy':
                value = "%s\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%s\t%s\t%s" % (manip.cursor,manip.dx,manip.dy,manip.v1_min,manip.v1_max,manip.v2_min,manip.v2_max,manip.dataref1,manip.dataref2,manip.tooltip)
            if type=='drag_axis':
                value = "%s\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%s\t%s" % (manip.cursor,manip.dx,manip.dy,manip.dz,manip.v1,manip.v2,manip.dataref1,manip.tooltip)
            if type=='drag_axis_pix':
                value = "%s\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%s\t%s" % (manip.cursor,manip.dx,manip.step,manip.exp,manip.v1,manip.v2,manip.dataref1,manip.tooltip)
            if type=='command':
                value = "%s\t%s\t%s" % (manip.cursor,manip.command,manip.tooltip)
            if type=='command_axis':
                value = "%s\t%6.8f\t%6.8f\t%6.8f\t%s\t%s\t%s" % (manip.cursor,manip.dx,manip.dy,manip.dz,manip.positive_command,manip.negative_command,manip.tooltip)
            if type=='push':
                value = "%s\t%6.8f\t%6.8f\t%s\t%s" % (manip.cursor,manip.v_down,manip.v_up,manip.dataref1,manip.tooltip)
            if type=='radio':
                value = "%s\t%6.8f\t%s\t%s" % (manip.cursor,manip.v_down,manip.dataref1,manip.tooltip)
            if type=='toggle':
                value = "%s\t%6.8f\t%6.8f\t%s\t%s" % (manip.cursor,manip.v_on,manip.v_off,manip.dataref1,manip.tooltip)
            if type in ('delta','wrap'):
                value = "%s\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%s\t%s" % (manip.cursor,manip.v_down,manip.v_hold,manip.v1_min,manip.v1_max,manip.dataref1,manip.tooltip)
        else:
            attr=None

        if attr is not None:
            self.cockpitAttributes.add(XPlaneAttribute(attr,value))

    def write(self):
        indent = self.xplaneBone.getIndent()
        o = super(XPlanePrimitive, self).write()

        # rendering (do not render meshes/objects with no indices)
        if self.indices[1] > self.indices[0]:
            o += self.material.write()

            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += "%sTRIS\t%d %d\n" % (indent, offset, count)

        return o
