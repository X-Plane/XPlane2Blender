import bpy
import copy

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
    #   XPlaneObject xplaneObject - A <XPlaneObject>.
    def __init__(self, keyframe, index, dataref, xplaneBone):
        currentFrame = bpy.context.scene.frame_current
        self.value = keyframe.co[1]
        self.dataref = dataref
        self.index = index

        if xplaneBone.blenderBone:
            # we need the pose bone
            blenderObject = xplaneBone.blenderObject.pose.bones[xplaneBone.blenderBone.name]
        else:
            blenderObject = xplaneBone.blenderObject

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame = self.frame)

        self.location = copy.copy(blenderObject.location)
        self.location[0] = round(self.location[0],KEYFRAME_PRECISION)
        self.location[1] = round(self.location[1],KEYFRAME_PRECISION)
        self.location[2] = round(self.location[2],KEYFRAME_PRECISION)
        self.rotation = None
        self.rotationMode = blenderObject.rotation_mode

        # TODO: rotationMode should reside in keyframes collection as it is the same for each keyframe
        if self.rotationMode == 'QUATERNION':
            self.rotation = blenderObject.rotation_quaternion.copy()
        elif self.rotationMode == 'AXIS_ANGLE':
            rot = blenderObject.rotation_axis_angle
            self.rotation = (round(rot[0],KEYFRAME_PRECISION), rot[1], rot[2], rot[3])
        else:
            self.rotation = blenderObject.rotation_euler.copy()
            self.rotation[0] = round(self.rotation[0],KEYFRAME_PRECISION)
            self.rotation[1] = round(self.rotation[1],KEYFRAME_PRECISION)
            self.rotation[2] = round(self.rotation[2],KEYFRAME_PRECISION)

        self.scale = copy.copy(blenderObject.scale)
        bpy.context.scene.frame_set(frame = currentFrame)

    def __str__(self):
        return "Value=%f Dataref=%s bone=%s rotation_mode=%s trans=(%f,%f,%f) rot=(%f,%f,%f)" % (
            self.value, self.dataref, self.rotationMode,
                self.translation[0],self.translation[1],self.translation[2],
                self.rotation[0],self.rotation[1],self.rotation[2])
