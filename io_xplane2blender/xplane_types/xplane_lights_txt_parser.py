import collections
import copy
import functools
import math
import os
from collections import OrderedDict

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger
from mathutils import Vector
from numbers import Number
from typing import List


'''
API Rules:
1. After reading the file, we only have valid data
2. All data is transformed to it's correct state ("float"->float) before entering _parsed_lights
3. If we don't know a light name, it can't be used by this API
4. If we don't know a dataref, it is a noop
'''
def _get_rgb(prototype,lhs):
    return lhs[prototype.index("R"):prototype.index("B") + 1]

def _set_rgb(prototype,lhs,value):
    lhs[prototype.index("R"):prototype.index("B")+1] = value

def _get_a(prototype,lhs):
    return lhs[prototype.index("A")]

def _set_a(prototype,lhs,value):
    lhs[prototype.index("A")] = value

def _get_xyz(prototype,lhs):
    return lhs[prototype.index("DX"):prototype.index("DZ")+1]

def _set_xyz(prototype,lhs,value):
    lhs[prototype.index("DX"):prototype.index("DZ")+1] = value

def _get_width(prototype,lhs,value):
    return lhs[prototype.index("WIDTH")]

def _set_width(prototype,lhs,value):
    lhs[prototype.index("WIDTH")] = value

def _do_rgba_to_dxyz_w(prototype,data):
    r = data
    _set_xyz(prototype, data, _get_rgb(prototype, data))
    _set_width(prototype, data, r[prototype.index("A")])
    _set_rgb(prototype,data,[1,1,1])
    _set_a(prototype,data,1)

def _do_rgb_to_dxyz_w_calc(prototype,data):
    r = data
    _set_xyz(prototype, r, r[prototype.index("R"):prototype.index("B")])
    dir_vec = Vector((_get_xyz(prototype,r)))
    _set_width(prototype, r, 1 - dir_vec.magnitude)
    _set_xyz(prototype, r, dir_vec.normalized())
    _set_rgb(prototype, r, [1,1,1])

def _do_force_omni(prototype,data):
    r = data
    _set_width(prototype,r,1)

def _do_noop(prototype,data):
    pass

def _get_sw_light_callback(dref):
    drefs = {
        "sim/graphics/animation/lights/airplane_beacon_light_dir":     _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light":        _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light_flash":  _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light_spill":  _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_landing_light":        _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_landing_light_flash":  _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_navigation_light_dir": _do_rgb_to_dxyz_w_calc,
        "sim/graphics/animation/lights/airplane_strobe_light_dir":     _do_rgb_to_dxyz_w_calc,

        "sim/graphics/animation/lights/airport_beacon":                _do_rgba_to_dxyz_w, #As of 11/14/2017, all lights with this are commented out
        "sim/graphics/animation/lights/airport_beacon_flash":          _do_rgba_to_dxyz_w, #As of 11/14/2017, none of this dataref appears in lights.txt

        "sim/graphics/animation/lights/airplane_beacon_light_rotate":  _do_force_omni,
        "sim/graphics/animation/lights/carrier_waveoff":               _do_force_omni,

        "sim/graphics/animation/lights/fresnel_horizontal":            _do_force_omni,
        "sim/graphics/animation/lights/fresnel_vertical":              _do_force_omni,
        "sim/graphics/animation/lights/strobe":                        _do_force_omni,
        "sim/graphics/animation/lights/strobe_sp":                     _do_force_omni,
        "sim/graphics/animation/lights/vasi_papi":                     _do_force_omni,
        "sim/graphics/animation/lights/vasi_papi_tint":                _do_force_omni,
        "sim/graphics/animation/lights/vasi3":                         _do_force_omni,
        "sim/graphics/animation/lights/rabbit":                        _do_force_omni,
        "sim/graphics/animation/lights/rabbit_sp":                     _do_force_omni,
        "sim/graphics/animation/lights/wigwag":                        _do_force_omni,
        "sim/graphics/animation/lights/wigwag_sp":                     _do_force_omni
    }
    try:
        return drefs[dref]
    except:
        return _do_noop

# The parsed lights dictionary, where the key is the light name (str)
# and the value is a ParsedOverload
_parsed_lights = None

class ParsedLightParamDef():
    def __init__(self,light_prototype):
        self.prototype = tuple(light_prototype)
        #To be filled in later during xplane_light's collect method
        self.user_values = [None]*len(self.prototype)

    def set_user_values(self,user_values):
        def isfloat(number_str):
            try:
                val = float(number_str)
            except:
                return False
            else:
                return True
        assert len(user_values) == len(self.user_values)
        self.user_values = [float(v) if isfloat(v) else v for v in user_values]


