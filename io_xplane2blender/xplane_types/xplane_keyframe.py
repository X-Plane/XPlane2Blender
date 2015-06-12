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
    #   XPlaneObject obj - A <XPlaneObject>.
    def __init__(self,keyframe,index,dataref,obj):
        self.value = keyframe.co[1]
        self.dataref = dataref
        self.translation = [0.0,0.0,0.0]
        self.rotation = [0.0,0.0,0.0]
        self.scale = [0.0,0.0,0.0]
        self.index = index
        self.blenderObject = obj

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame=self.frame)

        # update objects so we get values from the keyframe
        #self.blenderObject.update()

        local = self.blenderObject.getLocal(True)     #True parameter added by EagleIan
        world = self.blenderObject.getWorld()

        self.location = world["location"]
        self.angle = world["angle"]
        self.scale = world["scale"]

        self.locationLocal = local["location"]
        self.angleLocal = local["angle"]
        self.scaleLocal = local["scale"]
        # TODO: multiply location with scale of parent?

#        print(self.blenderObject.name)
#        print(self.locationLocal)
#        print(self.blenderObject.locationLocal)
#        print(obj.name, self.angleLocal)
#        print(self.blenderObject.angleLocal)

        self.rotation = self.angleLocal

        # local position will be applied by static translations right now
        # so remove initial location to get offset
        for i in range(0,3):
            self.translation[i] = self.locationLocal[i]-self.blenderObject.locationLocal[i]
