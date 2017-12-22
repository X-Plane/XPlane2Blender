from collections import namedtuple
from collections.abc import MutableSequence
import copy
import math

import bpy
import mathutils
from mathutils import Vector

# Class: XPlaneKeyframeCollection
#
# A list of at least 2 XPlaneKeyframes. All keyframes should share the same dataref and
# have the same rotation mode
class XPlaneKeyframeCollection(MutableSequence):
    EULER_AXIS_ORDERING = {
        'ZYX': (0, 1, 2),
        'ZXY': (1, 0, 2),
        'YZX': (0, 2, 1),
        'YXZ': (2, 0, 1),
        'XZY': (1, 2, 0),
        'XYZ': (2, 1, 0)
    }

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

    def getReferenceAxes(self,rotation_mode=None):
        def _makeReferenceAxes(keyframes):
            axes = []
            rotationMode = keyframes.getRotationMode()
            if rotationMode == 'QUATERNION':
                return _makeReferenceAxes(keyframes.keyframesAsAA())

            if rotationMode == 'AXIS_ANGLE':
                refAxis    = None
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
                    elif refAxis.x == axis.x and\
                         refAxis.y == axis.y and\
                         refAxis.z == axis.z:
                        continue
                    elif refAxisInv.x == axis.x and\
                         refAxisInv.y == axis.y and\
                         refAxisInv.z == axis.z:
                        keyframe.rotation = rotation * -1
                    else:
                        return _makeReferenceAxes(keyframes.keyframesAsEuler())

                axes.append(refAxis)
            else:

                try:
                    eulerAxesOrdering = self.EULER_AXIS_ORDERING[rotationMode]
                    eulerAxes = [mathutils.Vector((1.0,0.0,0.0)),\
                                 mathutils.Vector((0.0,1.0,0.0)),\
                                 mathutils.Vector((0.0,0.0,1.0))]
                    for axis in eulerAxesOrdering:
                        axes.append(eulerAxes[axis]) 
                except:
                    raise Exception("Rotation mode %s doesn't exist in eulerAxisMap" % (rotationMode))

            assert len(axes) == 1 or len(axes) == 3
            assert len([axis for axis in axes if not isinstance(axis,mathutils.Vector)]) == 0
            return axes

        if rotation_mode is None:
            rotation_mode = self.getRotationMode()
        
        if rotation_mode == 'QUATERNION':
            keyframes = self.keyframesAsQuaternion()
        elif rotation_mode == 'AXIS_ANGLE':
            keyframes = self.keyframesAsAA()
        elif {'X','Y','Z'}  == set(rotation_mode):
            keyframes = self.keyframesAsEuler()
        else:
            raise Exception("% is not a known rotation mode" % rotation_mode)

        return  _makeReferenceAxes(keyframes)


    def getDataref(self):
        return self._list[0].dataref

    def getRotationMode(self):
        return self._list[0].rotationMode

    def getRotationKeyframeTable(self):
        '''
        Return the rotation portion of a keyframe collection in the form of
        List[Tuple[axis, List[Tuple[value,deg]]]], where axis is Vector.
        '''
        axes = self.getReferenceAxes()

        ret = [[axis,None] for axis in axes]
        TableEntry = namedtuple('TableEntry', ['value','degrees'])
        if self.getRotationMode() == "AXIS_ANGLE" or\
           self.getRotationMode() == "QUATERNION":
            keyframe_table = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[0])) for keyframe in self] 
            ret[0][1] = keyframe_table
        else:
            for axis,order in zip(axes,self.EULER_AXIS_ORDERING[self.getRotationMode()]):
                keyframe_table = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[order])) for keyframe in self]
                ret[ret.index(axis)] = keyframe_table
    
        ret = [(info[0],info[1]) for info in ret]
        assert isinstance(ret,list)
        for axis_info in ret:
            assert isinstance(axis_info,tuple)
            assert isinstance(axis_info[0],Vector)
            assert isinstance(axis_info[1],list)

            for table_entry in axis_info[1]:
                assert isinstance(table_entry,tuple)
                assert isinstance(table_entry.value,float)
                assert isinstance(table_entry.degrees,float)

        return ret

    def getTranslationKeyframeTable(self):
        '''
        Returns List[TranslationKeyframe[keyframe.value, keyframe.location]] where location is a Vector
        '''
        TranslationKeyframe = namedtuple('TranslationKeyframe', ['value','location'])
        return [TranslationKeyframe(keyframe.value, keyframe.location) for keyframe in self]

    # Returns list  of tuples of (keyframe.value, keyframe.location)
    # with location being a Vector in Blender form and scaled by the scaling amount
    def getTranslationKeyframeTableWScale(self):
        pre_scale = self[0].xplaneBone.getPreAnimationMatrix().decompose()[2]
        return [(value, location * pre_scale) for value, location in self.getTranslationKeyframeTable()]

    def keyframesAsAA(self):
        #TODO: This copy operation still isn't enough to make it clean without sideeffects
        keyframes = copy.copy(self)
        if self.getRotationMode() == "AXIS_ANGLE":
            return keyframes
        elif self.getRotationMode() == "QUATERNION":
            for keyframe in keyframes:
                axisAngle = keyframe.rotation.normalized().to_axis_angle()
                keyframe.rotation = mathutils.Vector((axisAngle[1], axisAngle[0][0], axisAngle[0][1], axisAngle[0][2]))
                keyframe.rotationMode = "AXIS_ANGLE"
            return keyframes
        else:
            for keyframe in keyframes:
                rotation = keyframe.rotation
                euler_axis = mathutils.Euler((rotation.x,rotation.y,rotation.z),rotation.order)
                keyframe.rotationMode = "AXIS_ANGLE"

                # Very annoyingly, to_axis_angle and blenderObject.rotation_axis_angle disagree
                # about (angle, axis_x, axis_y, axis_z) vs (axis, (angle))
                new_rotation = euler_axis.to_quaternion().to_axis_angle()
                new_rotation_axis  = new_rotation[0]
                new_rotation_angle = new_rotation[1]
                keyframe.rotation = (new_rotation_angle, new_rotation_axis[0], new_rotation_axis[1], new_rotation_axis[2])

            return keyframes
        
    def keyframesAsEuler(self):
        keyframes = copy.copy(self)
        if self.getRotationMode() == "AXIS_ANGLE":
            for keyframe in keyframes:
                rotation = keyframe.rotation
                axis = mathutils.Vector((rotation[1:4]))
                # Why the heck XZY?  Jonathan's 2.49 exporter decomposes Eulers using XYZ (because that is the ONLY
                # decomposition available in 2.49), but it does so in X-Plane space.  So this is an axis renaming
                # (since we alway work in Blender space) so that it comes out the same in X-Plane.
                keyframe.rotationMode = 'XZY'
                keyframe.rotation = mathutils.Quaternion(axis, rotation[0]).to_euler('XZY')

            return keyframes
        elif self.getRotationMode() == "QUATERNION":
            return
        else:
            return keyframes
            
    def keyframesAsQuaternion(self):
        keyframes = copy.copy(self)
        if self.getRotationMode() == "AXIS_ANGLE":
            for keyframe in keyframes:
                rotation = keyframe.rotation
                keyframe.rotation = mathutils.Quaternion(*rotation[0:4])
                keyframe.rotationMode = "QUATERNION"
        elif self.getRotationMode() == "QUATERNION":
            return keyframes
        else:
            return
    
