# import bpy
# import math
import mathutils
import math
from .xplane_keyframe import XPlaneKeyframe
from ..xplane_config import getDebug
from ..xplane_helpers import floatToStr, FLOAT_PRECISION, logger

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

    def sortChildren(self):
        def getWeight(xplaneBone):
            if xplaneBone.xplaneObject:
                return xplaneBone.xplaneObject.weight

            return 0

        self.children.sort(key = getWeight)

    # Method: isAnimated
    # Checks if the object is animated.
    #
    # Returns:
    #   bool - True if bone is animated, False if not.
    def isAnimated(self):
        return (hasattr(self, 'animations') and len(self.animations) > 0) or \
               (self.xplaneObject != None and len(self.xplaneObject.animAttributes) > 0)

    # Method: collectAnimations
    # Stores all animations in <animations>.
    def collectAnimations(self):
        if not self.parent:
            return None

        debug = getDebug()

        bone = self.blenderBone
        blenderObject = self.blenderObject

        # if bone:
        #     groupName = "XPlane Datarefs " + bone.name
        # else:
        #     groupName = "XPlane Datarefs"

        #check for animation
        if bone:
            logger.info("\t\t checking animations of %s:%s" % (blenderObject.name, bone.name))
        else:
            logger.info("\t\t checking animations of %s" % blenderObject.name)

        animationData = blenderObject.animation_data

        # bone animation data resides in the armature objects .data block
        if bone:
            animationData = blenderObject.data.animation_data

        if (animationData != None and animationData.action != None and len(animationData.action.fcurves) > 0):
            logger.info("\t\t animation found")
            #check for dataref animation by getting fcurves with the dataref group
            for fcurve in animationData.action.fcurves:
                logger.info("\t\t checking FCurve %s Group: %s" % (fcurve.data_path, fcurve.group))
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

                    # FIXME: removed datarefs keep fcurves, so we have to check if dataref is still there.
                    # FCurves have to be deleted correctly.
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

                    logger.info("\t\t adding dataref animation: %s" % dataref)

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
                            logger.info("\t\t adding keyframe: %6.3f" % keyframe.co[0])
                            keyframes.append(keyframe)

                        # sort keyframes by frame number
                        keyframesSorted = sorted(keyframes, key = lambda keyframe: keyframe.co[0])

                        for i in range(0, len(keyframesSorted)):
                            self.animations[dataref].append(XPlaneKeyframe(keyframesSorted[i], i, dataref, self))

    def getName(self):
        if self.blenderBone:
            return '%d Bone: %s' % (self.level, self.blenderBone.name)
        elif self.blenderObject:
            return '%d Object: %s' % (self.level, self.blenderObject.name)
        elif self.parent == None:
            return '%d ROOT' % self.level

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
            # Blender bones in their current pose (which matches the shape of all data
            # blocks 'right now') are stored as a transform in the pose bone relative
            # to the parent armature.  So it's easy to export them:
            poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
            if poseBone:
                return self.blenderObject.matrix_world.copy() * poseBone.matrix.copy()
            else:
                # FIXME: is there ever not a pose bone for a bone?  Should this be some kind of assert?
                return self.blenderObject.matrix_world.copy() * self.blenderBone.matrix_local.copy()
        elif self.blenderObject:
            # Data blocks simply know their world-space location post-transform.
            return self.blenderObject.matrix_world.copy()

    def getPreAnimationMatrix(self):
        if not self.isAnimated() or self.parent == None:
            # not animated objects have own world matrix
            return self.getBlenderWorldMatrix()
        elif self.blenderBone:

            poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
            if self.blenderBone.parent and poseBone and poseBone.parent:
                # This special cases a bone that is parented to another bone.  In this case, we have a
                # problem: Blender stores all bones relative to the armature, both in rest and in pose.
                # This doesn't give us access to the bone _after_ its parent's transform but _before_
                # it's own animation.
                #
                # So we construct it ourselves.  r2r is the _relative_ transform from the parent bone
                # to our bone when at rest - in other words, it's the bake matrix from our parent bone to us.
                r2r = self.blenderBone.parent.matrix_local.inverted_safe() * self.blenderBone.matrix_local
                # Now we can formulate that the full transform is:
                # 1. Armature's world space
                # 2. Our parent's pose
                # 3. The bake matrix from our parent's pose to us.
                # This gets us up to right before our transform.
                return (self.blenderObject.matrix_world.copy() * poseBone.parent.matrix.copy() * r2r)

            # This is the unparented bone case (and any fall-throughs from crazy objects):
            # Simply apply our rest position (relative to the armature) to the armature's current world-space
            # position.
            return self.blenderObject.matrix_world.copy() * self.blenderBone.matrix_local.copy()

        elif self.blenderObject:
            # animated objects have parents world matrix * inverse of parents matrix
            # matrix_parent_inverse is a static arbitrary transform applied at parenting time to keep
            # objects from "jumping".  Without this, Blender would have to edit key frame tables on parenting.
            return self.parent.getBlenderWorldMatrix() * self.blenderObject.matrix_parent_inverse

    def getPostAnimationMatrix(self):
        # for non-animated or root bones, post = pre
        if not self.isAnimated() or self.parent == None:
            # FIXME: Ben syas - this is just calling getBlenderWorldMatrix.  I think getBlenderWorldMatrix
            # _is_ the post-animation matrix in pretty much all cases; we should merge these routines.
            return self.getPreAnimationMatrix()
        else:
            return self.getBlenderWorldMatrix()

    # This API returns the bake matrix that is applied _to_ the animations of this bone itself.  In other words,
    # this is what we bake our own animation prefix with.  This should NOT be called by other code!
    def getBakeMatrixForMyAnimations(self):
        if self.parent == None:
            # If our pre-animation matrix contains a static transform we still need it?
            return self.getBlenderWorldMatrix()
        else:
            return self.getFirstAnimatedParent().getPostAnimationMatrix().inverted_safe() * self.getPreAnimationMatrix()

    #
    # This API gets the bake matrix to be applied to output-able primitives that are attached to -this- bone.
    # In other words, this is a helper for how to bake our lights, meshes, etc.
    #
    def getBakeMatrixForAttached(self):
        # In the case where we have to bake for an attached object, we are looking for a relative matrix...
        #  From: the end of the last animation we output
        #  To: the transform of the actual 'thing' we are going to output.
        #
        # This code assumes that the data block that the primitive sits in _is_ its parent bone.
        # In the future, maybe we pass in the data block of the exportable primitive.
        if self.isAnimated():
            my_anchor_bone = self                           # The anchor bone is the last bone to be animated -
        else:                                               # We are 'in' its post-animation coordinate system
            my_anchor_bone = self.getFirstAnimatedParent()

        if my_anchor_bone == None:
            # If there's no animation, just get to our post-animation xform.
            return self.getPostAnimationMatrix()
        else:
            # Find the relative matrix from the post-animation of our last animated bone to our final post animation transform.
            return my_anchor_bone.getPostAnimationMatrix().inverted_safe() * self.getPostAnimationMatrix()

    def __str__(self):
        return self.toString()

    def _axisAngleRotationKeyframesToEuler(self, keyframes):
        for keyframe in keyframes:
            rotation = keyframe.rotation
            axis = mathutils.Vector((rotation[1], rotation[2], rotation[3]))
            keyframe.rotationMode = 'XYZ'
            keyframe.rotation = mathutils.Quaternion(axis, rotation[0]).to_euler('XYZ')

        return keyframes

    def writeAnimationPrefix(self):
        debug = getDebug()
        indent = self.getIndent()
        o = ''

        if debug:
            o += indent + '# ' + self.getName() + '\n'
            '''
            if self.blenderBone:
                poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
                if poseBone != None:
                    o += "# Armature\n" + str(self.blenderObject.matrix_world) + "\n"
                    if self.blenderBone.parent:
                        poseParent = self.blenderObject.pose.bones[self.blenderBone.parent.name]
                        if poseParent:
                            o += "#  parent matrix local rest\n" + str(self.blenderBone.parent.matrix_local) + "\n"
                            o += "#  parent matrix local pose\n" + str(poseParent.matrix) + "\n"
                            o += "#  delta r2r\n" + str(self.blenderBone.parent.matrix_local.inverted_safe() * self.blenderBone.matrix_local) + "\n"
                            o += "#  delta p2p\n" + str(poseParent.matrix.inverted_safe() * poseBone.matrix) + "\n"
                    o += "#   matrix local rest\n" + str(self.blenderBone.matrix_local) + "\n"
                    o += "#   matrix local pose\n" + str(poseBone.matrix) + "\n"
                    o += "#   pose delta\n" + str(self.blenderBone.matrix_local.inverted_safe() * poseBone.matrix) + "\n"
            elif self.blenderObject != None:
                o += "# Data block\n" + str(self.blenderObject.matrix_world) + "\n"

            # Debug code - this dumps the pre/post/bake matrix for every single xplane bone into the file.

            p = self
            while p != None:
               o += indent + '#   ' + p.getName() + '\n'
               o += str(p.getPreAnimationMatrix()) + '\n'
               o += str(p.getPostAnimationMatrix()) + '\n'
               o += str(p.getBakeMatrixForMyAnimations()) + '\n'
               p = None
            '''

        if not self.isAnimated():
            return o

        preMatrix = self.getPreAnimationMatrix()
        postMatrix = self.getPostAnimationMatrix()
        bakeMatrix = self.getBakeMatrixForMyAnimations()

        if postMatrix is not preMatrix:
            # write out static translations of bake
            o += indent + 'ANIM_begin\n'

            o += self._writeStaticTranslation(bakeMatrix)
            o += self._writeStaticRotation(bakeMatrix)

        for dataref in self.animations:
            o += self.writeKeyframes(dataref)

        # IMPORTANT: we _do not_ invert out the static translation!  All children of this
        # bone will be taken relative to our final transform, wihch is around the rotation
        # origin!

        #if postMatrix is not preMatrix:
        #    # revert static translations needed for correct rotation origin
        #    o += self._writeStaticTranslation(bakeMatrix, True)

        o += self._writeAnimAttributes()

        return o

    def _writeStaticTranslation(self, bakeMatrix, reverse = False):
        debug = getDebug()
        indent = self.getIndent()
        o = ''

        bakeMatrix = bakeMatrix or self.getBakeMatrixForMyAnimations()

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
        bakeMatrix = bakeMatrix or self.getBakeMatrixForMyAnimations()
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

            # ignore zero rotation
            if not deg == 0:
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

        # our reference axis
        refAxis = None
        refAxisInv = None

        # find reference axis
        for keyframe in keyframes:
            rotation = keyframe.rotation
            axis = mathutils.Vector((rotation[1], rotation[2], rotation[3]))

            if rotation[0] == 0:
                continue
            elif refAxis == None:
                refAxis = axis
                refAxisInv = refAxis * -1
            elif refAxis.x == axis.x and \
                 refAxis.y == axis.y and \
                 refAxis.z == axis.z:
                continue
            elif refAxisInv.x == axis.x and \
                 refAxisInv.y == axis.y and \
                 refAxisInv.z == axis.z:
                keyframe.rotation = rotation * -1
            else:
                # decompose to eulers and return euler rotation instead
                self._axisAngleRotationKeyframesToEuler(keyframes)
                o = self._writeEulerRotationKeyframes(dataref)
                return o

        if refAxis == None:
            refAxis = mathutils.Vector((0, 0, 1))

        o += "%sANIM_rotate_begin\t%s\t%s\t%s\t%s\n" % (
            indent,
            floatToStr(refAxis[0]),
            floatToStr(refAxis[2]),
            floatToStr(-refAxis[1]),
            dataref
        )

        for keyframe in keyframes:
            deg = math.degrees(keyframe.rotation[0])
            totalRot += abs(deg)

            if lastValue != keyframe.value:
                o += "%sANIM_rotate_key\t%s\t%s\n" % (
                    indent,
                    floatToStr(keyframe.value),
                    floatToStr(deg)
                )
                lastValue = keyframe.value

        o += self._writeKeyframesLoop(dataref)
        o += "%sANIM_rotate_end\n" % indent

        # do not write zero rotations
        if round(totalRot, FLOAT_PRECISION) == 0:
            return ''

        return o

    def _writeQuaternionRotationKeyframes(self, dataref):
        keyframes = self.animations[dataref]

        # convert rotations to axis angle
        for keyframe in keyframes:
            axisAngle = keyframe.rotation.normalized().to_axis_angle()
            keyframe.rotation = mathutils.Vector((axisAngle[1], axisAngle[0][0], axisAngle[0][1], axisAngle[0][2]))

        # now simply write axis angle
        return self._writeAxisAngleRotationKeyframes(dataref)

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
            ao = ''
            lastValue = None
            totalAxisRot = 0

            ao += "%sANIM_rotate_begin\t%s\t%s\t%s\t%s\n" % (
                indent,
                floatToStr(eulerAxes[axis][0]),
                floatToStr(eulerAxes[axis][2]),
                floatToStr(-eulerAxes[axis][1]),
                dataref
            )

            for keyframe in keyframes:
                deg = math.degrees(keyframe.rotation[axis])
                totalRot += abs(deg)
                totalAxisRot += abs(deg)

                if lastValue != keyframe.value:
                    ao += "%sANIM_rotate_key\t%s\t%s\n" % (
                        indent,
                        floatToStr(keyframe.value),
                        floatToStr(deg)
                    )
                    lastValue = keyframe.value

            ao += self._writeKeyframesLoop(dataref)
            ao += "%sANIM_rotate_end\n" % indent

            # do not write non-animated axis
            if round(totalAxisRot, FLOAT_PRECISION) > 0:
                o += ao

        # do not write zero rotations
        if round(totalRot, FLOAT_PRECISION) == 0:
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

    def _writeAnimAttributes(self):
        o = ''
        indent = self.getIndent()

        if self.xplaneObject == None:
            return o

        for name in self.xplaneObject.animAttributes:
            attr = self.xplaneObject.animAttributes[name]
            o += indent + '%s\t%s\n' % (attr.name, attr.getValueAsString())

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
