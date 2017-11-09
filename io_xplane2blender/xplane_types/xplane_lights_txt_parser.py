import copy
import functools
import os
import math
import collections
from collections import OrderedDict
from gc import collect
from numbers import Number

def sort_by_trust(overload_lhs,overload_rhs):
    rankings = [
                "SPILL_HW_DIR",
                "SPILL_HW_FLA",
                "SPILL_SW",
                "BILLBOARD_HW",
                "BILLBOARD_SW",
                "SPILL_GND",
                "SPILL_GND_REV",
                "CONE_HW",
                "CONE_SW"
                ]
    rankings.reverse()
    
    if rankings.index(overload_lhs[0]) > rankings.index(overload_rhs[0]): 
        return 1
    elif rankings.index(overload_lhs[0]) == rankings.index(overload_rhs[0]):
        return 0
    elif rankings.index(overload_lhs[0]) < rankings.index(overload_rhs[0]):
        return -1
    else:
        assert False

#from mathutils import Vector
#BILLBOARD_SW airplane_nav_right_size FOCUS 0 0 1 SIZE 1 6 7 0 0    0 1 sim/graphics/animation/lights/airplane_navigation_light_dir 
#BILLBOARD_SW airplane_nav_right_size 1 1 1 1 SIZE 1 6 7 FOCUS 0    0 1-FOCUS sim/graphics/animation/lights/airplane_navigation_light_dir 

def _get_rgb(type,lhs):
    return lhs[type.index("R"):type.index("B") + 1]

def _set_rgb(type,lhs,value):
    lhs[type.index("R"):type.index("B")+1] = value

def _get_xyz(type,lhs):
    return lhs[type.index("DX"):type.index("DZ")+1]

def _set_xyz(type,lhs,value):    
    lhs[type.index("DX"):type.index("DZ")+1] = value

def _get_width(type,lhs,value):
    return lhs[type.index("WIDTH")]

def _set_width(type,lhs,value):
    lhs[type.index("WIDTH")] = value
    
#dataref transform functions
#
# takes in a tuple of type information to be used to get indicies of the data and the data itself
# returns transformed data as a new list
def do_nav_light(type,data):
    r = data
    _set_xyz(type, r, r[type.index("R"):type.index("B")])
    dir_vec = [float(i) for i in _get_xyz(type,r)]
    mag = math.sqrt(sum([d**2 for d in dir_vec]))
    norm = (dir_vec[0]/mag,dir_vec[1]/mag,dir_vec[2]/mag)

    _set_width(type, r, 1 - mag)
    _set_xyz(type, r, norm)
    _set_rgb(type, r, [1,1,1])
    #return r

drefs = { "sim/graphics/animation/lights/airplane_navigation_light_dir" : do_nav_light }

'''Garuntees:
 1. After cleaning lines, we only have valid data
 2. We know how to manipulate and use all valid data perfectly
 '''

class ParsedLightParamDef():
    def __init__(self,light_prototype):
        self.prototype = tuple(light_prototype)
        #To be filled in later during xplane_light's collect method
        self.user_values = [None]*len(self.prototype)

class ParsedDataSource():
    TYPE_PROTOTYPES = {
        "":(),#TODO: this is just for debugging , get rid of it!
# Keys         :   1/2 of value (data provides other half)
#("LIGHT_PARAM_DEF",(...)
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,     13,    14,     15,   16
"BILLBOARD_HW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH","FREQ","PHASE","AMP","DAY"),
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,                                13
"BILLBOARD_SW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF"),
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
        self.data = light_data

    def get_prototype(self):
            return self.TYPE_PROTOTYPES[self.type]

#TODO: Use the word overload!
class ParsedLightOverload():
    def __init__(self,light_name):
        self.light_name = light_name
        #self.prototype = None prptotype is derived from, not stored
        self.light_param_def = None # kept for doing data_source.data replacements
        
        self.data_source = None

    #query must be a valid number or one of the column names
    def get(self,query):
        if isinstance(query,Number):
            return self.data_source.data[query]
        elif isinstance(query,str):
            keys = self.data_source.get_prototype()
            values = self.data_source.data
            value = dict(zip(keys,values))[query]
            return value
        else:
            raise TypeError

    def set(self,query,value):
        if isinstance(query,Number):
            self.data_source.data[query] = value
        elif isinstance(query,str):
            keys = self.data_source.get_prototype()
            values = self.data_source.data
            collections.OrderedDict(zip(keys,values))[query] = value
        else:
            raise TypeError

    def finalize_data(self):
        if self.light_param_def is not None:
            for i,param in enumerate(self.light_param_def.prototype):
                new_value = self.light_param_def.user_values[i]
                actual_param_idx = self.data_source.data.index(param)
                old_value = self.data_source.data[actual_param_idx]
                print("Replacing final_data['%s'] (%s) with user_value (%s)" % (actual_param_idx,old_value,new_value))
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
                drefs[self.get("DREF")](self.data_source.get_prototype(),self.data_source.data)
                print("Final Data")
                print("%s: %s" % (self.data_source.type,str(self.data_source.data)))
            
