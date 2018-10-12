import collections
import os
import re
import sys
from typing import Any, Dict, Optional, Text, Tuple, Union

import bpy

from io_xplane2blender import xplane_helpers
from io_xplane2blender.tests import test_creation_helpers

DatarefFull = Text
SName = Text
TailName = Text # Never has an index in it. That is 
BoneName = Union[SName,TailName,Text] # Could have SName + "[idx]" or TailName + "[idx]"
LookupRecord = Tuple[DatarefFull, int]

def _remove_vowels(s:Text)->Text:
    for eachLetter in s:
        if eachLetter in ['a','e','i','o','u','A','E','I','O','U','_']:
            s = s.replace(eachLetter, '')
    return s

def _make_short_name(full_path:DatarefFull)->SName:
    '''
    The spec seems to be
    - take the first letter of every component in the path,
    - remove the array from the tail part
    - if the tail is greater than 15 characters, remove all the vowles
    - parts of the path that end in 2, like cockpit2 append it. sim/cockpit2->sc2

    There is no validation for fullpath.
    '''
    ref=full_path.split('/')
    short=""
    for comp in ref:
        #If we've reached the end
        if comp == ref[-1]:
            short=short+"_"
            #if the end part before the '[' 
            if len(comp.split('[')[0]) > 15:
                short=short+_remove_vowels(comp)
            else:
                short=short+comp
        else:
            short=short+comp[0]
            if comp[-1] == '2':
                short=short+"2"
    return short

