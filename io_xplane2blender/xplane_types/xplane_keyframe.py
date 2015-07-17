import bpy
import copy

# Class: XPlaneKeyframe
# A Keyframe.
class XPlaneKeyframe():
    # Property: object
    # XPlaneObject - The <XPlaneObject> this keyframe belongs to.

    # Property: value
    # float - Contains the Dataref value in this keyframe.

    # Property: dataref
    # string - The Path of the dataref this keyframe refers to.

    # Property: translation
    # list - [x,y,z] With translations of the <object> relative to the <object> rest position (frame 1).

    # Property: rotation
    # list - [x,y,z] With rotation angles of the <object> in this keyframe.

    # Property: scale
    # list - [x,y,z] With scale of the <object> in this keyframe.

    # Property: index
    # int - The index of this keyframe in the <object> keyframe list.

    # Constructor: __init__
    # Caclulates <translation>, <rotation> and <scale>.
    #
    # Parameters:
    #   keyframe - A Blender keyframe
    #   int index - The index of this keyframe in the <object> keyframe list.
    #   string dataref - Path of the dataref this keyframe refers to.
    #   XPlaneObject xplaneObject - A <XPlaneObject>.
    def __init__(self, keyframe, index, dataref, xplaneBone):
        self.value = keyframe.co[1]
        self.dataref = dataref
        self.translation = [0.0,0.0,0.0]
        self.rotation = [0.0,0.0,0.0]
        self.scale = [0.0,0.0,0.0]
        self.index = index
        self.xplaneBone = xplaneBone

        if self.xplaneBone.blenderBone:
            # we need the pose bone
            blenderObject = self.xplaneBone.blenderObject.pose.bones[self.xplaneBone.blenderBone.name]
        else:
            blenderObject = self.xplaneBone.blenderObject

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame = self.frame)

        self.location = copy.copy(blenderObject.location)
        self.rotation = None
        self.rotationMode = blenderObject.rotation_mode

        # TODO: rotationMode should reside in keyframes collection as it is the same for each keyframe
        if self.rotationMode == 'QUATERNION':
            self.rotation = blenderObject.rotation_quaternion.copy()
        elif self.rotationMode == 'AXIS_ANGLE':
            rot = blenderObject.rotation_axis_angle
            self.rotation = (rot[0], rot[1], rot[2], rot[3])
        else:
            self.rotation = blenderObject.rotation_euler.copy()

        self.scale = copy.copy(blenderObject.scale)
