'''
This module handles converting Ben Russel's (old) manipulator scheme
and Ondrej's (new) manipulator scheme.

Reading List:

- https://github.com/der-On/XPlane2Blender/wiki/2.49:-How-It-Works:-Manipulators
'''
import os
import re

import bpy
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_constants import (ANIM_TYPE_HIDE, ANIM_TYPE_SHOW,
                                                ANIM_TYPE_TRANSFORM,
                                                MANIP_AXIS_KNOB,
                                                MANIP_AXIS_SWITCH_LEFT_RIGHT,
                                                MANIP_AXIS_SWITCH_UP_DOWN,
                                                MANIP_CURSOR_HAND, MANIP_DELTA,
                                                MANIP_WRAP,
                                                MANIPULATORS_MOUSE_WHEEL)
from typing import Callable, Dict, List, Optional, Tuple, Union

# Key is ATTR_manip_type, value is dict of manip nn@attributes and their values
OndrejManipInfo = Dict[str, Union[int, float, str]]
def getManipulators()->Tuple[Dict[str, OndrejManipInfo], List[str]]:
    """Returns data defining x-plane manipulators
    This method currently hard-codes the data definitions for manipulators and
    the associated cursors. Descriptions for manipulators can be found at:
    http://wiki.x-plane.com/Manipulators
    http://scenery.x-plane.com/library.php?doc=obj8spec.php

    Return values:
    manipulators -- Dictionary of "ATTR_manip*": Dict["nn@ondrej_attr_name", defaults  of 0, 0.0, or ""]
    property names nearly match XPlaneManipSettings. the nn@ is for sorting the keys by a particular order,
    for during XPlaneAnimObject.getmanipulatorvals

    cursors -- An array of strings of all possible cursors
    """
    manipulators={} # type: Dict[str, OndrejManipInfo]
    # cursors is xplane_constants.MANIP_CURSOR_*,
    # except 'down' and 'up' are switched
    cursors=['four_arrows',
             'hand',
             'button',
             'rotate_small',
             'rotate_small_left',
             'rotate_small_right',
             'rotate_medium',
             'rotate_medium_left',
             'rotate_medium_right',
             'rotate_large',
             'rotate_large_left',
             'rotate_large_right',
             'up_down',
             'down',
             'up',
             'left_right',
             'right',
             'left',
             'arrow']

    manipulators['ATTR_manip_none']= {'00@NULL':0}
    manipulators['ATTR_manip_drag_xy'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@v1min':0.0, '04@v1max':0.0, '05@v2min':0.0, '06@v2max':0.0, '07@dref1':'', '08@dref2':'', '09@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_drag_axis'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@dz':0.0, '04@v1':0.0, '05@v2':0.0, '06@dataref':'', '07@tooltip':'', '98@wheel':0.0}
    manipulators['ATTR_manip_command'] = {'00@cursor': '', '02@command':'', '03@tooltip':''}
    manipulators['ATTR_manip_command_axis'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@dz':0.0, '04@pos-command':'', '05@neg-command':'', '06@tooltip':'', '98@wheel':0.0}
    manipulators['ATTR_manip_noop']= {'00@dataref':'', '01@tooltip':''}
    manipulators['ATTR_manip_push'] = {'00@cursor': '', '01@v-down':0.0, '02@v-up':0.0, '03@dataref':'', '04@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_radio'] = {'00@cursor': '', '01@v-down':0.0, '02@dataref':'', '03@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_toggle'] = {'00@cursor': '', '01@v-on':0.0, '02@v-off':0.0, '03@dataref':'', '04@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_delta'] = {'00@cursor': '', '01@v-down':0.0, '02@v-hold':0.0, '03@v-min':0.0, '04@v-max':0.0, '05@dataref':'', '06@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_wrap'] = {'00@cursor': '', '01@v-down':0.0, '02@v-hold':0.0, '03@v-min':0.0, '04@v-max':0.0, '05@dataref':'', '06@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_drag_axis_pix'] = { '00@cursor': '', '01@length':0.0, '02@step':0.0, '03@power':0.0, '04@v-min':0.0, '05@v-max':0.0, '06@dataref':'','07@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_command_knob'] = { '00@cursor':'rotate_medium', '01@pos-command':'', '02@neg-command':'', '03@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_command_switch_up_down'] = { '00@cursor':'up_down', '01@pos-command':'', '02@neg-command':'', '03@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_command_switch_left_right'] = { '00@cursor':'left_right', '01@pos-command':'', '02@neg-command':'', '03@tooltip':'','98@wheel':0.0}

    manipulators['ATTR_manip_axis_knob'] = { '00@cursor':'rotate_medium', '01@v-min':'', '02@v-max':'', '03@step':'','04@hold':'','05@dataref':'', '06@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_axis_switch_up_down'] = { '00@cursor':'up_down', '01@v-min':'', '02@v-max':'', '03@step':'','04@hold':'','05@dataref':'', '06@tooltip':'','98@wheel':0.0}
    manipulators['ATTR_manip_axis_switch_left_right'] = { '00@cursor':'left_right', '01@v-min':'', '02@v-max':'', '03@step':'','04@hold':'','05@dataref':'', '06@tooltip':'','98@wheel':0.0}

    manipulators['ATTR_manip_command_knob2'] = {'00@cursor': '', '02@command':'', '03@tooltip':''}
    manipulators['ATTR_manip_command_switch_up_down2'] = {'00@cursor': '', '02@command':'', '03@tooltip':''}
    manipulators['ATTR_manip_command_switch_left_right2'] = {'00@cursor': '', '02@command':'', '03@tooltip':''}

    manipulators['ATTR_manip_drag_rotate'] = {
        '00@cursor':'hand',
        '01@pivot_x':'',
        '02@pivot_y':'',
        '03@pivot_z':'',
        '04@axis_dx':'',
        '05@axis_dy':'',
        '06@axis_dz':'',
        '07@angle-min':'',
        '08@angle-max':'',
        '09@lift-len':'',
        '10@v1min':'',
        '11@v1max':'',
        '12@v2min':'',
        '13@v2max':'',
        '14@dref1':'',
        '15@dref2':'',
        '16@tooltip':'',
        '95@detentz':'',
        '96@detents':'',
        '97@keyframes':'',
        '98@wheel':'0.0'
        }

    return (manipulators, cursors)

ondrej_manipulators, ondrej_cursors = getManipulators()

class ParsedManipulatorInfo():
    """
    The final manipulator output, matching XPlaneManipulatorSettings. Since it may be applied
    to multiple objects that are children of the armature, it does not directly change any
    Blender properties
    """
    #TODO: Inputs are validated so that each type has what it needs and only what it needs
    #being passed in.
    def __init__(self, manipulator_type: str, **kwargs: Dict[str,Union[int,float,str]]):
        '''
        Takes the contents of a manipulator_dict's sub dictionary and translates them into
        something matchining XPlaneManipulatorSettings,
        '''
        self.axis_detent_ranges = [] # type: List[Tuple[float, float, float]]

        assert manipulator_type.startswith("ATTR_manip_"), "manipulator_type must start with ATTR_manip_"
        self.type = manipulator_type.replace("ATTR_manip_", "") # type: str

        if self.type == "drag_rotate" and (kwargs.get('detentz', "") + kwargs.get('detents', "")):
            self.type = "drag_rotate_detent"

        self.tooltip          = "" # type: str
        self.cursor           = MANIP_CURSOR_HAND # type: str
        self.dx               = 0.0 # type: float
        self.dy               = 0.0 # type: float
        self.dz               = 0.0 # type: float
        self.v1               = 0.0 # type: float
        self.v2               = 0.0 # type: float
        self.v1_min           = 0.0 # type: float
        self.v1_max           = 0.0 # type: float
        self.v2_min           = 0.0 # type: float
        self.v2_max           = 0.0 # type: float
        self.v_down           = 0.0 # type: float
        self.v_up             = 0.0 # type: float
        self.v_hold           = 0.0 # type: float
        self.v_on             = 0.0 # type: float
        self.v_off            = 0.0 # type: float
        self.command          = "" # type: str
        self.positive_command = "" # type: str
        self.negative_command = "" # type: str
        self.dataref1         = "" # type: str
        self.dataref2         = "" # type: str
        self.step             = 0.0 # type: float
        self.click_step       = 0.0 # type: float
        self.hold_step        = 0.0 # type: float
        self.wheel_delta      = 0.0 # type: float
        self.exp              = 0.0 # type: float

        def translate_manip_attr(manipulator_type: str, attr: str)->Optional[Tuple[Callable, str]]:
            '''
            Returns the XPlaneManipulatorSettings attr name and the function to convert it
            of Ondrej or BR's (TODO) manipulator info encoding,
            or None if no such mapping exists
            '''
            attr_translation_map = {
                # 2.49 -> 2.7x
                "manipulator-name": None, # See use of manipulator_type instead

                #Exceptions:
                #
                # noop doesn't have a cursor, so we use the default "hand"
                "cursor"      : (str, "cursor"),

                "tooltip"     : (str, "tooltip"),
                "NULL"        : None,
                "angle-max"   : None, # Drag Rotate now auto detects this
                "angle-min"   : None, # Drag Rotate now auto detects this
                "axis_dx"     : None, # Drag Rotate now auto detects this
                "axis_dy"     : None, # Drag Rotate now auto detects this
                "axis_dz"     : None, # Drag Rotate now auto detects this
                "command"     : (str, "command"),
                "dataref"     : (str, "dataref1"),
                "detentz"     : None, # str->List[Tuple[float,float,float]] of Axis Detent Range
                "detents"     : None, # A second line for even more axis detent range
                "dref1"       : (str, "dataref1"),
                "dref2"       : (str, "dataref2"),
                "dx"          : (float, "dx"),
                "dy"          : (float, "dy"),
                "dz"          : (float, "dz"),
                "hold"        : (float, "hold_step"),
                "keyframes"   : None, # Completely dropped, manip_keyframe is autodetected
                "length"      : (float, "dx"),
                "lift-len"    : None,
                "neg-command" : (str, "negative_command"),
                "pivot_x"     : None,
                "pivot_y"     : None,
                "pivot_z"     : None,
                "pos-command" : (str, "positive_command"),
                "power"       : (float, "exp"),

                # Exceptions:
                # 2.78 axis_knob, axis_switch_up_down, axis_switch_left_right
                # has this special case "step"->"click_step"
                "step"        : (float, "step"),

                "v-down"      : (float, "v_down"),
                "v-hold"      : (float, "v_hold"),

                # Exceptions:
                # 2.78 Delta and Wrap use v1_min/max
                "v-min"       : (float, "v1"),
                "v-max"       : (float, "v2"),

                "v-off"       : (float, "v_off"),
                "v-on"        : (float, "v_on"),
                "v-up"        : (float, "v_up"),
                "v1"          : (float, "v1"),
                "v1min"       : (float, "v1_min"),
                "v1max"       : (float, "v1_max"),
                "v2"          : (float, "v2"),
                "v2min"       : (float, "v2_min"),
                "v2max"       : (float, "v2_max"),

                # Exceptions:
                # In 2.49 some manipulators erroniously include this:
                # during export we ignore it
                "wheel"       : (float, "wheel_delta"),
            }

            try:
                # Several 2.49 manipulators allowed wheel to be specified, we ignore that data
                # (even if the exporter ignores these later as well)
                manipulator_type = manipulator_type.replace("ATTR_manip_", "")
                if (manipulator_type not in MANIPULATORS_MOUSE_WHEEL) and attr == "wheel":
                    return None

                if (
                        manipulator_type in {
                            MANIP_AXIS_KNOB,
                            MANIP_AXIS_SWITCH_UP_DOWN,
                            MANIP_AXIS_SWITCH_LEFT_RIGHT
                        }
                        and attr == "step"
                    ):
                    return (float, "click_step")

                if (manipulator_type in {MANIP_DELTA, MANIP_WRAP}):
                    if attr == "v-min":
                        return (float, "v1_min")
                    if attr == "v-max":
                        return (float, "v1_max")

                return attr_translation_map[attr]
            except KeyError:
                assert False, "Not yet implementing error handling for unknown attrs like " + attr

        # Inner "   " prevents "0" + ".25" -> "0.25"
        detents_list = list(
            map(float,
                "".join(
                        (
                            kwargs.get("detentz", ""),
                            "    ",
                            kwargs.get("detents", "")
                        )
                ).split()
            )
        )
        #print("249 detents", detents_list)
        assert len(detents_list) % 3 == 0, \
           "len(detents + detentz) {} % 3 != 0, is {}. Uncaught error" \
           .format(len(detents_list), len(detents_list) % 3)
        self.axis_detent_ranges = [
            (detents_list[i], detents_list[i+1], detents_list[i+2])
            for i in range(0, len(detents_list), 3)
        ]

        print("--- Translating Manipulator Attributes ---")
        for manip_attr, value in kwargs.items():
            if (isinstance(value, (int, float, str))
                and translate_manip_attr(manipulator_type, manip_attr)
               ):
                print(manip_attr, value)
                translated_manip_attr = translate_manip_attr(manipulator_type, manip_attr)
                assert hasattr(self, translated_manip_attr[1]), \
                       "{} not in ParsedManipulatorInfo".format(translated_manip_attr[1])
                setattr(self, translated_manip_attr[1], translated_manip_attr[0](value))
        print("---")


def _getmanipulator(armature: bpy.types.Object)->Optional[OndrejManipInfo]:
    try:
        manipulator_type = armature.game.properties['manipulator_type'].value
        if manipulator_type == 'ATTR_manip_none':
            return None
    except KeyError:
        return None

    # If the manipulator_type was long enough, we cut it off
    if manipulator_type.startswith("ATTR_manip_command_") and len(manipulator_type) > 23:
        manip_key = manipulator_type.replace("ATTR_manip_command_", "") # type: str
    elif manipulator_type.startswith("ATTR_manip_") and len(manipulator_type) > 23:
        manip_key = manipulator_type.replace("ATTR_manip_", "") # type: str
    else:
        manip_key = manipulator_type

    manipulator_dict, _ = getManipulators()
    # Loop through every manip property, mapping property key -> manip_info key
    for prop in filter(lambda p: p.name.startswith(manip_key), armature.game.properties):
        potential_ondrej_attr_key = prop.name.split('_')[-1]
        for real_ondrej_attr_key in manipulator_dict[manipulator_type]:
            if potential_ondrej_attr_key in real_ondrej_attr_key:
                manipulator_dict[manipulator_type][real_ondrej_attr_key] = prop.value

    manipulator_dict[manipulator_type]['99@manipulator-name'] = manipulator_type
    return ParsedManipulatorInfo(manipulator_type, **{ondrej_key[3:]: value for ondrej_key, value in manipulator_dict[manipulator_type].items()})


def _anim_decode(obj: bpy.types.Object)->Optional[OndrejManipInfo]:
    m = _getmanipulator(obj)
    if m is None:
        if obj.parent is None:
            return None
        if obj.type == 'MESH':
            assert False, "Recusive manip info in parent look up not implemented yet"
            return _anim_decode(obj.parent)
        return None

    return m


def _decode(armature: bpy.types.Object):
    #properties = obj.getAllProperties()
    properties = armature.game.properties
    objname = armature.name

    #setup default manipulator attribute values
    manip_iscommand_br    = False
    manip_is_push_tk    = False
    manip_is_toggle_tk    = False
    manip_command_br    = "<command>"
    manip_cursor_br     = "<cursor>"
    manip_x_br             = "<x>"
    manip_y_br             = "<y>"
    manip_z_br             = "<z>"
    manip_val1_br         = "<val1>"
    manip_val2_br         = "<val2>"
    manip_dref_br         = "<dref>"
    manip_tooltip_br     = "<tooltip>"

    manip_bone_name_br    = "" #--leave this blank by default, if its not blank the code will try and find the bone name

    for prop in properties:
        if( prop.name == "mnp_iscommand" ):     manip_iscommand_br    = prop.data #--expects a boolean value
        if( prop.name == "mnp_command" ):        manip_command_br    = prop.data.strip()
        if( prop.name == "mnp_cursor" ):         manip_cursor_br     = prop.data.strip()
        if( prop.name == "mnp_dref" ):             manip_dref_br         = prop.data.strip()
        if( prop.name == "mnp_tooltip" ):         manip_tooltip_br    = prop.data.strip()
        if( prop.name == "mnp_bone" ):             manip_bone_name_br     = prop.data.strip()
        if( prop.name == "mnp_v1" ):             manip_val1_br         = str(prop.data)
        if( prop.name == "mnp_v2" ):             manip_val2_br         = str(prop.data)
        if( prop.name == "mnp_is_push" ):        manip_is_push_tk    = prop.data
        if( prop.name == "mnp_is_toggle" ):        manip_is_toggle_tk    = prop.data

    # BR's weird scheme: if there is NO mnp_bone there is no manip, get out.  But the magic
    # bone names arm_ are place-holders - they're not REAL armatures, it's just a place-holder
    # to make the export work.

    # No BR bone name?  Run Ondrej's decoder.
    if manip_bone_name_br == "":
        return _anim_decode(armature)

    if( manip_bone_name_br != "" and manip_bone_name_br != "arm_" ):
        obj_manip_armature_br = bpy.data.objects[manip_bone_name_br] # Or is this not getting the armature? bpy.Object.Get means what?
        if( obj_manip_armature_br != None ):
            obj_manip_armature_data_br = obj_manip_armature_br.getData()
            obj_manip_bone_br = obj_manip_armature_data_br.bones.values()[0]

            vec_tail = obj_manip_bone_br.tail['ARMATURESPACE']
            vec_arm = [obj_manip_armature_br.LocX, obj_manip_armature_br.LocY, obj_manip_armature_br.LocZ]

            #blender Y = x-plane Z, transpose
            manip_x_br = str( round(vec_tail[0],3) )
            manip_y_br = str( round(vec_tail[2],3) )
            manip_z_br = str( round(-vec_tail[1],3) ) #note: value is inverted.

            #self.file.write( str( vec_tail ) + "\n" )
            #self.file.write( str( vec_arm ) + "\n" )



    data = ""


    #TODO: We don't need this, we need to return here our own ManipInfo class
    return

    '''
    if( manip_iscommand_br ):
        #wiki def: ATTR_manip_command <cursor> <command> <tooltip>
        data = ("ATTR_manip_command %s %s %s"
                                                %(manip_cursor_br,
                                                manip_command_br,
                                                manip_tooltip_br))
    elif( manip_is_push_tk):
        data = ("ATTR_manip_push %s %s %s %s"
                                                %(manip_cursor_br,
                                                manip_val1_br,
                                                manip_val2_br,
                                                manip_dref_br))
    elif( manip_is_toggle_tk):
        data = ("ATTR_manip_toggle %s %s %s %s"
                                                %(manip_cursor_br,
                                                manip_val1_br,
                                                manip_val2_br,
                                                manip_dref_br))

    else:
        #wiki def: ATTR_manip_drag_axis <cursor> <x> <y> <z> <value1> < value2> <dataref> <tooltip>
        data = ("ATTR_manip_drag_axis %s %s %s %s %s %s %s %s"
                                                %(manip_cursor_br,
                                                manip_x_br,
                                                manip_y_br,
                                                manip_z_br,
                                                manip_val1_br,
                                                manip_val2_br,
                                                manip_dref_br,
                                                manip_tooltip_br))


    if data.find("<x>") != -1:
        print(properties)
        raise ExportError("%s: Manipulator '%s' is incomplete but was still exported." % (objname, data))

    return data
    '''

def convert_armature_manipulator(armature:bpy.types.Object)->None:
    '''
    Converts any manipulator game properties in an armature
    and applies it to all any meshes it is a child of
    '''

    print("Decoding manipulator for '{}'".format(armature.name))
    parsed_manip_info = _decode(armature) # type: ParsedManipulatorInfo
    if not parsed_manip_info:
        return

    for obj in filter(lambda child: child.type == "MESH", armature.children):
        setattr(obj.xplane.manip, "enabled", True)
        for attr, value in vars(parsed_manip_info).items():
            if attr == "axis_detent_ranges":
                for (start, end, height) in value:
                    r = obj.xplane.manip.axis_detent_ranges.add()
                    r.start, r.end, r.height = (start, end, height)
            else:
                setattr(obj.xplane.manip, attr, value)