def _getDatarefs()->Dict[Union[SName,TailName],LookupRecord]:
    '''
    Parses the contents of the dataref file as a dictionary where
    where a short_name or tail-name can retrive
    (dateref_full, size where 0 = not usable, 1 = scalar, > 1 array).

    See https://github.com/der-On/XPlane2Blender/wiki/2.49:-How-It-Works:-Dataref-Encoding-and-Decoding
    for what this is all about. Its too much to explain here.

    Historically, this also returned a hierarchy form for 2.49's UI. This isn't needed anymore.
    '''

    '''
    A reperesentation of the output of this
    {
    'acf_descrip':('sim/aircraft/view/acf_descrip', 0   ),
    'sav_acf_author':('sim/aircraft/view/acf_author', 0   ),
    'sa_acf_struct':('sim/aircraft/acf_struct', 10   ),
    'sav_acf_notes':('sim/aircraft/view/acf_notes', 0   ),
    'acf_author':('sim/aircraft/view/acf_author', 0   ),
    'acf_notes':('sim/aircraft/view/acf_notes', 0   ),
    'acf_size_x':('sim/aircraft/view/acf_size_x', 1   ),
    'acf_tailnum':('sim/aircraft/view/acf_tailnum', 0   ),
    'acf_size_z':('sim/aircraft/view/acf_size_z', 1   ),
    'sav_acf_size_x':('sim/aircraft/view/acf_size_x', 1   ),
    'sav_acf_size_z':('sim/aircraft/view/acf_size_z', 1   ),
    'sav_acf_descrip':('sim/aircraft/view/acf_descrip', 0   ),
    'acf_struct':('sim/aircraft/acf_struct', 10   ),
    'sav_acf_tailnum':('sim/aircraft/view/acf_tailnum', 0   )
    }
    '''
    datarefs={}
    err=IOError(0, "Corrupt DataRefs.txt file. Please re-install.")
    try:
        with open(os.path.join(xplane_helpers.get_addon_resources_dir(), "DataRefs.txt")) as f:
            #d is the version line of the DataRefs.txt line
            #d: ['2', '1004', 'Sat', 'Mar', '3', '23:12:08', '2012']
            d=f.readline().split()

            # Difference between 2.78 Datref and 2.49 Dataref parser:
            # 1. 2.49 must have the date time metadata version line
            # 2. Any number of line breaks are allowed after and in between dataref lines
            # 3. sim/test and sim/version are ignored
            # 4. sim/multiplayer is ignored
            # 5. byte array is not allowed
            # 6. data type is allowed to have upper or mixed case
            # 7. Multiply indexed array types are allowed, such as 'flightmodel/parts/v_el [73][10][4]'
            if len(d)!=7 or d[0]!='2': # Diff #1
                raise err
            for line in f:
                if 'yoke_roll_ratio' in line:
                    import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev.core_6.5.0.201809011628\pysrc')
                    #import pydevd;pydevd.settrace()
                    #print("line!: " + line)

                d=line.split() #Annoying re-use of non-descriptive variable 'd'
                if not d: # Diff #2
                    continue
                if len(d)<3:
                    raise err
                sname=_make_short_name(d[0])
                ref=d[0].split('/')
                if 'yoke_roll_ratio' in line:
                    import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev.core_6.5.0.201809011628\pysrc')
                    #import pydevd;pydevd.settrace()
                    #print("sname!: " + sname)

                if ref[1] in ['test', 'version']: # Diff #3
                    continue # hack: no usable datarefs

                #############################
                # The Very Odd Type Parser: #
                #############################
                # This code finds out two things
                # 1. Is this a unusable dataref? (n = 0)
                # 2. Is this a usable dataref w/o an array? (n = 1)
                # 3. Is this a usable dataref w an array? (n = product of every array size)
                #
                # The code to find this out works, is full of buggy cases edge cases and relies
                # on having good data, and is not obvious how it works.
                n=1 # scalar by default

                for c in ['int', 'float', 'double']: # Diff #5
                    if d[1].lower().startswith(c): # Diff #6
                        # Is there something after the type?
                        if len(d[1])>len(c):
                            #suffix could contain data like '10' or '73][10][4'
                            #spliting on the ][s allows for iterating over this
                            #and finding the product of all array sizes
                            suffix = d[1][len(c)+1:-1]
                            for dd in suffix.split(']['):
                                # One of the most prime examples of "Don't be as clever as possible"
                                # I've ever seen in my life.
                                n = n * int(dd) # Diff #7
                        break
                else:
                    # If the type did not start with int, float, or double,
                    # we have an unusable dataref
                    n = 0

                #Other parts of the code need to append text like '[10]_v1', so space must be reserved for that
                if n>99:
                    if len(sname) > 23:
                        print('WARNING - dataref ' + line + ' is too long for key frame table')
                if n>9:
                    if len(sname) > 24:
                        print('WARNING - dataref ' + line + ' is too long for key frame table')
                elif n > 1:
                    if len(sname) > 25:
                        print('WARNING - dataref ' + line + ' is too long for key frame table')
                else:
                    if len(sname) > 28:
                        print('WARNING - dataref ' + line + ' is too long for key frame table')
    #                elif len(sname) > 17:
    #                   print 'WARNING - dataref ' + d[0] + ' is too long for show/hide'

                # This makes the actual datarefs dictionary.
                # The key is either the short name or, if short enough, just the tail of the dataref
                if ref[1]!=('multiplayer'): # too many ambiguous datarefs # Diff #4
                    if sname in datarefs:
                        print('WARNING - ambiguous short name '+ sname + ' for dataref ' + d[0])
                    else:
                        datarefs[sname]=(d[0], n)
                    if ref[-1] in datarefs:
                        datarefs[ref[-1]]=None # ambiguous
                    else:
                        datarefs[ref[-1]]=(d[0], n)
    except:
        raise IOError(0, "Missing DataRefs.txt file. Please re-install.")

    #print(datarefs)
    return datarefs

'''
The contents of DataRefs.txt, after being parsed!
'''
_249_datarefs = _getDatarefs()

#--------------------------------------------------------------------------------

def get_known_dataref_from_shortname(dataref_short:SName)->Optional[LookupRecord]:
    '''
    Returns full dataref and array size from an sname lookup,
    or None if not found.

    Remember: This means that this was never in Datarefs.txt,
    unlike getting None from a tail-name lookup
    '''

    if dataref_short in _249_datarefs and _249_datarefs[dataref_short]: 
        dataref_full = _249_datarefs[dataref_short][0]
        array_size = _249_datarefs[dataref_short][1]
        return (dataref_full, array_size)
    else:
        return None

def get_known_dataref_from_tailname(dataref_tailname:TailName)->Optional[LookupRecord]:
    '''
    Returns full dataref and array size from a tail-name look up,
    or None if not Found.

    Remember: This means that there is an ambiguity in Datarefs.txt,
    unlike getting None from an sname lookup
    '''

    if dataref_tailname in _249_datarefs and _249_datarefs[dataref_tailname]: 
        dataref_full = _249_datarefs[dataref_tailname][0]
        array_size = _249_datarefs[dataref_tailname][1]
        return (dataref_full, array_size)
    else:
        return None

