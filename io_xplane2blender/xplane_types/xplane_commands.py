from ..xplane_config import getDebug, getDebugger
from ..xplane_helpers import firstMatchInList
from .xplane_attributes import XPlaneAttributes
import re

# Class: XPlaneCommands
# Creates the OBJ commands table.
class XPlaneCommands():
    # Property: reseters
    # dict - Stores attribtues that reset other attributes.
    reseters = {}

    # Property: written
    # dict - Stores all already written attributes and theire values.
    written = {}

    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self, xplaneFile):
        self.xplaneFile = xplaneFile

        self.reseters = {
            'ATTR_light_level':'ATTR_light_level_reset',
            'ATTR_cockpit':'ATTR_no_cockpit',
#            'ATTR_cockpit_region':'ATTR_no_cockpit',
            'ATTR_manip_(.*)':'ATTR_manip_none',
            'ATTR_draw_disable':'ATTR_draw_enable',
            'ATTR_poly_os':'ATTR_poly_os 0',
            'ATTR_no_cull':'ATTR_cull',
            'ATTR_hard':'ATTR_no_hard',
            'ATTR_hard_deck':'ATTR_no_hard',
            'ATTR_no_depth':'ATTR_depth',
            'ATTR_no_blend':'ATTR_blend'
        }
        # add default X-Plane states to presve writing them in the obj
        self.written = {
            'ATTR_no_hard': True,
            'ATTR_shade_smooth': True,
            'ATTR_depth': True,
            'ATTR_cull': True,
            'ATTR_blend': True,
            'ATTR_no_hard': True,
            'ATTR_no_cockpit': True,
            'ATTR_no_solid_camera': True,
            'ATTR_draw_enable': True,
            'ATTR_no_cockpit': True
        }

    # Method: write
    # Returns the OBJ commands table.
    #
    # Params:
    #   int lod - (default -1) Level of detail randing from 0..2, if -1 no level of detail will be used
    #
    # Returns:
    #   string - The OBJ commands table.
    def write(self, lod = -1):
        o = ''
        o += self.writeXPlaneBone(self.xplaneFile.rootBone, lod)

        # write down all lights
        # TODO: write them in writeObjects instead to allow light animation and nesting
