# import bpy
# import math
import mathutils
from .xplane_keyframe import XPlaneKeyframe
from ..xplane_config import getDebugger, getDebug
from ..xplane_helpers import floatToStr

# Class: XPlaneBone
# Animation/Hierarchy primitive
class XPlaneBone():

    # Constructor: __init__
    #
    # Parameters:
    #   blenderObject - Blender Object
    #   xplaneObject - <XPlaneObject>
    #   parent - (optional) parent <XPlaneAnimBone>
    def __init__(self, blenderObject = None, xplaneObject = None, parent = None):
        self.xplaneObject = xplaneObject
        self.blenderObject = blenderObject
        self.blenderBone = None
        self.parent = parent
        self.children = []

        if self.xplaneObject:
            self.xplaneObject.xplaneBone = self

        # nesting level of this bone (used for intendation)
        self.level = 0

        if self.parent:
            self.level = self.parent.level + 1

        # dict - The keys are the dataref paths and the values are lists of <XPlaneKeyframes>.
        self.animations = {}

        # dict - The keys area dataref paths and the values are <XPlaneDataref> properties
        self.datarefs = {}

    # Method: isAnimated
    # Checks if the object is animated.
    #
    # Returns:
    #   bool - True if bone is animated, False if not.
    def isAnimated(self):
        return (hasattr(self, 'animations') and len(self.animations) > 0)

    # Method: collectAnimations
    # Stores all animations in <animations>.
    def collectAnimations(self):
        if not self.parent:
            return None

        debug = getDebug()
        debugger = getDebugger()

        bone = self.blenderBone
        blenderObject = self.blenderObject

        # if bone:
        #     groupName = "XPlane Datarefs " + bone.name
        # else:
        #     groupName = "XPlane Datarefs"

        #check for animation
        if debug:
            if bone:
                debugger.debug("\t\t checking animations of %s:%s" % (blenderObject.name, bone.name))
            else:
                debugger.debug("\t\t checking animations of %s" % blenderObject.name)

        animationData = blenderObject.animation_data

        # bone animation data resides in the armature objects .data block
        if bone:
            animationData = blenderObject.data.animation_data

        if (animationData != None and animationData.action != None and len(animationData.action.fcurves) > 0):
            if debug:
                debugger.debug("\t\t animation found")
            #check for dataref animation by getting fcurves with the dataref group
            for fcurve in animationData.action.fcurves:
                if debug:
                    debugger.debug("\t\t checking FCurve %s Group: %s" % (fcurve.data_path, fcurve.group))
                #if (fcurve.group != None and fcurve.group.name == groupName): # since 2.61 group names are not set so we have to check the datapath
                if ('xplane.datarefs' in fcurve.data_path):
                    # get dataref name
                    pos = fcurve.data_path.find('xplane.datarefs[')
                    if pos!=-1:
                        index = fcurve.data_path[pos+len('xplane.datarefs[') : -len('].value')]
                    else:
                        return

                    # old style datarefs with wrong datapaths can cause errors so we just skip them
                    try:
                        index = int(index)
                    except:
                        return

                    # FIXME: removed datarefs keep fcurves, so we have to check if dataref is still there. FCurves have to be deleted correctly.
                    if bone:
                        if index < len(bone.xplane.datarefs):
                            dataref = bone.xplane.datarefs[index].path
                        else:
                            return
                    else:
                        if index < len(blenderObject.xplane.datarefs):
                            dataref = blenderObject.xplane.datarefs[index].path
                        else:
                            return

                    if debug:
                        debugger.debug("\t\t adding dataref animation: %s" % dataref)

                    if len(fcurve.keyframe_points) > 1:
                        # time to add dataref to animations
                        self.animations[dataref] = []
                        if bone:
                            self.datarefs[dataref] = bone.xplane.datarefs[index]
                        else:
                            self.datarefs[dataref] = blenderObject.xplane.datarefs[index]

                        # store keyframes temporary, so we can resort them
                        keyframes = []

                        for keyframe in fcurve.keyframe_points:
                            if debug:
                                debugger.debug("\t\t adding keyframe: %6.3f" % keyframe.co[0])
                            keyframes.append(keyframe)

                        # sort keyframes by frame number
                        keyframesSorted = sorted(keyframes, key=lambda keyframe: keyframe.co[0])

                        for i in range(0,len(keyframesSorted)):
                            self.animations[dataref].append(XPlaneKeyframe(keyframesSorted[i], i, dataref, self))

    def getName(self):
        if self.parent == None:
            return '%d ROOT' % self.level
        elif self.blenderBone:
            return '%d Bone: %s' % (self.level, self.blenderBone.name)
        elif self.blenderObject:
            return '%d Object: %s' % (self.level, self.blenderObject.name)

        return 'UNKNOWN'

    def getBlenderName(self):
        if self.blenderBone:
            return self.blenderBone.name
        elif self.blenderObject:
            return self.blenderObject.name

        return None

    def getIndent(self):
        return ''.ljust(self.level, '\t')

    def toString(self, indent = ''):
        out = indent + self.getName() + '\n'

        for bone in self.children:
            out += bone.toString(indent + '\t')

        return out

    def getFirstAnimatedParent(self):
        if self.parent == None:
            return None

        if self.parent.isAnimated() or self.parent.parent == None:
            return self.parent
        else:
            return self.parent.getFirstAnimatedParent()


    def getBlenderWorldMatrix(self):
        if self.parent == None:
            return mathutils.Matrix.Identity(4)

        if self.blenderBone:
            # TODO: what is the world matrix of a bone?
            return None
        elif self.blenderObject:
            return self.blenderObject.matrix_world.copy()

    def getPreAnimationMatrix(self):
        if not self.isAnimated() or self.parent == None:
            # not animated objects have own world matrix
            return self.getBlenderWorldMatrix()
        else:
            # animated objects have parents world matrix
            return self.parent.getBlenderWorldMatrix()

    def getPostAnimationMatrix(self):
        # for non-animated or root bones, post = pre
        if not self.isAnimated() or self.parent == None:
            return self.getPreAnimationMatrix()
        else:
            return self.getBlenderWorldMatrix()

    def getBakeMatrix(self):
        if self.parent == None:
            return self.getBlenderWorldMatrix()
        else:
            return self.getFirstAnimatedParent().getPostAnimationMatrix().inverted_safe() * self.getPreAnimationMatrix()

    def __str__(self):
        return self.toString()

    def writeAnimationPrefix(self):
        debug = getDebug()
        debugger = getDebugger

        indent = self.getIndent()
        o = ''

        if debug:
            o += indent + '# ' + self.getName() + '\n'

        preMatrix = self.getPreAnimationMatrix()
        postMatrix = self.getPostAnimationMatrix()

        if postMatrix is not preMatrix:
            # TODO: this is most probably wrong
            bakeMatrix = self.getBakeMatrix()
            # write out static translations of pre animation matrix
            o += indent + 'ANIM_begin\n'

            translation = bakeMatrix.to_translation()

            o += indent + 'ANIM_trans\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
                floatToStr(translation[0]),
                floatToStr(translation[1]),
                floatToStr(translation[2]),
                floatToStr(translation[0]),
                floatToStr(translation[1]),
                floatToStr(translation[2])
            )

        for dataref in self.animations:
            o += self.writeKeyframes(dataref)

        return o

    def writeKeyframes(self, dataref):
        keyframes = self.animations[dataref]
        o = ''
        indent = self.getIndent()

        o += "%sANIM_trans_begin\t%s\n" % (indent, dataref)

        for keyframe in keyframes:
            o += "%sANIM_trans_key\t%6.8f\t%6.8f\t%6.8f\t%6.8f\n" % (indent, keyframe.value, keyframe.translation[0], keyframe.translation[1], keyframe.translation[2])

        o += "%sANIM_trans_end\n" % indent

        return o

    def writeAnimationSuffix(self):
        o = ''

        # unanimated bones do not export any suffix
        preMatrix = self.getPreAnimationMatrix()
        postMatrix = self.getPostAnimationMatrix()

        if postMatrix is not preMatrix:
            indent = self.getIndent()
            o += indent + 'ANIM_end\n'

        return o