class LookupResult():
    __slots__ = ['record', 'sname_success', 'tailname_success']
    def __init__(self, record:LookupRecord=(None,None), sname_success:bool=False, tailname_success:bool=False):
        self.record =             record
        self.sname_success =      sname_success
        self.tailname_success =   tailname_success

def lookup_dataref(sname:Optional[SName], tailname:Optional[TailName])->LookupResult:
    '''
    Using an optional SName andor TailName, lookup a dataref in
    the datarefs dictionary. Returns the Lookup Record (if found, else None)
    and which methods were successful. Remeber, they have different semantic meanings!

    res[1][0] is False: Dataref is unknown (not in datarefs dict and therefore not in Datarefs.txt)
    res[1][1] is False: Dataref is unknown or has ambiguity that needs game prop resolution
    '''
    assert sname is not None and tailname is not None, "sname and tailname are both None"

    lookup_result = LookupResult()
    for i,lookup_name in enumerate([sname, tailname]):
        if lookup_name in _249_datarefs:
            '''
            if i == 0:
                assert _249_datarefs[lookup_name] is not None,\
                    "sname lookup with {} returned None".format(lookup_name)
            '''

            if i == 1 and lookup_result.record != (None,None):
                assert lookup_result.record == _249_datarefs[lookup_name],\
                    ("good tailname lookup != good sname lookup: {}"
                        .format(_249_datarefs[lookup_name]))

            lookup_result.record = _249_datarefs[lookup_name]
            if i == 0:
                lookup_result.sname_success = True
            if i == 1:
                lookup_result.tailname_success = True

    return lookup_result

# Why these stupid methods? To be descriptive! The 2.49 code is
# littered with array accessing, string munging. By using
# a common and clear vocabulary we'll be able to tame
# the split, convert, append, convert beast

def sname_from_full_dataref(dataref_full:DatarefFull)->SName:
    '''Turns any full dataref into a shortname version'''
    return _make_short_name(dataref_full)

def tailname_from_full_dataref(dataref_full:DatarefFull)->TailName:
    return dataref_full.split('/')[-1]

def get_shortname_from_gameprop(game_prop:str)->Optional[str]:
    x = game_prop.split("[")[0].split("_")
    return x


def decode_shortname_properties(dataref_short:str)->Optional[Tuple[str, Tuple[Optional[int], Dict[str,Any]]]]:
    '''
    Given a 2.49 short name, return the path, frame_number, and a dictionary of properties
    matching xplane_props.XPlaneDataref or None if there was a problem
    '''
    #This comes from attempting to understand XPlaneAnimObject.getvals, line 225-, line 987-999
    #and the property table of a real life example using sa_acf_struct

    #print("DFSHORT: " + dataref_short)
    #TODO: Show/Hide doesn't work like the rest for path. It gets split? Value forms part of dataref
    match = re.match(r"(?P<path>[a-zA-Z]\w+)" #sim/whatever/this/part
                     r"(\[(?P<idx>\d+)\])?" #TODO: What about the cloud weirdo dataref?
                     r"(?P<anim_type>_show|_hide)?"
                     r"(?P<prop>(_v(?P<frame_number>\d+))|_loop)?",
                     dataref_short,
                     flags=re.I)

    print("MATCH: " + repr(match))
    if match:
        m_dict = match.groupdict(default="")
        print("M_DICT: {}".format(m_dict))
        #TODO: This doesn't work with unknown datarefs!
        sname, _ = get_known_dataref_from_shortname(m_dict['path'])
        if sname:
            path = "{}[{}]".format(sname, m_dict['idx']) # type: str
        else:
            return None, None
        frame_number = None # type: int
        props = dict(
            #Matches XPlaneDataref, not dataref_short, Including By Datatype
            zip(['value', 'loop', 'anim_type', 'show_hide_v1', 'show_hide_v2'], [None]*5)
        )

        if m_dict['anim_type'] == "_show" or m_dict['anim_type'] == "_hide":
            props['anim_type'] = m_dict['anim_type'][1:]
        else:
            props['anim_type'] = 'transform'
        if m_dict['prop'] == "_loop":
            props['loop'] = m_dict['prop'][1:]
        elif m_dict['prop'].startswith("_v"):
            frame_number = int(m_dict['frame_number'])
        #print("{},({},{})".format(path,frame_number,props))
        return path, (frame_number, props)
    else:
        return None, None