# ["Name"] -> ([prototypes],[data sources])
# [prototypes]   = ParsedProtoype
# [data_sources] = ParsedData

'''
# ["Name"] -> Overload
'''
#TODO: Make actual API based on "get_generic_light_overload", make user_values get passed into finalize
parsed_lights = None
#collections.OrderedDict()

#TODO: should combine light_type and light_data into ordered dict so we can stop with the data[type.index("KEY")] pattern
#add a light to the parsed_lights dictionary
#
# light_type_str<str> - A string of one of the supported light types, such as "BILLBOARD_HW" or "LIGHT_PARAM_DEF
# light_name<str>     - The name of the light, found in lights.txt
# light_data<list>    - The data of the light after the name.
def add_light(light_type_str,light_name,light_data):
    if light_name not in parsed_lights:
        parsed_lights[light_name] = ParsedLightOverload(light_name)

    if light_type_str == "LIGHT_PARAM_DEF":
        #import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        #import pydevd;pydevd.settrace()
        parsed_lights[light_name].light_param_def = ParsedLightParamDef(light_data[1:])#light_data[1:0] skips over the first number in param def 
        
    else:
        rankings = ["CONE_SW" #Least trustworthy
                    "CONE_HW",
                    "SPILL_GND_REV",
                    "SPILL_GND",
                    "BILLBOARD_SW",
                    "BILLBOARD_HW",
                    "SPILL_SW",
                    "SPILL_HW_FLA",
                    "SPILL_HW_DIR"] #Most trustworthy

        if parsed_lights[light_name].data_source is not None:
            existing_trust = rankings.index(parsed_lights[light_name].data_source.type)
        else:
            existing_trust = -1 
        new_trust = rankings.index(light_type_str)
        if new_trust > existing_trust:
            parsed_lights[light_name].data_source = ParsedDataSource(light_type_str,light_data)

    overload = parsed_lights[light_name]
    light_param_def = overload.light_param_def
    data_source = overload.data_source
    
    return

    if data_source == None:
        return

    if overload.light_name == "airplane_taxi_sp" or data_source is None:
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        #import pydevd;pydevd.settrace()
        
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
    global parsed_lights
    if parsed_lights is not None:
        return
    else:
        parsed_lights = collections.OrderedDict()#TODO: Not good. What if parsing fails part way through? where best to put this to parse as few times as posible.
        #Must for unit test have in xplanefile level

    LIGHTS_FILEPATH = "./lights.txt"
    __dirname__ = os.path.dirname(__file__)

    with open(os.path.join(__dirname__,LIGHTS_FILEPATH),"r") as f:
        lines = f.read().splitlines()[3:]
        clean_lines = []
        for line in lines:
            line = line.strip()
            #has_whitelist_sw_light = (line.startswith("SPILL_SW") or line.startswith("BILLBOARD_SW"))\
             #                        and\
              #                       ("sim/graphics/animation/lights/airplane_navigation_light_dir" in line)

            if "airplane_nav_" in line and "_size" in line:
                clean_lines.append(line)

            if not (len(line) == 0   or\
                line.startswith("#") or\
                line.startswith("TEXTURE")     or\
                line.startswith("X_DIVISIONS") or\
                line.startswith("Y_DIVISIONS") or\
                line.startswith("BILLBOARD_SW")  or\
                line.startswith("CONE_HW")       or\
                line.startswith("CONE_SW")       or\
                line.startswith("SPILL_GND")     or\
                line.startswith("SPILL_GND_REV")):
                line.startswith("SPILL_SW") or\
                clean_lines.append(line)

        for l in clean_lines:
            light_str_split = l.split()
            light_type = light_str_split[0]
            light_name = light_str_split[1]
            light_data = light_str_split[2:]
            add_light(light_type,light_name,light_data)

    for overload in parsed_lights.values():
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        #import pydevd;pydevd.settrace()
        #overload.finalize_data()

if __name__ == "__main__":
    parse_lights_file()

    for name,value in sorted(parsed_lights.items()):
        print("%s:" % name)
        #kl
        #print("%s:")
        #for prototype,datasource in valuezip(value[0],value[1]):
        #    pass
        #print("%s,%s"%(str(prototype),str(datasource)))
            
            #for p in prototype:
            #    print("\t-%s" % str(p[0]))
            #    print("\t-%s" % str(p[1][0]))
            #jfor d in datasource:
             #   print("\t-%s" % str(d[0]))
             #   print("\t-%s" % str(d[1][0]))
