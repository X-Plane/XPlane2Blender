import re

import bpy

from io_xplane2blender.xplane_types import xplane_attribute
from io_xplane2blender.xplane_types.xplane_attributes import XPlaneAttributes

from ..xplane_config import getDebug
from ..xplane_constants import *
from io_xplane2blender import xplane_helpers
from ..xplane_helpers import floatToStr, logger


# Setters, resetters, and counterparts:
#
# Conceptually X-Plane OBJ files are a state vector with orthogonal state, e.g. our "hardness" state, "blend" state,
# polygon offset state, etc.  Each triagnle mesh emitted via TRIS has the state of the vector, and attribute commands
# change the state vector for future commands.
#
# What makes file generation slightly tricky is that the name of the attributes is unrelated to the state vector, and
# the state vector can be affected by an arbitrary number of commands, e.g.
#
# ATTR_blend: set blend mode to "blend"
# ATTR_no_blend x: set blend mode to "no_blend", set blend cutoff to x.
# ATTR_shadow_blend x: set blend mode to "shadow_blend", set blend cutoff to x.
#
# There is, of coarse, an interaction between all three - we don't need to repeat ATTR_blend, until
# _one of_ ATTR_no_blend or ATTR_shadow_blend interposes, and we don't need to repeat ATTR_shadow_blend
# after another ATTR_shadow_blend unless the cutoff changes.
#
# Here's what makes the Blender 2.7 exporter REALLY tricky: the attribute system is written _generically_, to support
# the user interface where authors can make up their own attributes on the fly.  While every other OBJ8 exporter knows
# the schema, this one assumes very little.  This feature was requested of Ondrej so that authors could adopt new
# X-Plane features without waiting for an exporter iteration.
#
#
# Here's how the system works.  Conceptually any given attribute has one or more "counterparts" - other attributes that
# affect the same state vector.  For example, every ATTR_manip_xx command is a counter-part to every other one, and
# ATTR_hard, ATTR_no_hard, and ATTR_hard_deck are all counterparts.
#
# Amongst the set of counterparts, one is deemed the "resetter" - this is usually the one that sets X-Plane to the
# default state, and/or takes no arguments.  The other ones are "setters".
#
# The "reseters" map is a map of:
#
# Key: a regular expression that matches every setter.
# Value: a resetter.
#
# From this table, we can determine two things:
# 1. For any given attribute, what previously written attribute is no longer valid.  For example, if
#	 We write ATTR_no_hard, any past ATTR_hard or ATTR_hard_deck is no longer in effect.
# 2. If we need to write a new object that is missing a previously written setter, what is the resetter
#	 to issue to get to default state.
#
# For customization, the "addReseter" can be called to register the resetter for a custom attribute that
# will need to be undone later by another part of the code.
#
#
# The command processor tracks state by keeping a map of every written and currently effective attrbute, keyed by
# the attribute name.  When a new attribute is to be written, it is first compared to the existing written attributes
# and dropped if needed.  Then once it is written (if needed), every counter part to the new attribute that is in
# the written vector is removed.
#
#
# One known bug that I am aware of: X-Plane has interaction between manipulator and panel-texture state; the current
# exporter does not model this and the current authoring level blender data does not support it.  For the 3.4 release,
# we expect to leave things in their currently broken state; for 3.5, we can then add specific panel attribute labeling
# to the UI and have authors migrate their projects forward.
#
# Class: XPlaneCommands
# Creates the OBJ commands table.
class XPlaneCommands():
    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self, xplaneFile):
        self.xplaneFile = xplaneFile

        self.reseters = {
            'ATTR_light_level':'ATTR_light_level_reset',
            'ATTR_cockpit|ATTR_cockpit_region':'ATTR_no_cockpit',
            'ATTR_manip_(?!none)(?!wheel)(.*)':'ATTR_manip_none',
            'ATTR_draw_disable':'ATTR_draw_enable',
            'ATTR_poly_os':'ATTR_poly_os 0',
            'ATTR_hard|ATTR_hard_deck':'ATTR_no_hard',
            'ATTR_no_blend|ATTR_shadow_blend':'ATTR_blend',
            'ATTR_draped': 'ATTR_no_draped',
            'ATTR_solid_camera': 'ATTR_no_solid_camera'
        }

        # these attributes/commands are not persistant and must always be rewritten
        self.inpersistant = {
            'ATTR_axis_detent_range',
            'ATTR_manip_wheel'
        }

        # add default X-Plane states to presve writing them in the obj
        self.written = {
            'ATTR_no_hard': True,
            'ATTR_blend': True,
            'ATTR_no_hard': True,
            'ATTR_no_cockpit': True,
            'ATTR_no_solid_camera': True,
            'ATTR_draw_enable': True,
            'ATTR_no_draped': True
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

        return o

    def writeXPlaneBone(self, xplaneBone, lod):
        o = ''
        o += xplaneBone.writeAnimationPrefix()
        xplaneObject = xplaneBone.xplaneObject
        xplaneObjectWritten = False
        exportMode = self.xplaneFile.exportMode
        numLods = int(self.xplaneFile.options.lods)

        if xplaneObject:
            lods = []

            if exportMode == EXPORT_MODE_LAYERS:
                lods = xplaneObject.lod
            elif exportMode == EXPORT_MODE_ROOT_OBJECTS:
                lods = xplaneObject.blenderObject.layers

            isInLod = False

            for lodIndex in range(0, MAX_LODS):
                if len(lods) > lodIndex and lods[lodIndex] == True:
                    isInLod = True
                    break

            if lod == -1:
                # only write objects that are in no lod
                if not isInLod or (exportMode == EXPORT_MODE_ROOT_OBJECTS and numLods <= 0):
                    o += self._writeXPlaneObjectPrefix(xplaneObject)
                    xplaneObjectWritten = True

            # write objects that are within that lod and in no lod, as those should appear everywhere
            elif lods[lod] == True or not isInLod:
                o += self._writeXPlaneObjectPrefix(xplaneObject)
                xplaneObjectWritten = True

        # write bone children
        for childBone in xplaneBone.children:
            o += self.writeXPlaneBone(childBone, lod)

        if xplaneObject and xplaneObjectWritten:
            o += self._writeXPlaneObjectSuffix(xplaneObject)

        o += xplaneBone.writeAnimationSuffix()

        return o

    def _writeXPlaneObjectPrefix(self, xplaneObject):
        o = ''

        # open material conditions
        if hasattr(xplaneObject, 'material'):
            o += self._writeConditions(xplaneObject.material.conditions, xplaneObject)

        # open object conditions
        o += self._writeConditions(xplaneObject.conditions, xplaneObject)

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
        for i in range(len(attr.value)):
            value = attr.getValue(i)
            name = attr.name
            indent = xplaneObject.xplaneBone.getIndent()

            if value != None and self.canWriteAttribute(name, value):
                if isinstance(value, bool):
                    if value:
                        o += indent + '%s\n' % name

                        # store this in the written attributes
                        self.written[name] = value

                        # If there is a resetter for this attribute, we need to
                        # nuke it from the written list - we are replacing it.
                        counterparts = self.getAttributeCounterparts(name)
                        
                        for counterpart in counterparts:
                            if counterpart in self.written:
                                del self.written[counterpart]

                else:
                    # store this in the written attributes
                    self.written[name] = value
                    value = attr.getValueAsString(i)
                    value = self.parseAttributeValue(value, xplaneObject.blenderObject)
                    o += indent + '%s\t%s\n' % (name, value)

                    # check if this thing has a reseter and remove counterpart if any
                    counterparts = self.getAttributeCounterparts(name)

                    for counterpart in counterparts:
                        if counterpart in self.written:
                            del self.written[counterpart]
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
                xplane_helpers.floatToStr(blenderObject.location[0]),
                xplane_helpers.floatToStr(blenderObject.location[2]),
                xplane_helpers.floatToStr(-blenderObject.location[1])
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
    def canWriteAttribute(self, attr:str, value)->bool:
        if attr not in self.written or attr in self.inpersistant:
            return True
        elif self.written[attr] == value:
            return False
        else:
            return True

    def addReseter(self, attr:str, reseter:str):
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
    def getAllAttributesForReseter(self, attr):
        for reseter in sorted(self.reseters.keys()):
            if self.reseters[reseter] == attr:
                return reseter

        return None

    # Given any non-resetter attribute, this returns the
    # resetter that "undoes" it.  Given any resetter, this
    # returns all setters.
    def getAttributeCounterparts(self, attr):

        found=[]
        setterPatterns = sorted(list(self.reseters.keys()))

        for setterPattern in setterPatterns:
            resetter = self.reseters[setterPattern]
            compiledPattern = re.compile(setterPattern)

            # The attribute is a setter - the resetter is a counter part
            if compiledPattern.fullmatch(attr):
                found.append(resetter)
    
            # The pattern is a resetter or ONE of the setters.
            # Every other setter but us is a counterpart.
            if attr == resetter or compiledPattern.fullmatch(attr):
                allWritten = sorted(list(self.written.keys()))
                for oneWritten in allWritten:
                    if compiledPattern.fullmatch(oneWritten):
                        # We have to check for ourselves - we might be taking every written attribute
                        # that is a SETTER that matches the reg-ex, e.g. we are ATTR_cockpit and we found
                        # ATTR_cockpit|ATTR_cockpit_region.  So take ATTR_cockpit_region but NOT us.
                        if oneWritten != attr:
                            found.append(oneWritten)
        return found

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
        o = ''
        indent = xplaneObject.xplaneBone.getIndent()
        
        # create a temporary attributes dict
        attributes = XPlaneAttributes()
        # add custom attributes
        for attr in xplaneObject.attributes:
            if xplaneObject.attributes[attr].getValue():
                attributes.add(xplaneObject.attributes[attr])

        # add material attributes if any
        if hasattr(xplaneObject, 'material'):
            for attr in xplaneObject.material.attributes:
                if xplaneObject.material.attributes[attr].getValue():
                    attributes.add(xplaneObject.material.attributes[attr])
        # add cockpit attributes
        for attr in xplaneObject.cockpitAttributes:
            if xplaneObject.cockpitAttributes[attr].getValue():
                attributes.add(xplaneObject.cockpitAttributes[attr])

        WHITE_LIST = {
                'ATTR_light_level',
                'ATTR_light_level_reset',
                'ATTR_cockpit',
                'ATTR_cockpit_region',
                'ATTR_no_cockpit',
                'ATTR_draw_disable',
                'ATTR_draw_enable',
                'ATTR_poly_os',
                'ATTR_poly_os 0',
                'ATTR_hard',
                'ATTR_hard_deck',
                'ATTR_no_hard',
                'ATTR_no_blend',
                'ATTR_shadow_blend',
                'ATTR_blend',
                'ATTR_draped',
                'ATTR_no_draped',
                'ATTR_solid_camera',
                'ATTR_no_solid_camera'
                }
        
        #  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        # <What's up with WHITE_LIST? IT'S A STUPID HACK!>
        #  vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        # To ensure known OBJ directives only get reset as needed,
        # we artificially add every known OBJ directive (except
        # manips) to the attributes.
        #
        # This way the resetter thinks it doesn't have to reset
        # because the next object "has" it already.
        for attr in WHITE_LIST:
            attributes.add(xplane_attribute.XPlaneAttribute(attr))

        # This is the attributes that the next object will have.
        #
        # Comment about the comment: Remember "next object",
        # can mean self if that is what you passed in. Don't confuse
        # the comment's sense of tense with how this is currently used in
        # the exporter. Just remember who xplaneObject is and you'll be fine.
        #
        # Comment about the comment about the comment:
        # The resetter system is so confusing its
        # good comments also need good comments. Ugh.
        attributeNames = sorted(attributes.keys())

        # This is the attributes we have already stated that MIGHT need to be reset.
        writtenNames = sorted(self.written.keys())
        for setterPattern in sorted(self.reseters.keys()):
            resetingAttr = self.reseters[setterPattern]
            pattern = re.compile(setterPattern)

            matchingWritten = [x for x in writtenNames if pattern.fullmatch(x)]
            matchingAttribute = [x for x in attributeNames if pattern.fullmatch(x)]

            # Now that the added white list trick is in place,
            # we'll nearly always have 2 matching attributes
            if len(matchingAttribute) > 2:
                print("WARNING: multiple incoming attributes matched %s" % setterPattern)
                print(matchingAttribute)

            if len(matchingWritten) > 1:
                print("WARNING: multiple written attributes matched %s" % setterPattern)
                print(matchingWritten)

            
            if matchingWritten and not matchingAttribute:
                # only reset attributes that wont be written with this object again
                #logger.info('writing Reseter for %s: %s' % (attr,self.reseters[attr]))
                # write reseter and add it to written
                o += indent + resetingAttr + "\n"
                self.written[resetingAttr] = True

                for orphan in matchingWritten:
                    #print("orphan: "+orphan)
                    # we've reset an attribute so remove it from written as it will need rewrite with next object
                    del self.written[orphan]
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
