from collections.abc import MutableSequence
import copy

import bpy
import mathutils

# Class: XPlaneKeyframeCollection
# A list of at least 2 XPlaneKeyframes
class XPlaneKeyframeCollection(MutableSequence):
    # Constructor: __init__
    #
    # Parameters:
    #   data - A list of <XPlaneKeyframe>s at least 2 entries big
    def __init__(self, data):
        super().__init__()
        assert data is not None and len(data) >= 2
        self._list = list(data)

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__, self._list)

    def __len__(self):
        """List length"""
        return len(self._list)

    def __getitem__(self, i):
        """Get a list item"""
        return self._list[i]

    def __delitem__(self, i):
        """Delete an item"""
        del self._list[i]

    def __setitem__(self, i, val):
        self._list[i] = val

    def __str__(self):
        return str(self._list)

    def insert(self, i, val):
        self._list.insert(i, val)

    def append(self, val):
        self.insert(len(self._list), val)

    def getDataref(self):
        return self._list[0].dataref

    def getRotationMode(self):
        return self._list[0].rotationMode

    def keyframesAsAA(self):
        if self.getRotationMode() == "AXIS_ANGLE":
            return self.keyframes
        elif self.getRotationMode() == "QUATERNION":
            return
        else:
            return
        
    def keyframesAsEuler(self):
        if self.getRotationMode() == "AXIS_ANGLE":
            keyframes = copy.copy(self._list)
            for keyframe in keyframes:
                rotation = keyframe.rotation
                axis = mathutils.Vector((rotation[1], rotation[2], rotation[3]))
                # Why the heck XZY?  Jonathan's 2.49 exporter decomposes Eulers using XYZ (because that is the ONLY
                # decomposition available in 2.49), but it does so in X-Plane space.  So this is an axis renaming
                # (since we alway work in Blender space) so that it comes out the same in X-Plane.
                keyframe.rotationMode = 'XZY'
                keyframe.rotation = mathutils.Quaternion(axis, rotation[0]).to_euler('XZY')

            return keyframes
        elif self.getRotationMode() == "QUATERNION":
            return
        else:
            return
            