#        if len(self.file['lights'])>0:
#            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])

        return o

    def writeXPlaneBone(self, xplaneBone, lod):
        o = ''
        o += xplaneBone.writeAnimationPrefix()
        xplaneObject = xplaneBone.xplaneObject
        xplaneObjectWritten = False

        if xplaneObject:
            if lod == -1:
                # only write objects that are in no lod
                if xplaneObject.lod[0] == False and xplaneObject.lod[1] == False and xplaneObject.lod[2] == False:
                    o += self._writeXPlaneObjectPrefix(xplaneObject)
                    xplaneObjectWritten = True

            # write objects that are within that lod and in no lod, as those should appear everywhere
            elif xplaneObject.lod[lod] == True or (xplaneObject.lod[0] == False and xplaneObject.lod[1] == False and xplaneObject.lod[2] == False):
                o += self._writeXPlaneObjectPrefix(xplaneObject)
                xplaneObjectWritten = True

        # write bone children
        for childBone in xplaneBone.children:
            o += self.writeXPlaneBone(childBone, lod)

        if xplaneObject and xplaneObjectWritten:
            o += self._writeXPlaneObjectSuffix(xplaneObject)

        o += xplaneBone.writeAnimationSuffix()

        return o

    def _writeAnimAttributes(self, xplaneObject):
        indent = xplaneObject.xplaneBone.getIndent()
        o = ''

        if xplaneObject.hasAnimAttributes():
            for attr in xplaneObject.animAttributes:
                for value in xplaneObject.animAttributes[attr].getValuesAsString():
                    o += indent +"%s\t%s\n" % (attr, value)

        return o

    def _writeXPlaneObjectPrefix(self, xplaneObject):
        o = ''

        # open material conditions
        if hasattr(xplaneObject, 'material'):
            o += self._writeConditions(xplaneObject.material.conditions, xplaneObject)

        # open object conditions
        o += self._writeConditions(xplaneObject.conditions, xplaneObject)

        if xplaneObject.hasAnimAttributes():
            o += self._writeAnimAttributes(xplaneObject)

        o += xplaneObject.write()

        return o

    def _writeXPlaneObjectSuffix(self, xplaneObject):
        o = ''

        # close material conditions
        if hasattr(xplaneObject, 'material'):
            o += self._writeConditions(xplaneObject.material.conditions, xplaneObject, True)

        # close object conditions
        o += self._writeConditions(xplaneObject.conditions, xplaneObject, True)

        return o

    # Method: writeAttribute
    # Returns the Command line for an attribute.
    # Uses <canWrite> to determine if the command needs to be written.
    #
    # Parameters:
    #   string attr - The attribute name.
    #   string value - The attribute value.
    #   XPlaneObject object - A <XPlaneObject>.
    #
    # Returns:
    #   string or None if the command must not be written.
    def writeAttribute(self, attr, xplaneObject):
        o = ''
        value = attr.getValue()
        name = attr.name
        indent = xplaneObject.xplaneBone.getIndent()

        if value != None and self.canWriteAttribute(name, value):
            if isinstance(value, bool):
                if value:
                    o += indent + '%s\n' % name

                    # store this in the written attributes
                    self.written[name] = value
            else:
                # store this in the written attributes
                self.written[name] = value
                value = attr.getValueAsString()
                value = self.parseAttributeValue(value, xplaneObject.blenderObject)
                o += indent + '%s\t%s\n' % (name, value)

                # check if this thing has a reseter and remove counterpart if any
                reseter = self.getAttributeReseter(name)

                if reseter and reseter in self.written:
                    del self.written[reseter]

                writtenNames = list(self.written.keys())

                # check if a reseter counterpart has been written and if so delete its reseter
                for reseter in self.reseters:
                    matchingWritten = firstMatchInList(re.compile(reseter), writtenNames)

                    if self.reseters[reseter] == name and matchingWritten:
                        del self.written[matchingWritten]

        return o

    # Method: parseAttributeValue
    # Returns a string with the parsed attribute value (replacing insert tags)
    #
    # Parameters:
    #   string value - The attribute value.
    #   blenderObject - A blender object.
    #
    # Returns:
    #   string - The value with replaced insert tags.
    def parseAttributeValue(self, value, blenderObject):
        if str(value).find('{{xyz}}') != -1:
            return str(value).replace('{{xyz}}', '%6.8f\t%6.8f\t%6.8f' % (
                floatToStr(blenderObject.location[0]),
                floatToStr(blenderObject.location[2]),
                floatToStr(-blenderObject.location[1])
            ))

        return value

    # Method: canWriteAttribute
    # Determines if an attribute must/can be written.
    #
    # Parameters:
    #   string attr - The attribute name.
    #   string value - The attribute value.
    #
    # Returns:
    #   bool - True if the attribute must be written, else false.
    def canWriteAttribute(self, attr, value):
        if attr not in self.written:
            return True
        elif self.written[attr] == value:
            return False
        else:
            return True

    def addReseter(self, attr, reseter):
        self.reseters[attr] = reseter

    # Method: attributeIsReseter
    # Determines if a given attribute is a resetter.
    #
    # Parameters:
    #  string attr - The attribute name
    #  dict reseters - optional (default = self.reseters) a dict of reseters
    #
    # Returns:
    #  bool - True if attribute is a reseter, else False
    def attributeIsReseter(self, attr, reseters = None):
        if reseters == None: reseters = self.reseters

        for reseter in reseters:
            if reseters[reseter] == attr:
                return True

        return False

    def getAttributeReseter(self, attr):
        reseterNames = list(self.reseters.keys())

        for reseter in reseterNames:
            pattern = re.compile(reseter)

            if pattern.fullmatch(attr):
                return self.reseters[reseter]

        return None

    # Method: writeReseters
    # Returns the commands for a <XPlaneObject> needed to reset previous commands.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeReseters(self, xplaneObject):
        debug = getDebug()
        debugger = getDebugger()
        o = ''
        indent = xplaneObject.xplaneBone.getIndent()

        # create a temporary attributes dict
        attributes = XPlaneAttributes()
        # add custom attributes
        for attr in xplaneObject.attributes:
            if xplaneObject.attributes[attr]:
                attributes.add(xplaneObject.attributes[attr])
        # add material attributes if any
        if hasattr(xplaneObject, 'material'):
            for attr in xplaneObject.material.attributes:
                if xplaneObject.material.attributes[attr]:
                    attributes.add(xplaneObject.material.attributes[attr])
        # add cockpit attributes
        for attr in xplaneObject.cockpitAttributes:
            if xplaneObject.cockpitAttributes[attr]:
                attributes.add(xplaneObject.cockpitAttributes[attr])

        attributeNames = list(attributes.keys())
        writtenNames = list(self.written.keys())

        for reseter in self.reseters:
            resetingAttr = self.reseters[reseter]
            pattern = re.compile(reseter)

            matchingWritten = firstMatchInList(pattern, writtenNames)
            matchingAttribute = firstMatchInList(pattern, attributeNames)

            # only reset attributes that wont be written with this object again
            if not matchingAttribute and matchingWritten:
#                if debug:
#                    debugger.debug('writing Reseter for %s: %s' % (attr,self.reseters[attr]))

                # write reseter and add it to written
                o += indent + resetingAttr + "\n"
                self.written[resetingAttr] = True

                # we've reset an attribute so remove it from written as it will need rewrite with next object
                del self.written[matchingWritten]
        return o

    def _writeConditions(self, conditions, xplaneObject, close = False):
        o = ''
        indent = xplaneObject.xplaneBone.getIndent()

        for condition in conditions:
            if close == True:
                o += indent + 'ENDIF\n'
            else:
                if condition.value == True:
                    o += indent + 'IF %s\n' % condition.variable
                else:
                    o += indent + 'IF NOT %s\n' % condition.variable

        return o
