"""
About the XPlaneBone/XPlaneObject API
=====================================
XPlane2Blender makes it's own hierarchy of Blender objects,
which under most circumstances looks nearly identical
to the Blender hierarchy in the outliner.

However, where as the Blender Outliner is focused on Collections and Objects and the parent-child
connections between them, the XPlane2Blender hierarchy is focused on a tree
structure of XPlaneBones with XPlaneObjects optionally associated with them.

XPlane2Blender primarily uses this tree to make animations

Rules:
- XPlaneBones are made for the Root Collection and every Object and Armature Bone encountered
- XPlaneBones will not have an XPlaneObject if the Blender Object is unconvertible (such as the root collection, camera, and sound emitters)
- Every XPlaneBone (except the Root Bone under collections) must have a Blender Object associated with it
- Every Blender Object appears in the XPlaneBone Tree exactly once

Special Collection Rules:
- The root bone will have no Blender Object or XPlaneObject associated with it

Because XPlaneBones represent different relationships than Blender's parent-child
relationships, it cannot be assumed that the XPlaneBone Tree and Blender Hierarchy are the same.

**Therefore, all APIs should use the XPlaneBone tree's version of parent and child lookups instead of the Blender's!**
"""

import math
from typing import Dict, List, Optional, Tuple

import bpy
import mathutils

from io_xplane2blender import xplane_constants, xplane_props
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import floatToStr, logger, vec_b_to_x
from io_xplane2blender.xplane_types.xplane_keyframe import XPlaneKeyframe
from io_xplane2blender.xplane_types.xplane_keyframe_collection import (
    XPlaneKeyframeCollection,
)

# from xplane_object import XPlaneObject


