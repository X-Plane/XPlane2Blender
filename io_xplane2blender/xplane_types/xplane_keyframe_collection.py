from collections import Iterable, namedtuple
from collections.abc import MutableSequence
import copy
import math
from typing import List 

import bpy
import mathutils
from mathutils import Vector

from io_xplane2blender.xplane_types.xplane_keyframe import XPlaneKeyframe

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

    def __init__(self, data:List[XPlaneKeyframe]):
        '''
        data - A list of XPlaneKeyframes, all with the same dataref and
        rotationMode, at least 2 entries big.

        XPlaneKeyframeCollection may mutate some of the keyframe data to maintain a reference
        axis of animation.
        '''

        super().__init__()
        assert data is not None and len(data) >= 2
        assert len({kf.dataref for kf in data}) == 1
        assert len({kf.rotationMode for kf in data}) == 1
        self._list = copy.deepcopy(data)

        # _makeReferenceAxes uses a "cute but regrettable" recursive strategy for
        # converting Quaternions->AA->Euler as needed
        def _makeReferenceAxes(keyframes):
            axes = []
            if keyframes.getRotationMode() == 'QUATERNION':
                keyframes.toAA()

            if keyframes.getRotationMode() == 'AXIS_ANGLE':
                refAxis    = None
                refAxisInv = None

                for keyframe in keyframes:
                    angle = keyframe.rotation[0]
                    axis = keyframe.rotation[1]

                    def round_vector(vec,ndigits=5):
                        v = Vector([round(comp,ndigits) for comp in vec])
                        return v

                    '''
                    This section covers the following cases
                    - keyframe has 0 degrees of rotation, so no axis should be produced
                    - refAxis and axis are the same. If this happens for all keyframes, 1 reference axis will be returned! Yay! 
                    - Correct axis that are the same as the previous reference axes, just inverted
                    - If at least two axis are different, we convert to Euler angles
                    '''
                    if round(angle,5) == 0:
                        continue
                    elif refAxis == None:
                        refAxis = axis
                        refAxisInv = refAxis * -1
                    elif round_vector(refAxis) == round_vector(axis):
                        continue
                    elif round_vector(refAxisInv) == round_vector(axis):
                        keyframe.rotation = (angle*-1, axis * -1)
                    else:
                        return _makeReferenceAxes(keyframes.toEuler())

                #If our AA's W component was 0 the whole time, we need a default
                if refAxis == None:
                    refAxis = mathutils.Vector((0, 0, 1))
                axes.append(refAxis)
            else:
                try:
                    eulerAxesOrdering = self.EULER_AXIS_ORDERING[keyframes.getRotationMode()]
                    eulerAxes = [mathutils.Vector((1.0,0.0,0.0)),\
                                 mathutils.Vector((0.0,1.0,0.0)),\
                                 mathutils.Vector((0.0,0.0,1.0))]
                    for axis in eulerAxesOrdering:
                        axes.append(eulerAxes[axis]) 
                except:
                    raise Exception("Rotation mode %s doesn't exist in eulerAxisMap" % (keyframes.getRotationMode()))

            assert len(axes) == 1 or len(axes) == 3
            assert len([axis for axis in axes if not isinstance(axis,mathutils.Vector)]) == 0
            return axes, keyframes.getRotationMode()

        self._referenceAxes, final_rotation_mode  = _makeReferenceAxes(self)

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

    def getReferenceAxes(self):
        '''
        rotation_mode:str->List[Vector], str (final rotation mode)
        '''

        return (self._referenceAxes, self.getRotationMode())

    def getDataref(self):
        return self._list[0].dataref

    def getRotationMode(self):
        return self._list[0].rotationMode

    def getRotationKeyframeTable(self): # type: -> List[Tuple[Vector,List[TableEntry]]]
        '''
        Return the rotation portion of a keyframe collection in the form of
        List[Tuple[axis, List[Tuple[value,degrees]]]], where axis is Vector.
        '''
        axes, final_rotation_mode = self.getReferenceAxes()

        #List(length 1 or 3)[
        #    List[Vector:rotation axis, List[TableEntry]]
        #]
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

    def getRotationKeyframeTableNoClamps(self): # List[Tuple[axis, List[Tuple['value','degrees']]]]
        '''
        Return the rotation portion of a keyframe collection in the form of
        List[Tuple[axis, List[Tuple[value,degrees]]]], where axis is Vector.
        
        Does not contain any clamping keyframes.
        '''
        return XPlaneKeyframeCollection.filter_clamping_keyframes(self.getRotationKeyframeTable(), "degrees")

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

    def asAA(self)->'XPlaneKeyframeCollection':
        return XPlaneKeyframeCollection([keyframe.asAA() for keyframe in self])
        
    def asEuler(self)->'XPlaneKeyframeCollection':
        return XPlaneKeyframeCollection([keyframe.asEuler() for keyframe in self])
            
    def asQuaternion(self)->'XPlaneKeyframeCollection':
        return XPlaneKeyframeCollection([keyframe.asQuaternion() for keyframe in self])

    def toAA(self)->'XPlaneKeyframeCollection':
        self._list = [keyframe.asAA() for keyframe in self]
        return self
        
    def toEuler(self)->'XPlaneKeyframeCollection':
        self._list = [keyframe.asEuler() for keyframe in self]
        return self
            
    def toQuaternion(self)->'XPlaneKeyframeCollection':
        self._list = [keyframe.asQuaternion() for keyframe in self]
        return self

    @staticmethod
    def filter_clamping_keyframes(keyframe_collection:'XPlaneKeyframeCollection',attr:str):
        '''
        Returns a new keyframe collection without clamping keyframes
        attr specifies which keyframe attribute will be used to filter,
        and must be "location" or "degrees"
        '''
        assert attr in ("location","degrees")

        # Remove clamp values
        # if attr == 'location':
        #   List[TranslationKeyframe[keyframe.value, keyframe.location]]
        # elif attr == 'degrees
        #   List[RotationKeyframe['value','degrees']] from List[Tuple[axis, List[Tuple['value','degrees']]]]
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

        cleaned_keyframe_collection = keyframe_collection[:]
        if attr == 'location':
            remove_clamp_keyframes(cleaned_keyframe_collection,attr)
            cleaned_keyframe_collection.reverse()
            remove_clamp_keyframes(cleaned_keyframe_collection,attr)
            cleaned_keyframe_collection.reverse()
            return cleaned_keyframe_collection
        elif attr == 'degrees':
            for axis,table in cleaned_keyframe_collection:
                remove_clamp_keyframes(table, attr)
                table.reverse()
                remove_clamp_keyframes(table, attr)
                table.reverse()
            return cleaned_keyframe_collection
        