def do_249_conversion():
    #TODO: Create log, similar to conversion log

    #TODO: Can only run this if it is evident there is 249 data.
    # We can't simply ask if there are game properties in this file
    # and probably shouldn't just rely on "it has to exist on disk" or we could
    # lose out on good automation opportunities. Maybe.
    if not bpy.data.filepath:
        return

    # Global settings
    bpy.context.scene.xplane.debug = True
    #TODO: Take file name and make it layer name (TODO: What about root objects mode?)
    filename = os.path.split(bpy.data.filepath)[1]
    bpy.context.scene.xplane.layers[0].name = filename[:filename.index('.')]

    #TODO: Remove clean up workspace as best as possible,
    # remove areas with no space data and change to best
    # defaults like Action Editor to Dope Sheet

    # Make the default material for new objects to be assaigned
    # TODO: Only needed if you have cubes without materials? Don't create,
    # except for test files? Just don't be lazy about test files
    for armature in filter(lambda obj: obj.type == 'ARMATURE', bpy.data.objects):
        print(armature.name)
        bpy.context.scene.objects.active = armature
        # All datarefs mentioned by bone names and game properties in this armature
        all_arm_drefs = {}
        for bone in armature.pose.bones:
            # 2.49 slices and trims bone names before look up
            bone_name = bone.name.split('.')[0].strip() # type: BoneName
            bone_name_no_idx = bone_name.split('[')[0] # type: Union[SName,TailName]

            print('---')
            print(bone_name)
            print(bone_name_no_idx)
            #We don't know what we're looking at here? We need to be precise, so lookup_dataref can make assumptions
            lookup_result = lookup_dataref(bone_name,bone_name_no_idx)
            print(lookup_result.record)
            print(lookup_result.sname_success)
            print(lookup_result.tailname_success)
            dref_full = lookup_result.record[0]
            print(dref_full)
            print('---')
            continue
            #Test if it is a known name
            if dref_full:
                all_arm_drefs[dref_full] = None
            else:
                # Cases:
                # Sometimes the bone name could match a short prop name, or it, it would actually need to come from matching a full
                # If the short name wasn't a known name, it could be ambiguious or a custom dataref
                if bone_name in armature.game.properties:
                    #dref_short is the last component of the dataref,
                    #TODO: Unsure if we need another call to make_short_name
                    disambiguating_key = armature.game.properties[bone_name].value + "/" + bone_name
                    print("disambiguating key: " + disambiguating_key)
                    all_arm_drefs[disambiguating_key] = None
                else:
                    print(bone_name)
                    #assert False, "What the heck!"

        print("finally")
        print(all_arm_drefs)
        break
        for game_prop in armature.game.properties:
            print("game_prop.name: {}, value: {}".format(game_prop.name, game_prop.value))
            path, prop_info = decode_shortname_properties(game_prop.name)
            if not path:
                print("continuing from " + game_prop.name)
                continue
            prop_info[1].update(value=game_prop.value)
            print('{},{}'.format(path,prop_info))
            if path not in all_arm_drefs:
                print("not insane!" + path)

                #assert False, "New path discovered! " + path

                #all_arm_drefs[path] = []
            all_arm_drefs[path].append(prop_info)

        assert False
        #TODO: If you only have datarefs in bone name only
        for k in all_arm_drefs:
            all_arm_drefs[k] = sorted(all_arm_drefs[k])
        print("hi {}".format(all_arm_drefs))

        # What was the rule for multiple bones? Don't? Oh yes, don't! Short names must be unique or the whole system
        # falls apart!
        #for pose_bone in armature.pose.bones:
        for path,dref_info in all_arm_drefs.items():
            for frame,dref_in in dref_info:
                test_creation_helpers.set_animation_data(armature.pose.bones[0],
                        [test_creation_helpers.KeyframeInfo(
                            idx=frame,
                            dataref_path=path,
                            dataref_value=dref_in['value'],
                            dataref_anim_type=dref_in['anim_type'],
                            dataref_loop=0.0 if dref_in['loop'] is None else dref_in['loop']
                        )],
                        parent_armature=armature)
        sys.exit(0)