class XPlaneBone:
    def __init__(
        self,
        xplane_file: "XPlaneFile",
        blender_obj: Optional[bpy.types.Object],
        blender_bone: Optional[bpy.types.Bone] = None,
        xplane_obj: Optional["XPlaneObject"] = None,
        parent_xplane_bone: Optional["XPlaneBone"] = None,
    ):
        """
        self.blenderObject is the Blender Object associated with this XPlaneBone (according to our traversal of the Blender hierarchy).
        It is only None for the root XPlaneBone of an Exportable Collection

        self.blenderBone is the Blender Bone associated with this XPlaneBone (if the origin during traversal was a bpy.types.Bone)
        Thus, you can tell if something was a Bone by if blenderBone is not None

        XPlaneBone is responsible for tieing the xplane_obj (if any) with this XPlaneBone, and adding
        the us to the parent_xplane_bone's children. This way it is all kept in one place and can't be forgotten
        """
        self.xplaneFile = xplane_file
        self.blenderObject = blender_obj
        self.blenderBone = blender_bone
        self.xplaneObject = xplane_obj
        self.parent = parent_xplane_bone
        self.children: List["XPlaneBone"] = []

        if self.xplaneObject:
            assert (
                self.xplaneObject.blenderObject == self.blenderObject
            ), f"XPlaneBone ({self.blenderObject.name}) and XPlaneObject's blenderObject do not match ({self.blenderObject.name}, {self.xplaneObject.name})"
            self.xplaneObject.xplaneBone = self
            if self.xplaneObject.blenderObject.xplane.override_lods:
                self.xplaneObject.effective_buckets = tuple(
                    self.blenderObject.xplane.lod
                )
            else:

                def find_parent_buckets(
                    parent_xplane_bone: Optional["XPlaneBone"],
                ) -> Tuple[bool, bool, bool, bool]:
                    try:
                        if parent_xplane_bone.xplaneObject:
                            return parent_xplane_bone.xplaneObject.effective_buckets
                        elif parent_xplane_bone.parent:
                            return find_parent_buckets(parent_xplane_bone.parent)
                        else:
                            return (False,) * 4
                    except AttributeError:
                        return (False,) * 4

                self.xplaneObject.effective_buckets = find_parent_buckets(self.parent)

        if self.parent:
            self.parent.children.append(self)

        # dict - The keys are the dataref paths and the values are lists of <XPlaneKeyframeCollection>.
        self.animations: Dict[str, XPlaneKeyframeCollection] = {}

        # IMPORTANT NOTE: Show/Hide Datarefs and datarefs without 2 keyframes will not be included and
        # must be accessed via blenderObject.xplane.datarefs!
        self.datarefs: Dict[str, xplane_props.XPlaneDataref] = {}
        self.collectAnimations()

    def sortChildren(self) -> None:
        def getWeight(xplaneBone) -> int:
            if xplaneBone.xplaneObject:
                return xplaneBone.xplaneObject.weight

            return 0

        self.children.sort(key=getWeight)

    # Method: isAnimatedForTranslation
    # Checks if a dataref's keyframes actually contain meaningful translations, and we should therefore write keyframes out
    def isDataRefAnimatedForTranslation(self) -> bool:
        if hasattr(self, "animations") and len(self.animations) > 0:
            # Check to see if there is at least some difference in the keyframe locations
            for dataref in self.animations:
                keyframes = self.animations[dataref]
                if len(keyframes) > 0:
                    last_keyframe = keyframes[0]
                    for keyframe in keyframes:
                        # if there is a difference
                        if keyframe.location != last_keyframe.location:
                            return True
                        else:
                            last_keyframe = keyframe

        return False

    # Method: isAnimatedForRotation
    # Checks if a dataref's keyframes actually contain meaningful rotation, and we should therefore write keyframes out
    def isDataRefAnimatedForRotation(self) -> bool:
        if hasattr(self, "animations") and len(self.animations) > 0:
            # Check to see if there is at least some difference in the keyframe locations
            for dataref in self.animations:
                keyframes = self.animations[dataref]
                if len(keyframes) > 0:
                    last_keyframe = keyframes[0]
                    for keyframe in keyframes:
                        # if there is a difference
                        if keyframe.rotation != last_keyframe.rotation:
                            return True
                        else:
                            last_keyframe = keyframe

        return False

    def isAnimated(self) -> bool:
        """Uses isDataRefAnimated functions to check if the object is animated"""
        return (
            self.isDataRefAnimatedForTranslation()
            or self.isDataRefAnimatedForRotation()
        )

    def collectAnimations(self) -> None:
        """
        Collects animation_data from blenderObject, and pairs it with xplane datarefs
        """
        if not self.parent:
            return None

        debug = getDebug()

        bone = self.blenderBone
        blenderObject = self.blenderObject

        # check for animation
        # if bone:
        # print("\t\t checking animations of %s:%s" % (blenderObject.name, bone.name))
        # else:
        # print("\t\t checking animations of %s" % blenderObject.name)

        try:
            if bone:
                # bone animation data resides in the armature objects .data block
                fcurves = [
                    f
                    for f in blenderObject.data.animation_data.action.fcurves
                    if f.data_path.startswith(f'bones["{bone.name}"].xplane.datarefs')
                ]
            else:
                fcurves = [
                    f
                    for f in blenderObject.animation_data.action.fcurves
                    if f.data_path.startswith(f"xplane.datarefs")
                ]
        except AttributeError:
            pass
        else:
            for fcurve in fcurves:
                if bone:
                    index = int(
                        fcurve.data_path[
                            len(f'bones["{bone.name}"].xplane.datarefs[') : -len(
                                "].value"
                            )
                        ]
                    )
                else:
                    index = int(
                        fcurve.data_path[len("xplane.datarefs[") : -len("].value")]
                    )

                try:
                    if bone:
                        dataref = bone.xplane.datarefs[index].path
                    else:
                        dataref = blenderObject.xplane.datarefs[index].path
                except IndexError:
                    # Due to a long standing bug in (I think in BONE_OT_remove_xplane_dataref.execute)
                    # sometimes a Bone's fcurve is not properly removed. Any further indexes will also
                    # be wrong.
                    #
                    # TODO: Fix whatever is causing this, but, we'll still need this for old .blend files
                    # - Ted, 6/24/2020
                    return
                else:
                    if len(fcurve.keyframe_points) > 1:
                        if bone:
                            self.datarefs[dataref] = bone.xplane.datarefs[index]
                        else:
                            self.datarefs[dataref] = blenderObject.xplane.datarefs[
                                index
                            ]

                        self.animations[dataref] = XPlaneKeyframeCollection(
                            [
                                XPlaneKeyframe(kf, i, dataref, self)
                                for i, kf in enumerate(fcurve.keyframe_points)
                            ]
                        )

    def getName(self, ignore_indent_level: bool = False) -> str:
        """
        Gets the (optionally) indent level, Blender Type, and name.
        Useful for debugging and error message.

        Note: Unit tests, like the ones in xplane_file,
        test against the output of this method!
        """
        count_parents = (
            lambda bone: 1 + count_parents(bone.parent) if bone.parent else 0
        )
        prefix = "" if ignore_indent_level else f"{count_parents(self)} "

        if self.blenderBone:
            return f"{prefix}Bone: {self.blenderBone.name}"
        elif self.blenderObject:
            return (
                f"{prefix}{self.blenderObject.type.title()}: {self.blenderObject.name}"
            )
        elif self.parent == None:
            return f"{prefix}ROOT"
        else:
            assert (
                False
            ), "XPlaneBone has no Blender Data, but also is not the root. How did we did we get here?"

    def getBlenderName(self) -> str:
        if self.blenderBone:
            return self.blenderBone.name
        elif self.blenderObject:
            return self.blenderObject.name
        else:
            assert False, "Cannot call getBlenderName on a root bone"

    def getIndent(self) -> str:
        count_parents = (
            lambda bone: 1 + count_parents(bone.parent) if bone.parent else 0
        )
        return "\t" * count_parents(self)

    def getFirstAnimatedParent(self) -> Optional[str]:
        if self.parent == None:
            return None

        if self.parent.isAnimated() or self.parent.parent == None:
            return self.parent
        else:
            return self.parent.getFirstAnimatedParent()

    # Blender World Matrix (Pose)
    #
    # This is the absolute final pose of a blender object after _everything_ is taken into account.
    # If we want to emit a mesh, this is where the mesh lives.  The world matrix might be "more"
    # transforms than post-animation if there is a static rotation after a dynamic translation.
    #
    def getBlenderWorldMatrix(self) -> mathutils.Matrix:
        if self.blenderBone:
            # Blender bones in their current pose (which matches the shape of all data
            # blocks 'right now') are stored as a transform in the pose bone relative
            # to the parent armature.  So it's easy to export them:
            poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
            if poseBone:
                return self.blenderObject.matrix_world.copy() @ poseBone.matrix.copy()
            else:
                # FIXME: is there ever not a pose bone for a bone?  Should this be some kind of assert?
                return (
                    self.blenderObject.matrix_world.copy()
                    @ self.blenderBone.matrix_local.copy()
                )
        elif self.blenderObject:
            # Data blocks simply know their world-space location post-transform.
            return self.blenderObject.matrix_world.copy()
        # Root bone gets a special exception: if it has a None blender object, then we are parented to
        # the glboal coordinate system
        elif self.parent == None:
            return mathutils.Matrix.Identity(4)
        else:
            # Wat!?!  We have a non-root bone with NO blender stuff attached.
            raise Exception()

    #
    # THE PRE-ANIMATION MATRIX (POSE)
    #
    # This matrix represents the world space pose in the rest position of this bone _before_
    # its animations are applied.  This is the frame of reference in which the animations are
    # happening.
    #
    # It is only legal to ask for this if (1) a bone is animated and (2) it is not the root
    # bone.
    def getPreAnimationMatrix(self) -> mathutils.Matrix:
        if self.parent == None:
            # No one should ever need the pre-animation matrix of the root bone -
            # we only need this to get a bake matrix between two animations.
            print("Pre-animation requested on root bone - who requested this?")
            raise Exception()
        elif not self.isAnimated():
            # We should not ask for pre and post animation matrices when there is no
            # animation - if we did, the code has failed to optimize something out.
            print(self)
            raise Exception()
        elif self.blenderBone:

            poseBone = self.blenderObject.pose.bones[self.blenderBone.name]

            static_translation = mathutils.Matrix.Identity(4)
            if not self.isDataRefAnimatedForTranslation():
                static_translation = mathutils.Matrix.Translation(
                    poseBone.matrix_basis.to_translation()
                )

            if self.blenderBone.parent and poseBone and poseBone.parent:
                # This special cases a bone that is parented to another bone.  In this case, we have a
                # problem: Blender stores all bones relative to the armature, both in rest and in pose.
                # This doesn't give us access to the bone _after_ its parent's transform but _before_
                # it's own animation.
                #
                # So we construct it ourselves.  r2r is the _relative_ transform from the parent bone
                # to our bone when at rest - in other words, it's the bake matrix from our parent bone to us.
                r2r = (
                    self.blenderBone.parent.matrix_local.inverted_safe()
                    @ self.blenderBone.matrix_local
                )
                # Now we can formulate that the full transform is:
                # 1. Armature's world space
                # 2. Our parent's pose
                # 3. The bake matrix from our parent's pose to us.
                # This gets us up to right before our transform.
                return (
                    self.blenderObject.matrix_world.copy()
                    @ poseBone.parent.matrix.copy()
                    @ r2r
                ) @ static_translation

            # This is the unparented bone case (and any fall-throughs from crazy objects):
            # Simply apply our rest position (relative to the armature) to the armature's current world-space
            # position.
            return (
                self.blenderObject.matrix_world.copy()
                @ self.blenderBone.matrix_local.copy()
                @ static_translation
            )

        elif self.blenderObject:

            # Animated objects are affected by "a bunch of stuff" that Blender does - it's hard to predict what it all is.
            # But data block animation is the LAST thing that happens.  So we can basically take our post-animation pose,
            # back out the known animation, and that's our pre-animation pose.

            # (In previous versions we used to start with the parent and work forward, but this required simulating the
            # parent-child transformation, which involves a bunch of specal logic fo bones.
            # This is more reliable.

            # This is our final post-data block animation pose. (Technically it's MORE than post-animation if we have a dynamic
            # translation and static rotation, for example.)
            my_final = self.getBlenderWorldMatrix()

            # This is all of the transformations (rot,loc,scale) that our data block might do.
            my_block = self.blenderObject.matrix_basis

            # If we are NOT animated for translation and we are here we MUST be animated for rotation.  In this case, we want
            # to treat ONLY the rotation part as "dynamic" - so nuke the translation components.
            if not self.isDataRefAnimatedForTranslation():
                my_block = my_block.to_3x3().to_4x4()

            # This is the "undo" of the dynamic part of our block transform
            before_my_block = my_block.inverted_safe()

            # Final result is our post-animation pose with the dynamic animatons subtracted out.  This will nuke either
            # rotation or rotatio + location.
            return my_final @ before_my_block

    #
    # THE POST-ANIMATION MATRIX (POSE)
    #
    # This matrix represents the world space pose of the bone just after all dynamic animation.  EVERY
    # bone has this, because everything "on" the bone (sub-bones, meshes) is attached to this pose.
    #
    def getPostAnimationMatrix(self) -> mathutils.Matrix:
        if self.parent == None:
            # WARNING: If the root bone has been scaled then the scale does NOT apply to the OBJ.
            # This is probably technically correct based on some insane fine-print reading of export-by-object
            # but may astonish users.
            return (
                self.getBlenderWorldMatrix()
            )  # correctly returns Identity for root bone
        elif not self.isAnimated():
            # No one should be asking or post-animation matrices on _non_-animated bones!
            print(self)
            raise Exception()
        else:
            # Scaling trickery: we have to BACK OUT the scaling of our post-animation matrix...this
            # pushes it into the next bake, which means eventually the mesh vertices themselves get scaled.
            # If we DONT'T do this then scaling "above" an animation won't scale what's below because the code
            # assumes that the entire transform stack is "applied" in the OBJ file before we continue from an
            # animation - and since OBJs don't scale, we can't do that.  Obviously if something that is
            # impossible-in-OBJ happens, the pushed-through scaling will be wrong.
            #
            # Rotation trickery: if our rotation was static, we are goint to back that out of our post-animation too,
            # forcing it into the bake matrix.  This is correct and removes the need for static rotations.

            # First: get our world matrix without ANY scaling.
            world_matrix = self.getBlenderWorldMatrix()
            loc, rot, scale = world_matrix.decompose()
            world_matrix_no_scale = (
                mathutils.Matrix.Translation(loc) @ rot.to_matrix().to_4x4()
            )
            # If there is no scaling, just take our real matrix, don't decompose and recompose.  This aims to
            # avoid floating point crap accumulation
            if scale == mathutils.Vector((1.0, 1.0, 1.0)):
                world_matrix_no_scale = world_matrix

            if not self.isDataRefAnimatedForRotation():
                # No-rotation case: back out ONLY OUR rotation.  Note that our parents rotations and other random
                # rotations are kept in!

                if self.blenderBone:
                    poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
                    our_loc, our_rot, our_scale = poseBone.matrix_basis.decompose()
                else:
                    (
                        our_loc,
                        our_rot,
                        our_scale,
                    ) = self.blenderObject.matrix_basis.decompose()

                our_rot_inv = our_rot.to_matrix().to_4x4().inverted_safe()
                return world_matrix_no_scale @ our_rot_inv
            else:
                return world_matrix_no_scale

    #
    # ANIMATION BAKE MATRIX (DELTA)
    #
    # A bake matrix is a _delta_ - a transformation from one pose to another that is static in the model, and therefore can
    # be implemented by "applying" the transform to the child things, instead of writing it as ANIM_ directives.
    # In other wods, it is a static relative transform that is elligible for 'baking'.
    #
    # Baking is important because without it, the exporter would have to output a ton of transform code for 'highly structured'
    # (but not dynamic) models; with baking, an author can use lots of sub-blocks and relative positioning and still just get
    # triangles.
    #
    # The bake matrix for animations for bone X is the static transform _from X's parent bone to X before its animations.
    # In other words, once we are in X's parent's coordinate system, we need to do this bake to then apply our animations.
    def getBakeMatrixForMyAnimations(self) -> mathutils.Matrix:
        parent_bone = self.getFirstAnimatedParent()
        if parent_bone == None:
            # If we have no parent bone, our bake matrix goes from global coordinates TO our pre-animation pose.
            # This would be more formal if it was inverse(identity) @ getPreAnimationMatrix() - this has been
            # simplifiied.
            return self.getPreAnimationMatrix()
        else:
            # This is the parent transform we are going from
            parent_post = self.getFirstAnimatedParent().getPostAnimationMatrix()
            # This is the child we are going to
            pre = self.getPreAnimationMatrix()
            return parent_post.inverted_safe() @ pre

    # ATTACHENT BAKE MATRIX (DELTA)
    #
    # This bake matrix is the delta from the final bone (post animation) to an actual THING like a mesh or a light.
    #
    # This API gets the bake matrix to be applied to output-able primitives that are attached to -this- bone.
    # In other words, this is a helper for how to bake our lights, meshes, etc.
    #
    def getBakeMatrixForAttached(self) -> mathutils.Matrix:
        # Our anchor bone is the thing we are attached to - it might be us, or it might be our parent.
        if self.isAnimated():
            my_anchor_bone = self  # The anchor bone is the last bone to be animated -
        else:  # We are 'in' its post-animation coordinate system
            my_anchor_bone = self.getFirstAnimatedParent()

        if my_anchor_bone == None:
            # If my anchor bone is _none_, it means that there is both no animation AND no parent
            # bone of ANY kind.  This happens when we do a by-object export and the user sets the
            # mesh data block ITSELF to be a root.  In this case, we are our own coordinate system,
            # so our bake is the identity.
            return mathutils.Matrix.Identity(4)
        else:
            anchor_post_anim = my_anchor_bone.getPostAnimationMatrix()
            my_final_world = self.getBlenderWorldMatrix()
            # Find the relative matrix from the post-animation of our last animated bone to our final post animation transform.
            return anchor_post_anim.inverted_safe() @ my_final_world

    def __str__(self) -> str:
        def toString(bone: "XPlaneBone", indent: str = "") -> str:
            out = indent + bone.getName() + "\n"

            for bone in bone.children:
                out += toString(bone, indent + "\t")

            return out

        out = toString(self)
        return out

    def writeAnimationPrefix(self) -> None:
        debug = getDebug()
        indent = self.getIndent()
        o = ""

        if debug:
            o += indent + "# " + self.getName() + "\n"
            """
            if self.blenderBone:
                poseBone = self.blenderObject.pose.bones[self.blenderBone.name]
                if poseBone != None:
                    o += "# Armature\n" + str(self.blenderObject.matrix_world) + "\n"
                    if self.blenderBone.parent:
                        poseParent = self.blenderObject.pose.bones[self.blenderBone.parent.name]
                        if poseParent:
                            o += "#  parent matrix local rest\n" + str(self.blenderBone.parent.matrix_local) + "\n"
                            o += "#  parent matrix local pose\n" + str(poseParent.matrix) + "\n"
                            o += "#  delta r2r\n" + str(self.blenderBone.parent.matrix_local.inverted_safe() @ self.blenderBone.matrix_local) + "\n"
                            o += "#  delta p2p\n" + str(poseParent.matrix.inverted_safe() @ poseBone.matrix) + "\n"
                    o += "#   matrix local rest\n" + str(self.blenderBone.matrix_local) + "\n"
                    o += "#   matrix local pose\n" + str(poseBone.matrix) + "\n"
                    o += "#   pose delta\n" + str(self.blenderBone.matrix_local.inverted_safe() @ poseBone.matrix) + "\n"
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
            """
        isAnimated = self.isAnimated()
        hasAnimationAttributes = (
            self.xplaneObject != None and len(self.xplaneObject.animAttributes) > 0
        )

        if not isAnimated and not hasAnimationAttributes:
            return o

        # and postMatrix is not preMatrix
        if (isAnimated) or hasAnimationAttributes:
            o += indent + "ANIM_begin\n"

        if isAnimated:  # and postMatrix is not preMatrix:
            # write out static translations of bake
            bakeMatrix = self.getBakeMatrixForMyAnimations()
            o += self._writeStaticTranslation(bakeMatrix)
            o += self._writeStaticRotation(bakeMatrix)

            for dataref in sorted(list(self.animations.keys())):
                o += self._writeTranslationKeyframes(dataref)
            for dataref in sorted(list(self.animations.keys())):
                o += self._writeRotationKeyframes(dataref)

        o += self._writeAnimAttributes()

        return o

    def _writeStaticTranslation(self, bakeMatrix: mathutils.Matrix) -> None:
        debug = getDebug()
        indent = self.getIndent()
        o = ""

        bakeMatrix = bakeMatrix

        translation = bakeMatrix.to_translation()
        translation[0] = round(translation[0], 5)
        translation[1] = round(translation[1], 5)
        translation[2] = round(translation[2], 5)

        # ignore noop translations
        if translation[0] == 0 and translation[1] == 0 and translation[2] == 0:
            return o

        if debug:
            o += indent + "# static translation\n"

        o += indent + "ANIM_trans\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            floatToStr(translation[0]),
            floatToStr(translation[2]),
            floatToStr(-translation[1]),
            floatToStr(translation[0]),
            floatToStr(translation[2]),
            floatToStr(-translation[1]),
        )

        return o

    def _writeStaticRotation(self, bakeMatrix: mathutils.Matrix) -> str:
        debug = getDebug()
        indent = self.getIndent()
        o = ""
        bakeMatrix = bakeMatrix
        rotation = list(
            map(
                lambda c: round(c, xplane_constants.PRECISION_KEYFRAME),
                bakeMatrix.to_euler("XYZ"),
            )
        )

        # ignore noop rotations
        if rotation == (0, 0, 0):
            return o

        if debug:
            o += indent + "# static rotation\n"

        # Ben says: this is SLIGHTLY counter-intuitive...Blender axes are
        # globally applied in a Euler, so in our XYZ, X is affected -by- Y
        # and both are affected by Z.
        #
        # Since X-Plane works opposite this, we are going to apply the
        # animations exactly BACKWARD! ZYX.  The order here must
        # be opposite the decomposition order above.
        #
        # Note that since our axis naming is ALSO different this will
        # appear in the OBJ file as Y -Z X.
        #
        # see also: http://hacksoflife.blogspot.com/2015/11/blender-notepad-eulers.html

        axes = (2, 1, 0)
        eulerAxes = [(0, 0, 1), (0, 1, 0), (1, 0, 0)]

        for i, axis in enumerate(eulerAxes):
            deg = math.degrees(rotation[axes[i]])

            # ignore zero rotation
            if not round(deg, xplane_constants.PRECISION_KEYFRAME) == 0:
                tab = "\t"
                o += (
                    f"{indent}ANIM_rotate"
                    f"\t{tab.join(map(floatToStr,vec_b_to_x(axis)))}"
                    f"\t{tab.join(map(floatToStr, [deg, deg]))}\n"
                )

        return o

    def _writeKeyframesLoop(self, dataref: str) -> str:
        o = ""

        if dataref in self.datarefs:
            if self.datarefs[dataref].loop > 0:
                indent = self.getIndent()
                o += f"{indent}\tANIM_keyframe_loop\t{self.datarefs[dataref].loop}\n"
        return o

    def _writeTranslationKeyframes(self, dataref: str) -> str:
        debug = getDebug()
        keyframes = self.animations[dataref]

        o = ""

        if not self.isDataRefAnimatedForTranslation():
            return o

        # Apply scaling to translations
        pre_loc, pre_rot, pre_scale = self.getPreAnimationMatrix().decompose()

        totalTrans = 0
        indent = self.getIndent()

        if debug:
            o += f"{indent}# translation keyframes\n"

        o += f"{indent}ANIM_trans_begin\t{dataref}\n"

        for keyframe in keyframes:
            totalTrans += sum(map(abs, keyframe.location))

            o += (
                f"{indent}ANIM_trans_key"
                f"\t{floatToStr(keyframe.dataref_value)}"
                f"\t{floatToStr(keyframe.location[0] * pre_scale[0])}"
                f"\t{floatToStr(keyframe.location[2] * pre_scale[2])}"
                f"\t{floatToStr(-keyframe.location[1] * pre_scale[1])}"
                f"\n"
            )

        o += self._writeKeyframesLoop(dataref)
        o += f"{indent}ANIM_trans_end\n"

        # do not write zero translations
        if totalTrans == 0:
            return ""

        return o

    def _writeAxisAngleRotationKeyframes(self, dataref, keyframes) -> str:
        o = ""
        indent = self.getIndent()
        totalRot = 0

        # our reference axis (or axes)
        axes, final_rotation_mode = keyframes.getReferenceAxes()

        if len(axes) == 3:
            # decompose to eulers and return euler rotation instead
            o = self._writeEulerRotationKeyframes(dataref, keyframes.asEuler())
            return o
        elif len(axes) == 1:
            refAxis = axes[0]

        tab = "\t"
        o += (
            f"{indent}ANIM_rotate_begin"
            f"\t{tab.join(map(floatToStr, vec_b_to_x(refAxis)))}"
            f"\t{dataref}\n"
        )

        for keyframe in keyframes:
            deg = math.degrees(keyframe.rotation[0])
            totalRot += abs(deg)

            o += f"{indent}ANIM_rotate_key\t{floatToStr(keyframe.dataref_value)}\t{floatToStr(deg)}\n"

        o += self._writeKeyframesLoop(dataref)
        o += f"{indent}ANIM_rotate_end\n"

        # do not write zero rotations
        if round(totalRot, xplane_constants.PRECISION_KEYFRAME) == 0:
            return ""

        return o

    def _writeQuaternionRotationKeyframes(self, dataref, keyframes) -> str:
        # Writing axis angle will automatically convert quaternions to AA and write it
        return self._writeAxisAngleRotationKeyframes(dataref, keyframes.asAA())

    def _writeEulerRotationKeyframes(self, dataref, keyframes) -> str:
        debug = getDebug()
        o = ""
        indent = self.getIndent()
        axes, final_rotation_mode = keyframes.getReferenceAxes()
        totalRot = 0

        for axis, order in zip(
            axes, XPlaneKeyframeCollection.EULER_AXIS_ORDERING[final_rotation_mode]
        ):
            ao = ""
            totalAxisRot = 0

            tab = "\t"
            ao += (
                f"{indent}ANIM_rotate_begin"
                f"\t{tab.join(map(floatToStr, vec_b_to_x(axis)))}"
                f"\t{dataref}\n"
            )

            for keyframe in keyframes:
                deg = math.degrees(keyframe.rotation[order])
                totalRot += abs(deg)
                totalAxisRot += abs(deg)
                ao += f"{indent}ANIM_rotate_key\t{floatToStr(keyframe.dataref_value)}\t{floatToStr(deg)}\n"

            ao += self._writeKeyframesLoop(dataref)
            ao += f"{indent}ANIM_rotate_end\n"

            # do not write non-animated axis
            if round(totalAxisRot, xplane_constants.PRECISION_KEYFRAME) > 0:
                o += ao

        # do not write zero rotations
        if round(totalRot, xplane_constants.PRECISION_KEYFRAME) == 0:
            return ""

        return o

    def _writeRotationKeyframes(self, dataref) -> str:
        debug = getDebug()
        keyframes = self.animations[dataref]
        o = ""

        if not self.isDataRefAnimatedForRotation():
            return o

        if debug:
            o += f"{self.getIndent()}# rotation keyframes\n"

        rotationMode = keyframes[0].rotationMode

        if rotationMode == "AXIS_ANGLE":
            o += self._writeAxisAngleRotationKeyframes(dataref, keyframes)
        elif rotationMode == "QUATERNION":
            o += self._writeQuaternionRotationKeyframes(dataref, keyframes)
        else:
            o += self._writeEulerRotationKeyframes(dataref, keyframes)

        return o

    def _writeAnimAttributes(self) -> str:
        o = ""

        if self.xplaneObject == None:
            return o

        for name in self.xplaneObject.animAttributes:
            attr = self.xplaneObject.animAttributes[name]
            for i in range(len(attr.value)):
                o += f"{self.getIndent()}{attr.name}\t{attr.getValueAsString(i=i)}\n"

        return o

    def writeAnimationSuffix(self) -> str:
        o = ""
        isAnimated = self.isAnimated()
        hasAnimationAttributes = (
            self.xplaneObject != None and len(self.xplaneObject.animAttributes) > 0
        )

        if not isAnimated and not hasAnimationAttributes:
            return o

        if (isAnimated) or hasAnimationAttributes:
            o += f"{self.getIndent()}ANIM_end\n"

        return o
