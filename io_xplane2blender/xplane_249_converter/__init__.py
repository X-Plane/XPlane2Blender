'''
This is the entry point for the 249 converter. Before you start poking around
make sure you read the available documentation! Don't assume anything!

Reading List:

- https://github.com/der-On/XPlane2Blender/wiki/2.49:-How-It-Works:-Dataref-Encoding-and-Decoding
'''
import collections
import enum
import os
import re
import sys
from typing import Any, Dict, List, Optional, Text, Tuple, Union

import bpy

from io_xplane2blender import xplane_helpers
from io_xplane2blender.tests import test_creation_helpers

DatarefFull = str
SName = str
TailName = str
BoneName = Union[SName, TailName, str] # Could have SName + "[idx]" or TailName + "[idx]"

ArraySize = int # From DataRefs.txt datarefs size, always >= 0
LookupRecord = Optional[Tuple[DatarefFull, ArraySize]] # The int represents array size

FrameNumber = int # always >= 1, the Blender 2.49 frame counter starts at 1

# Representing ('path', ('frame_number', {'value', 'loop', 'anim_type', 'show_hide_v1', 'show_hide_v2'}))
ParsedGameAnimValueProp = Tuple[DatarefFull, Tuple[Optional[FrameNumber], Dict[str, Optional[Union[int, float, str]]]]]

class LookupResult():
    __slots__ = ['record', 'sname_success', 'tailname_success']
    def __init__(self, record:LookupRecord=None, sname_success:bool=False, tailname_success:bool=False):
        self.record =             record
        self.sname_success =      sname_success
        self.tailname_success =   tailname_success

    def __str__(self):
        return "record: {}, sname_success: {}, tailname_success: {}".format(self.record,self.sname_success,self.tailname_success)

