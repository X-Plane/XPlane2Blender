import bpy

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
            blenderObject = self.xplaneBone.blenderBone
        else:
            blenderObject = self.xplaneBone.blenderObject

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame = self.frame)

        # update objects so we get values from the keyframe
        #blenderObject.update()

        self.location = blenderObject.location
        self.rotation = None
        self.rotationMode = blenderObject.rotation_mode

        if self.rotationMode == 'QUATERNION':
            self.rotation = blenderObject.rotation_quaternion
        elif self.rotationMode == 'AXIS_ANGLE':
            self.rotation = blenderObject.rotation_axis_angle
        else:
            self.rotation = blenderObject.rotation_euler

        self.scale = blenderObject.scale
