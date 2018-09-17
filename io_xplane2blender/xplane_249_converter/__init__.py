import os
import re
from typing import Any, Dict, Optional, Tuple

import bpy

from io_xplane2blender.tests import test_creation_helpers

def _remove_vowels(s):
    for eachLetter in s:
        if eachLetter in ['a','e','i','o','u','A','E','I','O','U','_']:
            s = s.replace(eachLetter, '')
    return s

def _make_short_name(full_path:str)->str:
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

def _getDatarefs()->Tuple[Dict[str,Tuple[str,int]],Dict[str,Dict[str,Any]]]:#JSON-Like]]]: 
    '''
    Returns the dataref file in two forms. First a dictionary of short_name (or if small enough, the tail of the dataref)->(dataref_full,0 = not usable, 1 = scalar, > 1 array).
    Prop names have a maximum size of 31 characters, so, at some point the dataref is too long for the table (but is still saved anyway (why!?))
    
    Second is a dictionary of dictionaries, where each key is a portion of the dataref path, until the final dictionary which contains every tailhook_deploy
    end as a key and the array size as the value.
    This appears to be used in the popup menu for selecting a dataref in the AnimObject script window and will likely not be needed
    '''

    '''
    A reperesentation of the output of this
    ({
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
    },
    {
       'sim':{
          'aircraft':{
             'acf_struct':10,
             'view':{
                'acf_descrip':0,
                'acf_author':0,
                'acf_notes':0,
                'acf_size_x':1,
                'acf_tailnum':0,
                'acf_size_z':1
             }
          }
       }
    })
    '''
    #counts appears to be unused 
    #counts={'engines':8,
    #        'wings':56, # including props and pylons?
    #        'doors':20,
    #        'gear':10}
    datarefs={}
    hierarchy={}
    err=IOError(0, "Corrupt DataRefs.txt file. Please re-install.")
    try:
        #TODO: Does not need this
        with open(os.path.join(os.path.dirname(__file__), "DataRefs_249.txt")) as f:
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

                #this appears to be an alias for hierarchy
                #and is used to iteratively build this tree
                this=hierarchy
                for i in range(len(ref)-1):
                    if not ref[i] in this:
                        this[ref[i]]={}
                    this=this[ref[i]]
                this[ref[-1]]=n

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
    res = (datarefs, hierarchy)
    #print res
    return res

'''
These are all the Datarefs.txt in 249 regular and hierarchy formats
'''
(_249_datarefs,_249_hierarchy) = _getDatarefs()

#--------------------------------------------------------------------------------
def get_dataref_from_shortname(dataref_short:str)->Optional[Tuple[str,int]]:
    #TODO What about custom datarefs? like whatever/leaf?
    "Object has property {'leaf':'whatever','w_leaf_v1':-14,'w_leaf_v2':52.599}"
    if dataref_short in _249_datarefs: 
        dataref_full = _249_datarefs[dataref_short][0]
        array_size = _249_datarefs[dataref_short][1]
        return (dataref_full,array_size)
    else:
        return None

def get_shortname_from_dataref(dataref_full:str)->Optional[str]:
    return _make_short_name(dataref_full)

def decode_shortname_properties(dataref_short:str)->Tuple[str,Tuple[Optional[int],Dict[str,Any]]]:
    '''
    Given a 2.49 short name, return the path, frame_number, and a dictionary of properties
    matching xplane_props.XPlaneDataref
    '''
    #This comes from attempting to understand XPlaneAnimObject.getvals, line 225-, line 987-999
    #and the property table of a real life example using sa_acf_struct
    
    #print("DFSHORT: " + dataref_short)
    #TODO: Show/Hide doesn't work like the rest for path. It gets split? Value forms part of dataref
    match = re.match(r"(?P<path>[a-z]\w+)(?P<idx>\[\d+\])?"+\
                     r"(?P<anim_type>_show|_hide)?(?P<prop>_v(?P<frame_number>\d)|_loop)",dataref_short)

    try:
        m_dict = match.groupdict(default="")
        # print("M_DICT: {}".format(m_dict))
        path = get_dataref_from_shortname(m_dict['path'])[0] + m_dict['idx'] # type: str
        frame_number = None # type: int
        props = dict(
            #Matches XPlaneDataref, not dataref_short
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
    except AttributeError:
        return None, None

def do_249_conversion():
    # Global settings
    bpy.context.scene.xplane.debug = True
    #TODO: Take file name and make it layer name (TODO: What about root objects mode?)
    #TODO: Remove clean up workspace as best as possible,
    # remove areas with no space data and change to best
    # defaults like Action Editor to Dope Sheet

    # Make the default material for new objects to be assaigned
    # TODO: Only needed if you have cubes without materials? Don't create,
    # except for test files? Just don't be lazy about test files
    for armature in filter(lambda obj: obj.type == 'ARMATURE', bpy.data.objects):
        bpy.context.scene.objects.active = armature
        # All datarefs mentioned by game properties for bones of this armature
        all_datarefs = {}
        for game_prop in armature.game.properties:
            path,prop_info = decode_shortname_properties(game_prop.name)
            if not path:
                continue
            prop_info[1].update(value=game_prop.value)
            print(prop_info[0])
            print(prop_info[1])
            if path not in all_datarefs:
                all_datarefs[path] = []
            #TODO: What about multiple datarefs?
            all_datarefs[path].append(prop_info)

        for k in all_datarefs:
            all_datarefs[k] = sorted(all_datarefs[k])

        # What was the rule for multiple bones? Don't? Oh yes, don't! Short names must be unique or the whole system
        # falls apart!
        #for pose_bone in armature.pose.bones:
        for path,dref_info in all_datarefs.items():
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

