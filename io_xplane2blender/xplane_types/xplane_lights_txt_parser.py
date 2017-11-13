import copy
import functools
import os
import math
import collections
from collections import OrderedDict
from gc import collect
from numbers import Number
from mathutils import Vector
from io_xplane2blender import xplane_helpers

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

def do_rgba_to_dxyz_w(prototype,data):
    r = data
    _set_xyz(prototype, data, _get_rgb(prototype, data))
    _set_width(prototype, data, r[prototype.index("A")])
    _set_rgb(prototype,data,[1,1,1])
    _set_a(prototype,data,1)

#dataref transform functions
#
# takes in a tuple of prototype information to be used to get indicies of the data and the data itself
# returns transformed data as a new list
def do_rgb_to_xyz_w_calc(prototype,data):
    r = data
    _set_xyz(prototype, r, r[prototype.index("R"):prototype.index("B")])
    dir_vec = Vector((_get_xyz(prototype,r)))
    _set_width(prototype, r, 1 - dir_vec.magnitude)
    _set_xyz(prototype, r, dir_vec.normalized())
    _set_rgb(prototype, r, [1,1,1])
    #return r

def do_force_omni(prototype,data):
    r = data
    _set_width(prototype,r,1)

def do_noop(prototype,data):
    pass

def get_sw_light_callback(dref):
    drefs = {
        "sim/graphics/animation/lights/airplane_beacon_light_dir":     do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light":        do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light_flash":  do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_generic_light_spill":  do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_landing_light":        do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_landing_light_flash":  do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_navigation_light_dir": do_rgb_to_xyz_w_calc,
        "sim/graphics/animation/lights/airplane_strobe_light_dir":     do_rgb_to_xyz_w_calc,

        "sim/graphics/animation/lights/airport_beacon":                do_rgba_to_dxyz_w,
        "sim/graphics/animation/lights/airport_beacon_flash":          do_rgba_to_dxyz_w,

        "sim/graphics/animation/lights/airplane_beacon_light_rotate":  do_force_omni,
        "sim/graphics/animation/lights/carrier_waveoff":               do_force_omni,

        "sim/graphics/animation/lights/fresnel_horizontal":            do_force_omni,
        "sim/graphics/animation/lights/fresnel_vertical":              do_force_omni,
        "sim/graphics/animation/lights/strobe":                        do_force_omni,
        "sim/graphics/animation/lights/strobe_sp":                     do_force_omni,
        "sim/graphics/animation/lights/vasi_papi":                     do_force_omni,
        "sim/graphics/animation/lights/vasi_papi_tint":                do_force_omni,
        "sim/graphics/animation/lights/vasi3":                         do_force_omni,
        "sim/graphics/animation/lights/rabbit":                        do_force_omni,
        "sim/graphics/animation/lights/rabbit_sp":                     do_force_omni,
        "sim/graphics/animation/lights/wigwag":                        do_force_omni,
        "sim/graphics/animation/lights/wigwag_sp":                     do_force_omni
    }
    try:
        return drefs[dref]
    except Exception as e:
        return do_noop

'''Garuntees:
 1. After cleaning lines, we only have valid data
 2. We know how to manipulate and use all valid data perfectly
 3. If we don't know a light name, it can't be used by this API
 4. If we dn't know a dataref, it is a noop? #TODO?
 '''
# ["Name"] -> Overload
# ["Name"] -> ([prototypes],[data sources])
# [prototypes]   = ParsedProtoype
# [data_sources] = ParsedData
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

    def bake_user_values(self,user_values=None):
        if self.light_param_def is not None:
            assert user_values is not None
            self.light_param_def.set_user_values(user_values)

            for i,param in enumerate(self.light_param_def.prototype):
                new_value = self.light_param_def.user_values[i]
                actual_param_idx = self.data_source.data.index(param)
                old_value = self.data_source.data[actual_param_idx]
                print("Replacing final_data['%s'] (%s) with user_value (%s,type:%s)" % (actual_param_idx,old_value,new_value,type(new_value)))
                print("LIGHT_PARAM_DEF: %s" % str(self.light_param_def.prototype))
                print("USER_VALUES: %s" % str(self.light_param_def.user_values))
                print("Original Data")
                print("%s: %s" % (self.data_source.type,str(self.data_source.data)))
                self.data_source.data[actual_param_idx] = new_value
                print("Final Data")
                print("%s: %s" % (self.data_source.type,str(self.data_source.data)))
                print("----------")

            if "DREF" in self.data_source.get_prototype():
                print("DREF: %s" % self.get("DREF"))
                print("Original Data")
                print("%s: %s" % (self.data_source.type,str(self.data_source.data)))
                get_sw_light_callback(self.get("DREF"))(self.data_source.get_prototype(),self.data_source.data)
                print("Final Data")
                print("%s: %s" % (self.data_source.type,str(self.data_source.data)))
    

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
def _add_light(light_type_str,light_name,light_data):
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

    overload = _parsed_lights[light_name]
    light_param_def = overload.light_param_def
    data_source     = overload.data_source
    #return

    if data_source == None:
        return

    print("Parsed %s:\n"
          "Light Param Def:\n"
          "\t-%s\n"
          "Best Prototype:\n"
          "\t-%s\n"
          "\t-%s\n"
          "Data Source:\n"
          "\t-%s\n"
          % (overload.light_name,
                str(light_param_def.prototype) if light_param_def is not None else "None",
                str(data_source.type),
                str(data_source.get_prototype()),
                str(data_source.data)
                ))

def parse_lights_file():
    global _parsed_lights
    if _parsed_lights is not None:
        return None
    else:
        _parsed_lights = collections.OrderedDict()#TODO: Not good. What if parsing fails part way through? where best to put this to parse as few times as posible.
        #Must for unit test have in xplanefile level

    LIGHTS_FILEPATH = os.path.join(xplane_helpers.getResourcesFolder(),"lights.txt")
    if not os.path.isfile(LIGHTS_FILEPATH):
        raise Exception("Lights file not found!")

    with open(LIGHTS_FILEPATH,'r') as f:
        lines = f.read().splitlines()[3:]
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

if __name__ == "__main__":
    parse_lights_file()

    for name,value in sorted(_parsed_lights.items()):
        print("%s:" % name)