def _remove_vowels(s: str)->str:
    for eachLetter in s:
        if eachLetter in ['a','e','i','o','u','A','E','I','O','U','_']:
            s = s.replace(eachLetter, '')
    b = ''.join([letter for letter in s if letter not in {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U', '_'}])
    assert s == b, "s {} b {}".format(s, b)
    return s

def _make_short_name(full_path: DatarefFull)->SName:
    '''
    The spec seems to be
    - take the first letter of every component in the path,
    - remove the array from the tail part
    - if the tail is greater than 15 characters, remove all the vowles
    - parts of the path that end in 2, like cockpit2 append it. sim/cockpit2->sc2

    There is no validation for full_path.
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
    # TODO: What the heck are we implementing if someone used a multiplayer dref? Treat as 3rd party?!
                if ref[1]!=('multiplayer'): # too many ambiguous datarefs # Diff #4
                    if sname in datarefs:
                        print('WARNING - ambiguous short name '+ sname + ' for dataref ' + d[0])
                        print("sname " + sname + "is currently used for " + datarefs[sname][0])
                    else:
                        datarefs[sname]=(d[0], n)
                    if ref[-1] in datarefs:
                        datarefs[ref[-1]]=None # ambiguous
                    else:
                        datarefs[ref[-1]]=(d[0], n)
    except:
        # TODO: Should not capture all, also, IOError is now an alias for OSError and not descriptive.
        # Also, we should show something to the user like a popup bubble, because no one will read this
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


def lookup_dataref(sname:Optional[SName], tailname:Optional[TailName])->LookupResult:
    '''
    Using an optional SName andor TailName, lookup a dataref in
    the datarefs dictionary. Returns the Lookup Record (if found, else None)
    and which methods were successful. Remember, they have different semantic meanings!

    if lookup_result.sname_success is False, Dataref is unknown (not in datarefs dict
    and therefore not in Datarefs.txt)

    if lookup_result.tailname_success is False, Dataref is unknown or has ambiguity
    that needs game prop resolution

    if both are false, Dataref is definitely unknown and not ambiguous
    '''
    assert sname is not None and tailname is not None, "sname and tailname are both None"

    lookup_result = LookupResult()
    for i, lookup_name in enumerate([sname, tailname]):
        if lookup_name in _249_datarefs:
            '''
            Can't use this without the assumption that sname is always sname.
            #TODO: Maybe we'd better not use this
            if i == 0:
                assert _249_datarefs[lookup_name] is not None,\
                    "sname lookup with {} returned None".format(lookup_name)
            '''

            if i == 1 and lookup_result.record != None:
                assert lookup_result.record == _249_datarefs[lookup_name],\
                    ("good tailname lookup != good sname lookup: {}"
                     .format(_249_datarefs[lookup_name]))

            lookup_result.record = _249_datarefs[lookup_name]
            print("{}: Using '{}', found {}".format(i, lookup_name, _249_datarefs[lookup_name]))

            if i == 0 and lookup_result.record:
                lookup_result.sname_success = True
            if i == 1:
                lookup_result.tailname_success = True
        else:
            print("{}: {} not found in datarefs dict, skipping".format(i,lookup_name))

    return lookup_result

# Why these stupid methods? To be descriptive! The 2.49 code is
# littered with array accessing, string munging. By using
# a common and clear vocabulary we'll be able to tame
# the split, convert, append, convert beast
def sname_from_dataref_full(dataref_full:DatarefFull)->SName:
    '''Turns any full dataref into a shortname version'''
    return _make_short_name(dataref_full)


def tailname_from_dataref_full(dataref_full:DatarefFull)->TailName:
    '''Gets the tail from any full dataref'''
    return dataref_full.split('/')[-1]


def decode_game_animvalue_prop(game_prop: bpy.types.GameProperty,
                               known_datarefs: Tuple[str, Optional[str]]
                               ) -> Optional[ParsedGameAnimValueProp]:
    '''
    Given a 2.49 short name, return the path, (frame_number, and a dictionary of properties)
    matching xplane_props.XPlaneDataref or None if there was a problem
    '''
    #This comes from attempting to understand XPlaneAnimObject.getvals, line 225-, line 987-999
    #and the property table of a real life example using sa_acf_struct

    #---This block of code attempts to parse the game prop--------------
    def parse_game_prop_name(game_prop: bpy.types.GameProperty)->Optional[Dict[str,str]]:
        # Note: This Regex also captures _loop!
        PROP_NAME_IDX_REGEX = r"(?P<prop_root>[a-zA-Z]\w+)(\[(?P<idx>\d+)\])?" #TODO: breaks cloud case + "[idx]"
        PROP_NAME_FNUMBER = r"_v(?P<frame_number>\d+)$"
        name = game_prop.name.strip()

        parsed_results = {key:'' for key in ['anim_type', 'idx', 'prop_root', 'frame_number', 'loop']}

        print("Attempting to parse {}".format(game_prop.name))
        if re.search(r"_v\d+_(show|hide)$", name):
            print("1. Matched show/hide")
            parsed_results.update(
                re.search(PROP_NAME_IDX_REGEX + PROP_NAME_FNUMBER,
                         name).groupdict(default=""))
            parsed_results['anim_type'] = name[-4:]  #capture show or hide
        elif re.search(r"_loop$", name):
            print("2. Matched loop")
            parsed_results.update(
                re.search(PROP_NAME_IDX_REGEX,
                    name).groupdict(default=""))
            # I got tired of re-writing the regex to try and make this work,
            # instead we manually remove '_loop' and be done with it.
            parsed_results['prop_root'] = parsed_results['prop_root'].split('_loop')[0]
            parsed_results['loop'] = True
        elif re.search(PROP_NAME_FNUMBER, name):
            print("3. Matched anim-value")
            parsed_results.update(
                re.search(PROP_NAME_IDX_REGEX+PROP_NAME_FNUMBER,
                          name).groupdict(default=""))
        elif re.match(PROP_NAME_IDX_REGEX + "$", name):
            print("4. Matched disambiguating key or other text")
            print("Text: {}".format(name))
            return None
        else:
            print("5. Could not parse text")
            print("Unparsable Text: {}".format(name))
            return None

        assert parsed_results['anim_type'] or parsed_results['frame_number'] or parsed_results['loop'], "Parsed game_prop.name is missing meaningful values: {}".format(parsed_results)
        print("Parse Results: {}".format(parsed_results))
        return parsed_results

    parsed_results = parse_game_prop_name(game_prop)
    if not parsed_results:
        return None
    elif parsed_results['idx']:
        roots_to_test = [
            parsed_results['prop_root'], # rfind catches the "cloud case"
            parsed_results['prop_root'] + "[{}]".format(parsed_results['idx']),
            ]
    else:
        roots_to_test = [parsed_results['prop_root']]

    #TODO: What about _make_short_name copy from getcustomdatarefs?
    print("Testing Roots: {}".format(roots_to_test))
    #------------------------------------------------------------------

    #------------------------------------------------------------------
    # Our very important out path
    path = None # type: DatarefFull
    for prop_root in roots_to_test:
        #print("prop_root: {}".format(prop_root))
        def match_root_to_known_datarefs(
                prop_root: str,
                known_datarefs: List[DatarefFull])->Optional[DatarefFull]:
            '''
            Matches root to a known_dataref, or None if the root matched none of them
            (which is not necessarily a problem)
            '''
            for known_dataref in known_datarefs:
                #print("known_dataref: {}".format(known_dataref))
                known_tail = tailname_from_dataref_full(known_dataref) # type: TailName
                known_sname = _make_short_name(known_dataref)
                # Works for Known SNames, TailNames and the annoying + "[idx]" cloud case
                if prop_root in _249_datarefs:
                    #print("prop_root (in _249_datarefs): {}".format(prop_root))
                    # 1. Tail-Name could be None or in there. Duplicate (this also captures sname case sometimes)
                    if (_249_datarefs[prop_root] and _249_datarefs[prop_root][0] == known_dataref):
                        return known_dataref
                elif prop_root == known_tail: # Disambiguating key, TailName
                    return known_dataref
            else: #nobreak
                print("prop_root: {} didn't match any of the known_datarefs".format(prop_root))
                return None
        path = match_root_to_known_datarefs(prop_root, known_datarefs)
        if path:
            break
    else: #nobreak
        assert False, "Couldn't match prop_root to anything, which isn't how you're developing right now!"

    #TODO: Duplicate, can't decide if I like the for...else nobreak pattern
    if not path:
        assert False, "Couldn't match prop_root to anything, which isn't how you're developing right now!"

    #print("Final Path: " + path)
    #------------------------------------------------------------------

    #------------------------------------------------------------------
    frame_number = None # type: int
    # Matches attributes of xplane_props.XPlaneDataref
    props = {key:None for key in ['value', 'loop', 'anim_type', 'show_hide_v1', 'show_hide_v2']} # type: Dict[str,Optional[int,float,str]]
    #TODO: logging, not asserting
    assert game_prop.type in {"INT", "FLOAT"}, "game_prop ({},{}) value is not 'FLOAT' vs 'INT'".format(game_prop.name, game_prop.value)
    if parsed_results['anim_type'] == "show" or parsed_results['anim_type'] == "hide":
        props['anim_type'] = parsed_results['anim_type'][1:]
        props['value'] = float(game_prop.value)
    else:
        props['anim_type'] = 'transform'
        props['value'] = float(game_prop.value)

    if parsed_results['loop']:
        props['loop'] = float(game_prop.value)
    elif parsed_results['frame_number']:
        frame_number = int(parsed_results['frame_number'])

    print("Final Decoded Results: {},  ({}, {})".format(path, frame_number, props))
    #------------------------------------------------------------------
    return path, (frame_number, props)

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
    #TODO: Take file name and make it layer name
    #TODO: What about root objects mode?
    #TODO: What about those using layers as LODs?
    filename = os.path.split(bpy.data.filepath)[1]
    bpy.context.scene.xplane.layers[0].name = filename[:filename.index('.')]

    #TODO: Remove clean up workspace as best as possible,
    # remove areas with no space data and change to best
    # defaults like Action Editor to Dope Sheet

    # Make the default material for new objects to be assaigned
    # TODO: Only needed if you have cubes without materials? Don't create,
    # except for test files? Just don't be lazy about test files
    for armature in filter(lambda obj: obj.type == 'ARMATURE', bpy.data.objects):
        print("Decoding Game-Properties for '{}'".format(armature.name))
        bpy.context.scene.objects.active = armature

        def find_all_datarefs_in_armature(armature: bpy.types.Object)->Dict[DatarefFull,Tuple[bpy.types.PoseBone,List[ParsedGameAnimValueProp]]]:
            '''
            Returns a dictionary all datarefs mentioned in the bone names and game props,
            paired with the Bone the data was taken from an a list for
            future parsed game properties.

            Bones without useful names are ignored.
            '''

            all_arm_drefs = {} # type: Dict[DatarefFull,Tuple[bpy.types.PoseBone,List[ParsedGameAnimValueProp]]]

            #TODO: What about show/hide which is not dependent on bone names!
            for bone in armature.pose.bones:
                # 2.49 slices and trims bone names before look up
                bone_name = bone.name.split('.')[0].strip() # type: BoneName
                bone_name_no_idx = bone_name.split('[')[0] # type: Union[SName,TailName]

                print("\nLooking up dataref from '{}' and '{}'".format(bone_name, bone_name_no_idx))
                lookup_result = lookup_dataref(bone_name, bone_name_no_idx)

                print("Lookup Results: %s" % lookup_result)
                if lookup_result.record:
                    # SName or TailName, we've got it!
                    dref_full = lookup_result.record[0] # type: Optional[str]
                else:
                    # Catches known but ambiguous and unknown datarefs. Needs disambiguating
                    dref_full = None # type: Optional[str]

                #Test if it is a known name
                #TODO: Pretty this section can be folded into previous if/else
                if dref_full:
                    all_arm_drefs[dref_full] = (bone, [])
                else:
                    #TODO: What about a situation where you have my/custom/ref
                    # and my/custom/ref[1]
                    # Is this possible? Yes! ref:my/custom is disamb key, snames are ref[1] and ref.
                    # Seems very unlikely, however.
                    if bone_name in armature.game.properties:
                        disambiguating_prop = armature.game.properties[bone_name]
                    elif bone_name_no_idx in armature.game.properties:
                        disambiguating_prop = armature.game.properties[bone_name_no_idx]
                    else:
                        print("Bone {} found that can't convert to full dataref, will treat as plain bone.".format(bone_name))
                        continue

                    if disambiguating_prop.type == "STRING":
                        disambiguating_key = "{}/{}".format(disambiguating_prop.value.strip(" /"),bone_name)
                        print("Disambiguating Key: " + disambiguating_key)
                        all_arm_drefs[disambiguating_key] = (bone,[])
                    else:
                        print("Probable disambiguating prop ({}:{}) has wrong value type {}".format(
                            disambiguating_prop.name,
                            disambiguating_prop.value,
                            disambiguating_prop.type))
                        print("Bone {} found that can't convert to full dataref, will treat as plain bone.".format(bone_name))
                        continue

            print("Final Known Datarefs: {}".format(all_arm_drefs.keys()))
            return all_arm_drefs

        all_arm_drefs = find_all_datarefs_in_armature(armature)

        for game_prop in armature.game.properties:
            print("\ngame_prop.name: {}, value: {}".format(game_prop.name, game_prop.value))
            decoded_animval = decode_game_animvalue_prop(game_prop, tuple(all_arm_drefs.keys()))
            if decoded_animval:
                path, prop_info = decoded_animval
            else:
                #TODO: Error code goes here? How do we do these?
                #TODO: What about disambiguating keys returning none from decode_game_animvalue?
                print("Could not decode {}".format(game_prop.name))
                continue
            #print('Out: {},{}'.format(path,prop_info))
            assert path in all_arm_drefs, "How is this possible! path not in all_arm_drefs! " + path
            all_arm_drefs[path][1].append(prop_info)

        #print("all_arm_drefs pre-sorted: {}".format(all_arm_drefs))
        # Sorting by keyframe is necissary so they're applied correctly
        for k in all_arm_drefs:
            all_arm_drefs[k][1].sort()
        #print("all_arm_datarefs post-sorted: {}".format(all_arm_drefs))

        # Finally, the creation step!
        for path, (bone, dref_info) in all_arm_drefs.items():
            for frame, dref_in in dref_info:
                test_creation_helpers.set_animation_data(
                    bone, [
                        test_creation_helpers.KeyframeInfo(
                            idx=frame,
                            dataref_path=path,
                            dataref_value=dref_in['value'],
                            dataref_anim_type=dref_in['anim_type'],
                            dataref_loop=0.0 if dref_in['loop'] is None else dref_in['loop'])
                    ],
                    parent_armature=armature)
