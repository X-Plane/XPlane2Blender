from collections import Iterable, namedtuple
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
        '''
        rotation_mode:str->List[Vector], str (final rotation mode)
        '''
        def _makeReferenceAxes(keyframes):
            axes = []
            rotationMode = keyframes.getRotationMode()
            if rotationMode == 'QUATERNION':
                return _makeReferenceAxes(keyframes.asAA())

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
                        return _makeReferenceAxes(keyframes.asEuler())

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
            return axes, keyframes.getRotationMode()

        if rotation_mode is None:
            rotation_mode = self.getRotationMode()
        
        if rotation_mode == 'QUATERNION':
            keyframes = self.asQuaternion()
        elif rotation_mode == 'AXIS_ANGLE':
            keyframes = self.asAA()
        elif {'X','Y','Z'}  == set(rotation_mode):
            keyframes = self.asEuler()
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
        axes, final_rotation_mode = self.getReferenceAxes()

        #List[List[Vector,List[Keyframe]]]
        ret = [[axis,None] for axis in axes]
        TableEntry = namedtuple('TableEntry', ['value','degrees'])
        if final_rotation_mode == "AXIS_ANGLE" or\
           final_rotation_mode == "QUATERNION":
            keyframe_table = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[0])) for keyframe in self] 
            ret[0][1]  = keyframe_table
        else:
            cur_order = self.EULER_AXIS_ORDERING[final_rotation_mode]
            ret[0][1]  = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[cur_order[0]])) for keyframe in self]
            ret[1][1]  = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[cur_order[1]])) for keyframe in self]
            ret[2][1]  = [TableEntry(keyframe.value, math.degrees(keyframe.rotation[cur_order[2]])) for keyframe in self]

        ret = [tuple((axis_info[0],axis_info[1])) for axis_info in ret]

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

    def getRotationKeyframeTableNoClamps(self):
        '''
        Return the rotation portion of a keyframe collection in the form of
        List[Tuple[axis, List[Tuple[value,deg]]]], where axis is Vector.
        
        Does not contain any clamping keyframes.
        '''
        return XPlaneKeyframeCollection.filter_clamping_keyframes(self.getRotationKeyframeTable(), "rotation")

    def getTranslationKeyframeTable(self):
        '''
        Returns List[TranslationKeyframe[keyframe.value, keyframe.location]] where location is a Vector
        '''
        TranslationKeyframe = namedtuple('TranslationKeyframe', ['value','location'])
        return [TranslationKeyframe(keyframe.value, keyframe.location) for keyframe in self]

    def getTranslationKeyframeTableNoClamps(self):
        '''
        ()->List[TranslationKeyframe[keyframe.value, keyframe.location]] where location is a Vector
        without any clamping values in the keyframe table
        '''
        return XPlaneKeyframeCollection.filter_clamping_keyframes(self.getTranslationKeyframeTable(), "location")

    # Returns list  of tuples of (keyframe.value, keyframe.location)
    # with location being a Vector in Blender form and scaled by the scaling amount
    def getTranslationKeyframeTableWScale(self):
        pre_scale = self[0].xplaneBone.getPreAnimationMatrix().decompose()[2]
        return [(value, location * pre_scale) for value, location in self.getTranslationKeyframeTable()]

    def asAA(self):
        return XPlaneKeyframeCollection([keyframe.asAA() for keyframe in self])
        
    def asEuler(self):
        return XPlaneKeyframeCollection([keyframe.asEuler() for keyframe in self])
            
    def asQuaternion(self):
        return XPlaneKeyframeCollection([keyframe.asQuaternion() for keyframe in self])

    @staticmethod
    def filter_clamping_keyframes(keyframes,attr):
        '''
        Returns a new keyframe collection without clamping keyframes
        attr specifies which keyframe attribute will be used to filter,
        and must be "location" or "degrees"
        '''
        assert attr in ("location","degrees")

        cleaned_keyframes = keyframes[:]
        # Remove clamp values
        # List[Tuple[float,float]],value_str -> None
        def remove_clamp_keyframes(keyframes,attr):
            itr = iter(keyframes)
            while len(keyframes) > 2:
                current       = next(itr)
                next_keyframe = next(itr,None)

                if next_keyframe is not None:
                    if getattr(current,attr) == getattr(next_keyframe,attr):
                        del keyframes[keyframes.index(current)]
                        itr = iter(keyframes)
                    else:
                        break

        remove_clamp_keyframes(cleaned_keyframes,attr)
        cleaned_keyframes.reverse()
        remove_clamp_keyframes(cleaned_keyframes,attr)
        cleaned_keyframes.reverse()
        
        return cleaned_keyframes
