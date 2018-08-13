import copy
from typing import Tuple

import bpy
import mathutils

KEYFRAME_PRECISION = 5

# Class: XPlaneKeyframe
# A Keyframe.
class XPlaneKeyframe():
    '''
    Property: dataref
    string - The Path of the dataref this keyframe refers to.

    Property: frame
    int - The frame in Blender's timeline this keyframe belongs to

    Property: index
    int - The index of this keyframe in the <object> keyframe list.

    Property: location
    Vector - The location recorded in this keyframe

    Property: object
    XPlaneObject - The <XPlaneObject> this keyframe belongs to.

    Property: rotation
    Euler or list [w,x,y,z] - The rotation recorded in this keyframe, in the data structure of it's rotation mode

    Property: rotationMode
    str - The rotation mode used to make this animation, one of "QUATERNION", "AXIS_ANGLE", or a combination of "X","Y", and "Z"
    It is kept in sync with how rotation is statefully (regretfully) changed. Probably buggy.
 
    Property: scale
    list - [x,y,z] With scale of the <object> in this keyframe.

    Property: value
    float - Contains the Dataref value in this keyframe.
    '''

    # Constructor: __init__
    # Caclulates <translation>, <rotation> and <scale>.
    #
    # Parameters:
    #   keyframe - A Blender keyframe
    #   int index - The index of this keyframe in the <object> keyframe list.
    #   string dataref - Path of the dataref this keyframe refers to.
    #   XPlaneBone xplaneBone - An <XPlaneBone>
    def __init__(self, keyframe, index, dataref, xplaneBone):
        currentFrame = bpy.context.scene.frame_current
        self.dataref = dataref
        self.index = index
        self.value = keyframe.co[1]

        if xplaneBone.blenderBone:
            # we need the pose bone
            blenderObject = xplaneBone.blenderObject.pose.bones[xplaneBone.blenderBone.name]
        else:
            blenderObject = xplaneBone.blenderObject

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame = self.frame)

        self.location = mathutils.Vector([round(comp,KEYFRAME_PRECISION) for comp in copy.copy(blenderObject.location)])
        assert isinstance(self.location,mathutils.Vector)
		
        # Child bones with a parent and connection need to ignore the translation field -
        # Blender disables it in the UI and ignores it but does NOT clear out old data,
        # so we have to!
        if xplaneBone.blenderBone:
            if xplaneBone.blenderBone.use_connect and xplaneBone.blenderBone.parent:
                self.location[0] = 0
                self.location[1] = 0
                self.location[2] = 0
		
        self.rotationMode = blenderObject.rotation_mode

        if self.rotationMode == 'QUATERNION':
            self.rotation = blenderObject.rotation_quaternion.copy()
            assert isinstance(self.rotation, mathutils.Quaternion)

        elif self.rotationMode == 'AXIS_ANGLE':
            rot = blenderObject.rotation_axis_angle
            # Why tuple(angle, axis) when the thing is called axis_angle? Different Blender functions call for arbitrary
            # arrangements of this, so my priority was whatever is easiest to convert, not what I like.
            self.rotation = (round(rot[0],KEYFRAME_PRECISION), mathutils.Vector(rot[1:])) # type: Tuple[float,mathutils.Vector]
            assert isinstance(self.rotation,tuple)
            assert len(self.rotation) == 2
            for comp in self.rotation[1]:
                assert isinstance(comp, float)
        else:
            angles = [round(comp,KEYFRAME_PRECISION) for comp in blenderObject.rotation_euler.copy()]
            order = blenderObject.rotation_euler.order
            self.rotation = mathutils.Euler(angles,order)
            assert isinstance(self.rotation, mathutils.Euler)

        self.scale = copy.copy(blenderObject.scale)
        bpy.context.scene.frame_set(frame = currentFrame)

    def __str__(self):
    	# TODO: We aren't printing out the bone, or saving it, because we haven't solved the deepcopy
    	# of xplaneBone. Currently, that just poses an issue for debugging (and if all you need is the name
    	# of the bone to track it down, you can certainly store the name!)
        return "Value={} Dataref={} Rotation Mode={} Rotation=({}) Location=({})".format(
            self.value, self.dataref, self.rotationMode, self.rotation, self.location)

    def asAA(self):
        keyframe = copy.deepcopy(self)

        if self.rotationMode == "AXIS_ANGLE":
            pass
        elif self.rotationMode == "QUATERNION":
            axisAngle = keyframe.rotation.normalized().to_axis_angle()
            keyframe.rotation = (axisAngle[1], axisAngle[0])
        else:
            rotation = keyframe.rotation
            euler_axis = mathutils.Euler((rotation.x,rotation.y,rotation.z),rotation.order)

            # Very annoyingly, to_axis_angle and blenderObject.rotation_axis_angle disagree
            # about (angle, axis_x, axis_y, axis_z) vs (axis, (angle))
            new_rotation = euler_axis.to_quaternion().to_axis_angle()
            new_rotation_axis  = new_rotation[0]
            new_rotation_angle = new_rotation[1]
            keyframe.rotation = (new_rotation_angle, new_rotation_axis)

        keyframe.rotationMode = "AXIS_ANGLE"
        assert isinstance(keyframe.rotation,tuple)
        assert isinstance(keyframe.rotation[0],float)
        assert isinstance(keyframe.rotation[1],mathutils.Vector)
        assert len(keyframe.rotation[1]) == 3
        return keyframe
        
    def asEuler(self):
        keyframe = copy.deepcopy(self)
        if self.rotationMode == "AXIS_ANGLE":
            angle = keyframe.rotation[0]
            axis = keyframe.rotation[1]
            # Why the heck XZY?  Jonathan's 2.49 exporter decomposes Eulers using XYZ (because that is the ONLY
            # decomposition available in 2.49), but it does so in X-Plane space.  So this is an axis renaming
            # (since we alway work in Blender space) so that it comes out the same in X-Plane.
            keyframe.rotation = mathutils.Quaternion(axis, angle).to_euler('XZY')
            keyframe.rotationMode = keyframe.rotation.order
            return keyframe
        elif self.rotationMode == "QUATERNION":
            keyframe.rotation = keyframe.rotation.to_euler('XZY')
            keyframe.rotationMode = keyframe.rotation.order
            return keyframe
        else:
            return keyframe
            
    def asQuaternion(self):
        keyframe = copy.deepcopy(self)
        if self.rotationMode == "AXIS_ANGLE":
            angle = keyframe.rotation[0]
            axis = keyframe.rotation[1]
            keyframe.rotation = mathutils.Quaternion(axis, angle)
            keyframe.rotationMode = "QUATERNION"
            return keyframe
        elif self.rotationMode == "QUATERNION":
            return keyframe
        else:
            keyframe.rotation = keyframe.rotation.to_quaternion()
            keyframe.rotationMode = "QUATERNION"
            return keyframe