class ParsedDataSource():
    TYPE_PROTOTYPES = {
# Keys         :   1/2 of value (data provides other half)
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,     13,    14,     15,   16
"BILLBOARD_HW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH","FREQ","PHASE","AMP","DAY"),
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,                                13
"BILLBOARD_SW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF"),
"CONE_HW":      ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF"),
"CONE_SW":      ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF"),
#                                 1,     2,          3,         4
"SPILL_GND":    (                "SIZE","CELL_SIZE","CELL_ROW","CELL_COL"),
"SPILL_GND_REV":(                "SIZE","CELL_SIZE","CELL_ROW","CELL_COL"),
#                  1,  2,  3,  4,  5,                                       6,   7,   8,   9,                           10
"SPILL_HW_DIR": ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                     "DAY"),
#                  1,  2,  3,  4,  5,                                                              6,   7,   8,   9,    10
"SPILL_HW_FLA": ("R","G","B","A","SIZE",                                                         "FREQ","PHASE","AMP","DAY"),
#                  1,  2,  3,  4,  5,                                       6,   7,   8,   9,                                 10
"SPILL_SW":     ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                           "DREF")
}

    def __init__(self,light_type,light_data):
        self.type = light_type
        assert isinstance(light_data,list)
        def isfloat(number_str):
            try:
                val = float(number_str)
            except:
                return False
            else:
                return True

        self.data = [float(d) if isfloat(d) else d for d in light_data]

    def get_prototype(self):
            return self.TYPE_PROTOTYPES[self.type]


class ParsedLightOverload():
    def __init__(self,light_name):
        self.light_name = light_name
        self.light_param_def = None
        self.data_source = None

    #query must be a valid number or one of the column names
    def get(self,query):
        if isinstance(query,Number):
            return self.data_source.data[query]
        elif isinstance(query,str):
            keys = self.data_source.get_prototype()
            values = self.data_source.data
            try:
                value = dict(zip(keys,values))[query]
                return value
            except:
                return None
        else:
            raise TypeError

    def set(self,query,value):
        if isinstance(query,Number):
            self.data_source.data[query] = value
        elif isinstance(query,str):
            keys = self.data_source.get_prototype()
            values = self.data_source.data
            try:
                self.data_source.data[keys.index(query)] = value
            except Exception as e:
                raise e
        else:
            raise TypeError

    def is_param_light(self):
        return self.light_param_def is not None
    
    def apply_sw_light_callback(self):
        _get_sw_light_callback(self.get("DREF"))(self.data_source.get_prototype(),self.data_source.data)

    def bake_user_values(self,user_values=None):
        if self.light_param_def is not None:
            assert user_values is not None
            self.light_param_def.set_user_values(user_values)

            for i,param in enumerate(self.light_param_def.prototype):
                new_value = self.light_param_def.user_values[i]
                actual_param_idx = self.data_source.data.index(param)
                old_value = self.data_source.data[actual_param_idx]
                self.data_source.data[actual_param_idx] = new_value

            if "DREF" in self.data_source.get_prototype():
                self.apply_sw_light_callback()


def get_overload(light_name):
    try:
        return copy.deepcopy(_parsed_lights[light_name])
    except:
        return None

# Function _add_light
#
# light_type_str<str> - A supported light types, such as "BILLBOARD_HW" or "LIGHT_PARAM_DEF
# light_name<str>     - The name of the light, found in lights.txt
# light_data<list>    - The data of the light after the name.
def _add_light(light_type_str:str,light_name:str,light_data:List[str]):
    if light_name not in _parsed_lights:
        _parsed_lights[light_name] = ParsedLightOverload(light_name)

    if light_type_str == "LIGHT_PARAM_DEF":
        #light_data[1:0] skips over the first number in the LIGHT_PARAM_DEF
        _parsed_lights[light_name].light_param_def = ParsedLightParamDef(light_data[1:])
    else:
        rankings = ["CONE_SW", #Least trustworthy
                    "CONE_HW",
                    "SPILL_GND_REV",
                    "SPILL_GND",
                    "BILLBOARD_SW",
                    "BILLBOARD_HW",
                    "SPILL_SW",
                    "SPILL_HW_FLA",
                    "SPILL_HW_DIR"] #Most trustworthy

        if _parsed_lights[light_name].data_source is not None:
            existing_trust = rankings.index(_parsed_lights[light_name].data_source.type)
        else:
            existing_trust = -1
        new_trust = rankings.index(light_type_str)
        if new_trust > existing_trust:
            _parsed_lights[light_name].data_source = ParsedDataSource(light_type_str,light_data)



# Function: parse_lights_file
#
# Parses lights.txt file as needed.
#
# Returns:
#    True when file is parsed, False when there was an error or exception
def parse_lights_file():
    global _parsed_lights
    if _parsed_lights is not None:
        return True

    LIGHTS_FILEPATH = os.path.join(xplane_constants.ADDON_RESOURCES_FOLDER,"lights.txt")
    if not os.path.isfile(LIGHTS_FILEPATH):
        logger.error("lights.txt file was not found in resource folder %s" % (LIGHTS_FILEPATH))
        return False

    try:
        _parsed_lights = collections.OrderedDict()
        filename = open(LIGHTS_FILEPATH,'r')
        lines = filename.read().splitlines()[3:]
        if len(lines) == 0:
            logger.error("lights.txt file is empty")
            raise Exception
        
        for line in lines:
            line = line.strip()

            if not (len(line) == 0   or\
                line.startswith("#") or\
                line.startswith("TEXTURE")     or\
                line.startswith("X_DIVISIONS") or\
                line.startswith("Y_DIVISIONS")):

                light_str_split = line.split()
                light_type = light_str_split[0]
                light_name = light_str_split[1]
                light_data = light_str_split[2:]
                _add_light(light_type,light_name,light_data)
    except:
        _parsed_lights = None
    finally:
        filename.close()

    return True
