import functools
import os
import math
import collections
from collections import OrderedDict

def sort_by_trust(overload_lhs,overload_rhs):
    rankings = [
                "LIGHT_PARAM_DEF",
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
    dir_vec = [float(i) for i in _get_xyz(type,r)]
    mag = math.sqrt(sum([d**2 for d in dir_vec]))
    norm = (dir_vec[0]/mag,dir_vec[1]/mag,dir_vec[2]/mag)

    _set_xyz(type, r, r[type.index("R"):type.index("B")])
    _set_width(type, r, 1 - mag)
    _set_xyz(type, r, norm)
    _set_rgb(type, r, [1,1,1])
    return r

drefs = { "sim/graphics/animation/lights/airplane_navigation_light_dir" : do_nav_light }

'''Garuntees:
 1. After cleaning lines, we only have valid data
 2. We know how to manipulate and use all valid data perfectly
 '''

TYPE_PROTOTYPES = (
# Keys         :   1/2 of value (data provides other half)
#("LIGHT_PARAM_DEF",(...)
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,     13,    14,     15,   16
("BILLBOARD_HW", ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH","FREQ","PHASE","AMP","DAY")),
#                  1,  2,  3,  4,  5      6,          7,         8,         9,   10, 11,   12,                                13
("BILLBOARD_SW", ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF")),
#                  1,  2,  3,  4,  5,                                       6,   7,   8,   9,                           10
("SPILL_HW_DIR", ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                     "DAY")),
#                  1,  2,  3,  4,  5,                                                              6,   7,   8,   9,    10
("SPILL_HW_FLA", ("R","G","B","A","SIZE",                                                         "FREQ","PHASE","AMP","DAY")),
#                  1,  2,  3,  4,  5,                                       6,   7,   8,   9,                                 10
("SPILL_SW",     ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                           "DREF"))
)

def get_proto(l_type_str):
    for l_type in TYPE_PROTOTYPES:
        if l_type_str in l_type[0]:
            return l_type

# ["Name"] -> ([prototypes],[data sources])
# [prototypes]   = [("LIGHT_TYPE",TYPE_PROTOTYPES["LIGHT_TYPE" or data of LIGHT_PARAM_DEF)]
# [data_sources] = [("LIGHT_TYPE",parsed data)]

'''
# ["Name"] -> (
                [("LIGHT_TYPE",TYPE_PROTOTYPE["LIGHT_TYPE"]),...],*
                [("LIGHT_TYPE",light_data),...]
            )

When "LIGHT_TYPE" is "LIGHT_PARAM_DEF", TYPE_PROTOTYPE = light_data, and nothing is appended to the data_sources 
value<-<tuple>
value[0]<-prototype<list>
value[0][0]<-prototype's first entry<tuple>
value[0][0][0]<-prototype's first entry's "LIGHT_TYPE"<str>
value[0][0][1]<-prototype's first entry's prototype tuple<tuple<str>>
'''
parsed_lights = collections.OrderedDict()

#TODO: should combine light_type and light_data into ordered dict so we can stop with the data[type.index("KEY")] pattern
#add a light to the parsed_lights dictionary
#
# light_type_str<str> - A string of one of the supported light types, such as "BILLBOARD_HW" or "LIGHT_PARAM_DEF
# light_name<str>     - The name of the light, found in lights.txt
# light_data<list>    - The data of the light after the name.
def add_light(light_type_str,light_name,light_data):
    if light_name not in parsed_lights:
        parsed_lights[light_name] = ([],[])

    if light_type_str == "LIGHT_PARAM_DEF":
        #import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        #import pydevd;pydevd.settrace()
        light_prototype = tuple((light_type_str,light_data[1:]))#light_data[1:0] skips over the first number in param def 
        
    else:#if len([i for i in parsed_lights[light_name][0] if i[0] == "LIGHT_PARAM_DEF"]) == 0: #If there are no LIGHT_PARAM_DEFS in in 
        light_prototype = get_proto(light_type_str)
        parsed_lights[light_name][1].append((light_type_str,light_data))

    parsed_lights[light_name][0].append(light_prototype)
    parsed_lights[light_name][0].sort(key=functools.cmp_to_key(sort_by_trust))
    parsed_lights[light_name][1].sort(key=functools.cmp_to_key(sort_by_trust))


    last_overload = parsed_lights[light_name]
    prototype = last_overload[0][-1]
    try:
        datasource = last_overload[1][-1]
    except:
        datasource = []

    if light_name == "airplane_taxi_sp":
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        import pydevd;pydevd.settrace()
        
    print("Parsed %s:\n"
          "Best prototype (of %d):\n"
          "\t-%s\n"
          "\t-%s\n"
          "Best data source (of %d)\n"
          "\t-%s\n"
          "\t-%s\n"
          % (light_name,
                len(last_overload[0]),
                str(prototype[0]),
                str(prototype[1]),
                len(last_overload[1]),
                str(datasource[0]) if datasource != [] else "None",
                str(datasource[1]) if datasource != [] else "None",
                ))

def parse_lights_file():
    LIGHTS_FILEPATH = "./lights.txt"
    __dirname__ = os.path.dirname(__file__)

    with open(os.path.join(__dirname__,LIGHTS_FILEPATH),"r") as f:
        lines = f.read().splitlines()[3:]
        clean_lines = []
        for line in lines:
            line = line.strip()
            #has_whitelist_sw_light = (line.startswith("SPILL_SW") or line.startswith("BILLBOARD_SW"))\
                                     #and\
                                     #("sim/graphics/animation/lights/airplane_navigation_light_dir" in line)

            #if has_whitelist_sw_light or "airplane_nav_" in line and "_size" in line:
            #    clean_lines.append(line)

            if not (len(line) == 0   or\
                line.startswith("#") or\
                line.startswith("TEXTURE")     or\
                line.startswith("X_DIVISIONS") or\
                line.startswith("Y_DIVISIONS") or\
                #line.startswith("BILLBOARD_SW")  or\
                line.startswith("CONE_HW")       or\
                line.startswith("CONE_SW")       or\
                line.startswith("SPILL_GND")     or\
                line.startswith("SPILL_GND_REV")):
                #line.startswith("SPILL_SW") or\
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
        prototypes,data_sources = overload[:]
        prototypes.sort(key=functools.cmp_to_key(sort_by_trust))
        data_sources.sort(key=functools.cmp_to_key(sort_by_trust))

if __name__ == "__main__":
    parse_lights_file()

    for name,value in sorted(parsed_lights.items()):
        print("%s:" % str(name))
        for prototype,datasource in zip(value[0],value[1]):
            pass
        #print("%s,%s"%(str(prototype),str(datasource)))
            
            #for p in prototype:
            #    print("\t-%s" % str(p[0]))
            #    print("\t-%s" % str(p[1][0]))
            #jfor d in datasource:
             #   print("\t-%s" % str(d[0]))
             #   print("\t-%s" % str(d[1][0]))
