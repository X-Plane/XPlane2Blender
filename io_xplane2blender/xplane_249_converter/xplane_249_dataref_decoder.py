
'''
This module handles converting Dataref Keyframes and encoding and decoding bone names
Reading List:

- https://github.com/der-On/XPlane2Blender/wiki/2.49:-How-It-Works:-Dataref-Encoding-and-Decoding
'''
import collections
import copy
import enum
import os
import re
import sys
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Text, Tuple, Union
from operator import attrgetter

import bpy

from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_constants import ANIM_TYPE_HIDE, ANIM_TYPE_SHOW, ANIM_TYPE_TRANSFORM
from io_xplane2blender.tests import test_creation_helpers

DatarefFull = str
SName = str
TailName = str
BoneName = Union[SName, TailName, str] # Could have SName + "[idx]" or TailName + "[idx]"

ArraySize = int # From DataRefs.txt datarefs size, always >= 0
LookupRecord = Optional[Tuple[DatarefFull, ArraySize]] # The int represents array size

FrameNumber = int # always >= 1, the Blender 2.49 frame counter starts at 1

class LookupResult():
    __slots__ = ['record', 'sname_success', 'tailname_success']
    def __init__(self, record:LookupRecord=None, sname_success:bool=False, tailname_success:bool=False):
        self.record =             record
        self.sname_success =      sname_success
        self.tailname_success =   tailname_success

    def __str__(self):
        return "record: {}, sname_success: {}, tailname_success: {}".format(self.record,self.sname_success,self.tailname_success)

class ParsedGameAnimValueProp():
    '''
    All the possible data that can be taken from a game prop.
    Although 2.78 has the array idx as part of the path,
    we keep it seperate until the very very end

    If the path has a cloud in it, array_idx is automatically set to ""

    Aside from array_idx, this nearly matches xplane_props.XPlaneDataref. 

    Unlike test_creation_helpers.KeyframeInfo, Show/Hide can be neither or one.
    decode_game_animvalue_prop
    '''
    def __init__(self,
                path: DatarefFull,
                array_idx: str, # [idx] or ""
                anim_type:str, # "show", "hide", or "transform"
                frame_number: Optional[FrameNumber]=None,
                loop: Optional[float]=None,
                show_hide_v1: Optional[float]=None,
                show_hide_v2: Optional[float]=None,
                value: Optional[float]=None
                ):
        assert path, "path cannot be None"
        assert array_idx is not None, "array_idx cannot be None for path '{}'".format(path)
        assert anim_type in {ANIM_TYPE_SHOW, ANIM_TYPE_HIDE, ANIM_TYPE_TRANSFORM}, "anim_type cannot be None or '', is {}".format(anim_type)
        if frame_number is not None:
            assert frame_number > 0, "frame_number must be > 0, as per Blender 2.49 behavior"
        assert any(map(lambda v: v is not None, [loop, show_hide_v1, show_hide_v2, value,])), "No meaningful values found with (loop={},show_hide_v1={},show_hide_v2={},value={})".format(loop, show_hide_v1, show_hide_v2, value)
        sh = {show_hide_v1, show_hide_v2}
        assert sh == {None, None} or any(map(lambda s: isinstance(s, float), sh)), "show_hide_v1/2 must be either both None or some floats"

        self.anim_type = anim_type

        #-------------------
        # Cloud Case Fix!
        # If the path has an idx portion in it,
        # the array_idx is a false result
        if idx_portion(path):
            self.array_idx = ""
        else:
            self.array_idx = array_idx
        #-------------------

        self.frame_number = frame_number
        self.loop = loop
        self.path = path
        self.show_hide_v1 = show_hide_v1
        self.show_hide_v2 = show_hide_v2
        self.value = value

    def __str__(self):
        return "{}".format((
            self.anim_type,
            self.array_idx,
            self.frame_number,
            self.loop,
            self.path,
            self.show_hide_v1,
            self.show_hide_v2,
            self.value,
            )
        )

