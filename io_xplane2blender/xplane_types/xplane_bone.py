# import bpy
# import math
import mathutils
import math
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
        self.xplaneFile = None
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
        if self.level == 0:
            return  ''

        return ''.ljust(self.level - 1, '\t')

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
            # TODO: is this the correct multi order?
            return self.blenderObject.matrix_world.copy() * self.blenderBone.matrix_local.copy()
        elif self.blenderObject:
            return self.blenderObject.matrix_world.copy()

    def getPreAnimationMatrix(self):
        if not self.isAnimated() or self.parent == None:
            # not animated objects have own world matrix
            return self.getBlenderWorldMatrix()
        elif self.blenderBone:
            # TODO: what is the equivalent to .parent.matrix_parent_inverse for bones?
            parent_matrix = None
            
            if self.blenderBone.parent:
                parent_matrix = self.blenderBone.parent.matrix
            else:
                parent_matrix = self.blenderObject.matrix_local

            return self.parent.getBlenderWorldMatrix() * parent_matrix.inverted_safe()
        elif self.blenderObject:
            # animated objects have parents world matrix * inverse of parents matrix
            return self.parent.getBlenderWorldMatrix() * self.blenderObject.matrix_parent_inverse

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
        indent = self.getIndent()
        o = ''

        if debug:
            o += indent + '# ' + self.getName() + '\n'

        if not self.isAnimated():
            return o

        preMatrix = self.getPreAnimationMatrix()
        postMatrix = self.getPostAnimationMatrix()
        bakeMatrix = self.getBakeMatrix()

        if postMatrix is not preMatrix:
            # write out static translations of bake
            o += indent + 'ANIM_begin\n'

            o += self._writeStaticTranslation(bakeMatrix)
            o += self._writeStaticRotation(bakeMatrix)

        for dataref in self.animations:
            o += self.writeKeyframes(dataref)

        if postMatrix is not preMatrix:
            # revert static translations needed for correct rotation origin
            o += self._writeStaticTranslation(bakeMatrix, True)

        return o

    def _writeStaticTranslation(self, bakeMatrix, reverse = False):
        debug = getDebug()
        indent = self.getIndent()
        o = ''

        bakeMatrix = bakeMatrix or self.getBakeMatrix()

        translation = bakeMatrix.to_translation()

        # ignore noop translations
        if translation[0] == 0 and translation[1] == 0 and translation[2] == 0:
            return o

        if reverse:
            for i in range(0, 3):
               translation[i] = -translation[i]

        if debug:
            o += indent + '# static translation\n'

        o += indent + 'ANIM_trans\t%s\t%s\t%s\t%s\t%s\t%s\n' % (
            floatToStr(translation[0]),
            floatToStr(translation[2]),
            floatToStr(-translation[1]),
            floatToStr(translation[0]),
            floatToStr(translation[2]),
            floatToStr(-translation[1])
        )

        return o

    def _writeStaticRotation(self, bakeMatrix):
        debug = getDebug()
        indent = self.getIndent()
        o = ''
        bakeMatrix = bakeMatrix or self.getBakeMatrix()
        rotation = bakeMatrix.to_euler('XYZ')

        # ignore noop rotations
        if rotation[0] == 0 and rotation[1] == 0 and rotation[2] == 0:
            return o

        if debug:
            o += indent + '# static rotation\n'

        axes = (0, 2, 1)
        eulerAxes = [(1.0,.0,0.0), (0.0,1.0,0.0), (0.0,0.0,1.0)]
        i = 0

        for axis in eulerAxes:
            deg = math.degrees(rotation[axes[i]])

            o += indent + 'ANIM_rotate\t%s\t%s\t%s\t%s\t%s\n' % (
                floatToStr(axis[0]),
                floatToStr(axis[2]),
                floatToStr(-axis[1]),
                floatToStr(deg), floatToStr(deg)
            )

            i += 1

        return o

    def _writeKeyframesLoop(self, dataref):
        o = ''

        if self.xplaneObject and self.xplaneObject.datarefs[dataref].loop > 0:
            indent = self.getIndent()
            o += "%s\tANIM_keyframe_loop\t%s\n" % (
                indent,
                self.xplaneObject.datarefs[dataref].loop
            )

        return o

    def _writeTranslationKeyframes(self, dataref):
        debug = getDebug()
        keyframes = self.animations[dataref]
        o = ''
        lastValue = [None, None, None]
        totalTrans = 0
        indent = self.getIndent()

        if debug:
            o += indent + '# translation keyframes\n'

        o += "%sANIM_trans_begin\t%s\n" % (indent, dataref)

        for keyframe in keyframes:
            totalTrans += abs(keyframe.location[0]) + abs(keyframe.location[1]) + abs(keyframe.location[2])

            if lastValue[0] != keyframe.location[0] or lastValue[1] != keyframe.location[1] or lastValue[2] != keyframe.location[2]:
                o += "%sANIM_trans_key\t%s\t%s\t%s\t%s\n" % (
                    indent, floatToStr(keyframe.value),
                    floatToStr(keyframe.location[0]),
                    floatToStr(keyframe.location[2]),
                    floatToStr(-keyframe.location[1])
                )
                lastValue = keyframe.location

        o += self._writeKeyframesLoop(dataref)
        o += "%sANIM_trans_end\n" % indent

        # do not write zero translations
        if totalTrans == 0:
            return ''

        return o

    def _writeAxisAngleRotationKeyframes(self, dataref):
        o = ''
        indent = self.getIndent()
        keyframes = self.animations[dataref]
        lastValue = None
        totalRot = 0

        # TODO: be sure, axis angle axis does not change during keyframes
        axisAngle = (keyframes[0].rotation[1], keyframes[0].rotation[2], keyframes[0].rotation[3])

        o += "%sANIM_rotate_begin\t%s\t%s\t%s\t%s\n" % (
            indent,
            floatToStr(axisAngle[0]),
            floatToStr(axisAngle[2]),
            floatToStr(-axisAngle[1]),
            dataref
        )

        for keyframe in keyframes:
            totalRot += abs(keyframe.value)

            if lastValue != keyframe.value:
                o += "%sANIM_rotate_key\t%s\t%s\n" % (
                    indent,
                    floatToStr(keyframe.value),
                    floatToStr(math.degrees(keyframe.rotation[0]))
                )
                lastValue = keyframe.value

        o += self._writeKeyframesLoop(dataref)
        o += "%sANIM_rotate_end\n" % indent

        # do not write zero rotations
        if totalRot == 0:
            return ''

        return o

    def _writeQuaternionRotationKeyframes(self, dataref):
        debug = getDebug()
        keyframes = self.animations[dataref]
        o = ''
        indent = self.getIndent()

        if debug:
            o += indent + '# WARNING: Quaternion rotations are not supported yet (Please use Axis Angle or Euler instead)\n'

        # TODO: convert to axis angle
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToAngle/
        # public void set(Quat4d q1) {
        #    if (q1.w > 1) q1.normalise(); // if w>1 acos and sqrt will produce errors, this cant happen if quaternion is normalised
        #    angle = 2 * Math.acos(q1.w);
        #    double s = Math.sqrt(1-q1.w*q1.w); // assuming quaternion normalised then w is less than 1, so term always positive.
        #    if (s < 0.001) { // test to avoid divide by zero, s is always positive due to sqrt
        #      // if s close to zero then direction of axis not important
        #      x = q1.x; // if it is important that axis is normalised then replace with x=1; y=z=0;
        #      y = q1.y;
        #      z = q1.z;
        #    } else {
        #      x = q1.x / s; // normalise axis
        #      y = q1.y / s;
        #      z = q1.z / s;
        #    }
        # }
        return o

    def _writeEulerRotationKeyframes(self, dataref):
        debug = getDebug()
        keyframes = self.animations[dataref]
        o = ''
        indent = self.getIndent()
        rotationMode = keyframes[0].rotationMode
        eulerAxisMap = {
            'ZYX': (2, 1, 0),
            'ZXY': (2, 0, 1),
            'YZX': (1, 2, 0),
            'YXZ': (1, 0, 2),
            'XZY': (0, 2, 1),
            'XYZ': (0, 1, 2)
        }
        eulerAxes = [(1.0,.0,0.0), (0.0,1.0,0.0), (0.0,0.0,1.0)]
        axes = eulerAxisMap[rotationMode]
        totalRot = 0

        for axis in axes:
            lastValue = None

            o += "%sANIM_rotate_begin\t%s\t%s\t%s\t%s\n" % (
                indent,
                floatToStr(eulerAxes[axis][0]),
                floatToStr(eulerAxes[axis][2]),
                floatToStr(-eulerAxes[axis][1]),
                dataref
            )

            for keyframe in keyframes:
                totalRot += abs(keyframe.value)

                if lastValue != keyframe.value:
                    o += "%sANIM_rotate_key\t%s\t%s\n" % (
                        indent,
                        floatToStr(keyframe.value),
                        floatToStr(math.degrees(keyframe.rotation[axis]))
                    )
                    lastValue = keyframe.value

            o += self._writeKeyframesLoop(dataref)
            o += "%sANIM_rotate_end\n" % indent

        # do not write zero rotations
        if totalRot == 0:
            return ''

        return o

    def _writeRotationKeyframes(self, dataref):
        debug = getDebug()
        keyframes = self.animations[dataref]
        o = ''
        indent = self.getIndent()

        if debug:
            o += indent + '# rotation keyframes\n'

        rotationMode = keyframes[0].rotationMode

        if rotationMode == 'AXIS_ANGLE':
            o += self._writeAxisAngleRotationKeyframes(dataref)
        elif rotationMode == 'QUATERNION':
            o += self._writeQuaternionRotationKeyframes(dataref)
        else:
            o += self._writeEulerRotationKeyframes(dataref)

        return o

    def writeKeyframes(self, dataref):
        o = ''
        o += self._writeTranslationKeyframes(dataref)
        o += self._writeRotationKeyframes(dataref)

        return o

    def writeAnimationSuffix(self):
        o = ''

        if not self.isAnimated():
            return o

        # unanimated bones do not export any suffix
        preMatrix = self.getPreAnimationMatrix()
        postMatrix = self.getPostAnimationMatrix()

        if postMatrix is not preMatrix:
            indent = self.getIndent()
            o += indent + 'ANIM_end\n'

        return o