def remove_vowels(s: str)->str:
    return ''.join([letter for letter in s if letter not in {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U', '_'}])

def make_short_name(full_path: DatarefFull)->SName:
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
                short=short+remove_vowels(comp)
            else:
                short=short+comp
        else:
            short=short+comp[0]
            if comp[-1] == '2':
                short=short+"2"
    return short

def getDatarefs()->Dict[Union[SName,TailName],LookupRecord]:
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
            # 7. Multiple indexed array types are allowed, such as 'flightmodel/parts/v_el [73][10][4]'
            if len(d)!=7 or d[0]!='2': # Diff #1
                raise err
            for line in f:
                d=line.split() #Annoying re-use of non-descriptive variable 'd'
                if not d: # Diff #2
                    continue
                if len(d)<3:
                    raise err
                sname=make_short_name(d[0])
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
_249_datarefs = getDatarefs()

#--------------------------------------------------------------------------------

def _do_dict_lookup(name:str)->Optional[LookupRecord]:
    if name in _249_datarefs and _249_datarefs[name]:
        dataref_full = _249_datarefs[name][0]
        array_size = _249_datarefs[name][1]
        return (dataref_full, array_size)
    else:
        return None


def get_known_dataref_from_shortname(dataref_short:SName)->Optional[LookupRecord]:
    '''
    Returns full dataref and array size from an sname lookup,
    or None if not found.

    Remember: This means that this was never in Datarefs.txt,
    unlike getting None from a tail-name lookup
    '''

    assert {'a','e','i','o','u'} & set(dataref_short) == None and dataref_short.count("_") <= 1, "{} is an invalid SName".format(dataref_short)
    return _do_dict_lookup(dataref_short)


def get_known_dataref_from_tailname(dataref_tailname:TailName)->Optional[LookupRecord]:
    '''
    Returns full dataref and array size from a tail-name look up,
    or None if not Found.

    Remember: This means that there is an ambiguity in Datarefs.txt,
    unlike getting None from an sname lookup
    '''

    return _do_dict_lookup(dataref_tailname)


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
def idx_portion(name:str)->str:
    '''Returns the right most [idx] portion of a name, if possible. Else ""'''
    try:
        return '[' + name.rsplit('[',1)[1]
    except IndexError:
        return ""


def no_idx(name:str)->str:
    '''Gives a name to simple string processing. Removes the right most "[idx]".'''

    # "double/trouble[0] int[10] y" was and is invalid,
    # but we only remove the right most index. Otherwise you're
    # changing the dataref decleration!
    # Compare:
    # "double/trouble[0] int y" vs "double/trouble[0] int[10] y"
    return name.rsplit('[',1)[0]


def sname_from_dataref_full(dataref_full:DatarefFull)->SName:
    '''Turns any full dataref into a shortname version'''
    return make_short_name(dataref_full)


def tailname_from_dataref_full(dataref_full:DatarefFull)->TailName:
    '''Gets the tail from any full dataref'''
    return dataref_full.split('/')[-1]


def decode_game_animvalue_prop(game_prop: bpy.types.GameProperty,
                               known_datarefs: Tuple[DatarefFull],
                               ) -> Optional[ParsedGameAnimValueProp]:
    '''
    Given a 2.49 short name, return the path, (frame_number, and a dictionary of properties)
    matching xplane_props.XPlaneDataref or None if there was a problem
    '''
    #This comes from attempting to understand XPlaneAnimObject.getvals, line 225-, line 987-999
    #and the property table of a real life example using sa_acf_struct

    #---This block of code attempts to parse the game prop--------------
    def parse_game_prop_name(game_prop: bpy.types.GameProperty)->Optional[Dict[str,str]]:
        # Warning: One has to later remove _loop. Also, "Cloud Case" aren't caught with this
        PROP_NAME_IDX_REGEX = r"(?P<prop_root>[a-zA-Z]\w+)(\[(?P<array_idx>\d+)\])?"
        PROP_NAME_SH = r"_(?P<showhide>show|hide)"
        PROP_NAME_FNUMBER = r"_v(?P<frame_number>\d+)"
        name = game_prop.name.strip()

        parsed_result = {"anim_type": "", "array_idx":"", "prop_root":"", "frame_number":None, "loop":None, "show_hide_v1":None, "show_hide_v2":None}

        print("Attempting to parse {}".format(game_prop.name))
        if re.search(PROP_NAME_IDX_REGEX + PROP_NAME_SH + PROP_NAME_FNUMBER + "$", name):
            print("1. Matched show/hide")
            parsed_result.update(
                re.search(PROP_NAME_IDX_REGEX + PROP_NAME_SH + PROP_NAME_FNUMBER + "$",
                         name).groupdict(default=""))
            parsed_result['anim_type'] = parsed_result['showhide']
            # Show/Hide Always comes in pairs (_v1,_v2), (_v3,_v4), etc. Later on, we'll compress them back into one
            parsed_result['show_hide_v1'] = game_prop.value if int(parsed_result['frame_number']) % 2 == 1 else None
            parsed_result['show_hide_v2'] = game_prop.value if int(parsed_result['frame_number']) % 2 == 0 else None
        elif re.search(r"_loop$", name):
            print("2. Matched loop")
            parsed_result.update(
                re.search(PROP_NAME_IDX_REGEX,
                    name).groupdict(default=""))
            parsed_result['anim_type'] = ANIM_TYPE_TRANSFORM
            # I got tired of re-writing the regex to try and make this work,
            # instead we manually remove '_loop' and be done with it.
            parsed_result['prop_root'] = parsed_result['prop_root'].split('_loop')[0]
            parsed_result['loop'] = game_prop.value
        elif re.search(PROP_NAME_FNUMBER + "$", name):
            print("3. Matched anim-value")
            parsed_result.update(
                re.search(PROP_NAME_IDX_REGEX+PROP_NAME_FNUMBER + "$",
                          name).groupdict(default=""))
            parsed_result['anim_type'] = ANIM_TYPE_TRANSFORM
        elif re.match(PROP_NAME_IDX_REGEX + "$", name):
            print("4. Matched disambiguating key or other text")
            print("Text: {}".format(name))
            return None
        else:
            print("5. Could not parse text")
            print("Unparsable Text: {}".format(name))
            return None

        assert parsed_result['anim_type'] or parsed_result['frame_number'] or parsed_result['loop'], "Parsed game_prop.name is missing meaningful values: {}".format(parsed_result)
        #print("Parse Results: {}".format(parsed_result))
        return parsed_result

    parsed_result = parse_game_prop_name(game_prop)
    if not parsed_result:
        return None
    elif parsed_result['array_idx']:
        roots_to_test = [
            parsed_result['prop_root'],
            # Coincidentally (or perhaps too cleverly) also takes care of cloud cases
            parsed_result['prop_root'] + "[{}]".format(parsed_result['array_idx']),
            ]
    else:
        roots_to_test = [parsed_result['prop_root']]

    for known_dataref in known_datarefs:
        '''
        # Previously we've done:
        # Use bone name (TailName) to look up Disambiguating Game Prop
        # for all_arm_drefs[disamb_path]
        # Now to get the tailname to lookup a custom dataref that would have needed
        # disambiguating we
        # Match the known dataref's sname version to our root to test, and with this this knowledge
        # know that the tailname is the disambiguating key.
        #
        # The next will then use this during its matching phase.
        #
        # "But if we already know what we'll find, why bother?!" you say.
        # Its better to reduce the amount of flow here. Also, precedent.
        '''

        sname = make_short_name(known_dataref)
        if sname in roots_to_test:
            roots_to_test.append(tailname_from_dataref_full(known_dataref))
            break # We know that duplicate snames aren't possible

    print("Testing Roots: {}".format(roots_to_test))
    #------------------------------------------------------------------

    #------------------------------------------------------------------
    # Our very important out path
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
                known_sname = make_short_name(known_dataref)
                # In case the disambiguating key of a custom dataref is
                # also in the Datarefs.txt file, we check our .blend file before checking
                # DataRefs.txt
                if prop_root == known_tail: # Disambiguating key, TailName
                    return known_dataref
                # Works for Known SNames, TailNames and the annoying + "[idx]" cloud case
                elif prop_root in _249_datarefs:
                    #print("prop_root (in _249_datarefs): {}".format(prop_root))
                    # 1. Tail-Name could be None or in there. Duplicate (this also captures sname case sometimes)
                    if (_249_datarefs[prop_root] and _249_datarefs[prop_root][0] == known_dataref):
                        return known_dataref
            else: #nobreak
                print("prop_root: {} didn't match any of the known_datarefs".format(prop_root))
                return None
        path = match_root_to_known_datarefs(prop_root, known_datarefs) # type: DatarefFull
        if path:
            break
    else: #nobreak
        assert False, "Couldn't match prop_root {} to anything, which isn't how you're developing right now!".format(roots_to_test)

    #print("Final Path: " + path)
    #------------------------------------------------------------------

    #------------------------------------------------------------------
    #TODO: logging, not asserting

    assert game_prop.type in {"INT", "FLOAT"}, "game_prop ({},{}) value is not 'FLOAT' vs 'INT'".format(game_prop.name, game_prop.value)

    if (parsed_result['anim_type'] == ANIM_TYPE_TRANSFORM
        and not parsed_result['loop']):
        frame_number = int(parsed_result['frame_number'])
    else:
        frame_number = None

    if parsed_result['loop'] is None and parsed_result['anim_type'] == ANIM_TYPE_TRANSFORM:
        value = float(game_prop.value)
    else:
        value = None

    # Show/Hide always have _v1 and _v2, defaults came from the UI code.
    # Here 1 and 2 does not mean "Frame 1 and 2" but simply "Value 1 and 2"
    parsed_prop = ParsedGameAnimValueProp(
            path = path,
            array_idx = "[{}]".format(parsed_result['array_idx']) if parsed_result['array_idx'] else '',
            anim_type = parsed_result['anim_type'],
            frame_number = frame_number,
            loop = parsed_result['loop'],
            show_hide_v1 = parsed_result['show_hide_v1'],
            show_hide_v2 = parsed_result['show_hide_v2'],
            value = value
            )

    print("Final Decoded Results: {}".format(parsed_prop))
    #------------------------------------------------------------------
    return parsed_prop

def convert_armature_animations(armature:bpy.types.Object):
    #TODO: Create log, similar to conversion log

    if armature:
        print("Decoding Game-Properties for '{}'".format(armature.name))
        bpy.context.scene.objects.active = armature

        def find_all_datarefs_in_armature(armature: bpy.types.Object)->Dict[DatarefFull,Tuple[bpy.types.PoseBone,List[ParsedGameAnimValueProp]]]:
            '''
            Returns a dictionary all datarefs mentioned in the bone names and game props,
            paired with the Bone the data was taken from an a list for
            future parsed game properties.

            Bones without useful names are ignored.
            '''

            all_arm_drefs = OrderedDict() # type: OrderedDict[DatarefFull,Tuple[Union[bpy.types.PoseBone,bpy.types.Object]],List[ParsedGameAnimValueProp]]]

            for game_prop in filter(lambda p: p.type == "STRING", armature.game.properties):
                def find_key_uses(key_to_match:str)->bool:
                    '''
                    We can use this to find places where the potential disambiguation key
                    is actually used in a show/hide property. If, after filtering, we find
                    we have some show/hide props for this key, this key is added to all_arm_drefs
                    '''
                    name = key_to_match.strip()
                    REGEX_STR = ''.join([r"(?P<prop_root>" + game_prop.name + ")",
                                         r"(\[(?P<array_idx>\d+)\])?",
                                         r"_(?P<showhide>show|hide)",
                                         r"_v(?P<frame_number>\d+)"]) + "$"

                    try:
                        return re.match(REGEX_STR, name).groupdict()['prop_root'] == game_prop.name
                    except:
                        return None

                print("Attempting to find uses of (%s/%s)" % (game_prop.value, game_prop.name))
                matching_key_users = list(
                        filter(lambda p: find_key_uses(p.name),
                            filter(lambda p: "_show_" in p.name or "_hide_" in p.name, armature.game.properties)
                    )
                )

                print("Matching uses of potential disambiguation key")
                print([f.name for f in matching_key_users])
                if matching_key_users:
                    disambiguating_key = "{}/{}".format(game_prop.value.strip(" /"), game_prop.name.strip())
                    print("Disambiguating Key: " + disambiguating_key)
                    all_arm_drefs[disambiguating_key] = (armature,[]) # Show hide applies to armature object

            for bone in armature.pose.bones:
                # 2.49 slices and trims bone names before look up
                bone_name = bone.name.split('.')[0].strip() # type: BoneName
                bone_name_no_idx = no_idx(bone_name) # type: Union[SName,TailName]

                print("\nLooking up dataref from '{}' and '{}'".format(bone_name, bone_name_no_idx))
                lookup_result = lookup_dataref(bone_name, bone_name_no_idx)

                print("Lookup Results: %s" % lookup_result)
                if lookup_result.record:
                    all_arm_drefs[lookup_result.record[0]] = (bone, [])
                else:
                    # Catches known but ambiguous and unknown datarefs. Needs disambiguating
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

        all_arm_drefs = find_all_datarefs_in_armature(armature) # type: OrderedDict[DatarefFull,Tuple[bpy.types.PoseBone,List[ParsedGameAnimValueProp]]]

        for game_prop in armature.game.properties:
            print("\ngame_prop.name: {}, value: {}".format(game_prop.name, game_prop.value))
            decoded_animval = decode_game_animvalue_prop(game_prop, tuple(all_arm_drefs.keys()))
            if decoded_animval:
                assert decoded_animval.path in all_arm_drefs, "How is this possible! path not in all_arm_drefs! " + decoded_animval.path
                existing_props = all_arm_drefs[decoded_animval.path][1]
                # Show/Hide v1 and v2 will come in as seperate properties,
                # but test_creation_helpers needs them together
                if (existing_props
                    and existing_props[-1].anim_type in {ANIM_TYPE_SHOW, ANIM_TYPE_HIDE}
                    and existing_props[-1].show_hide_v2 is None):
                    assert existing_props[-1].path == decoded_animval.path, "show hide props out of order"
                    existing_props[-1].show_hide_v2 = decoded_animval.show_hide_v2
                    all_arm_drefs.move_to_end(decoded_animval.path) # As we parse game props, we re-order the show/hide disambiguous keys by the order the props are in, not the keys
                else:
                    all_arm_drefs[decoded_animval.path][1].append(decoded_animval)
            else:
                #TODO: Error code goes here? How do we do these?
                #TODO: What about disambiguating keys returning none from decode_game_animvalue?
                print("Could not decode {}".format(game_prop.name))
                continue

        for path, (bone, parsed_props) in all_arm_drefs.items():
            # A sorted list of each bone's channel's min/max gets us the first and last created frames
            try:
                s = sorted([c.range() for c in armature.animation_data.action.groups[bone.name].channels])
            except KeyError:
                continue

            first_frame = int(s[0][0]) # min value of smallest member in list
            last_frame = max(int(s[-1][1]), 2) # Max val of largest member or 2 (for datarefs with only 0 or 1 parsed props)

            print("\nBone name {}: Filling between first_frame {}, last_frame {}".format(bone.name,first_frame,last_frame))
            frameless_props = []
            keyframe_props = []
            for p in parsed_props:
                if p.frame_number:
                    keyframe_props.append(p)
                else:
                    frameless_props.append(p)

            keyframe_props.sort(key=attrgetter('frame_number'))

            for ensure_has in range(1,last_frame+1):
                ensure_has_idx = ensure_has-1
                # 2.49 makes sure every Blender keyframe has a 
                # dataref value of 0 (if first frame) or 1
                # to go with. If missing, it is filled in.
                new_pp_frame = ParsedGameAnimValueProp(
                        path=path,
                        array_idx=idx_portion(bone.name),
                        anim_type=ANIM_TYPE_TRANSFORM,
                        frame_number=ensure_has,
                        value=int(bool(ensure_has_idx))) # Why int? To match 2.49 behavior of using ints, which was and probably is meaningless.
                try:
                    if keyframe_props[ensure_has_idx].frame_number != ensure_has:
                        print("Inserting at %d" % ensure_has_idx)
                        keyframe_props.insert(ensure_has_idx, new_pp_frame)
                except IndexError:
                    print("Inserting at %d" % ensure_has_idx)
                    keyframe_props.insert(ensure_has_idx, new_pp_frame)

            parsed_props[:] = keyframe_props + frameless_props

        # Finally, the creation step!
        for path, (bone, parsed_props) in all_arm_drefs.items():
            for parsed_prop in parsed_props:
                if parsed_prop.value is not None:
                    #TODO: Must use no_ref for show_hide paths, but what does that mean?
                    test_creation_helpers.set_animation_data(
                        bone, [
                            test_creation_helpers.KeyframeInfoDatarefKeyframe(
                                dataref_path=path + parsed_prop.array_idx,
                                frame_number=parsed_prop.frame_number,
                                dataref_value=parsed_prop.value,
                                )
                        ],
                        parent_armature=armature
                    )
                elif parsed_prop.loop is not None:
                    test_creation_helpers.set_animation_data(
                        bone, [
                            test_creation_helpers.KeyframeInfoLoop(
                                dataref_path=path + parsed_prop.array_idx,
                                dataref_loop=parsed_prop.loop,
                                ),
                            ],
                            parent_armature=armature
                        )
                elif {parsed_prop.show_hide_v1,parsed_prop.show_hide_v2} != {None,None}:
                    test_creation_helpers.set_animation_data(
                        bone, [
                            test_creation_helpers.KeyframeInfoShowHide(
                                dataref_path=path + parsed_prop.array_idx,
                                dataref_anim_type=parsed_prop.anim_type,
                                dataref_show_hide_v1=parsed_prop.show_hide_v1,
                                dataref_show_hide_v2=parsed_prop.show_hide_v2,
                                ),
                            ],
                            parent_armature=armature
                        )

                else:
                    assert False, "How did we get here? {}".format(parsed_prop)
