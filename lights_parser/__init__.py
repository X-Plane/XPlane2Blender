import os
from collections import OrderedDict
import functools

LIGHTS_FILEPATH = "./lights.txt"

def sort_by_trust(overload_lhs,overload_rhs):
    rankings = ["SPILL_HW_DIR",
                "SPILL_HW_FLA",
                "SPILL_SW",
                "BILLBOARD_HW",
                "BILLBOARD_SW",
                "SPILL_GND",
                "SPILL_GND_REV",
                "CONE_HW",
                "CONE_SW"]
    
    if rankings.index(overload_lhs[0]) > rankings.index(overload_rhs[0]): 
        return 1
    elif rankings.index(overload_lhs[0]) == rankings.index(overload_rhs[0]):
        return 0
    elif rankings.index(overload_lhs[0]) < rankings.index(overload_rhs[0]):
        return -1
    else:
        assert False

L_TYPE_BILLBOARD_HW = ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH","FREQ","PHASE","AMP","DAY")
L_TYPE_SPILL_HW_DIR = ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                     "DAY")
L_TYPE_SPILL_HW_FLA = ("R","G","B","A","SIZE",                                                         "FREQ","PHASE","AMP","DAY")

# ["Name"] -> (LIGHT_PARAM_DEF or LIGHT_TYPE, overload sorted by trust worthiness)
# Where overload is a tuple of ("LIGHT_TYPE", (values tuple)), the most thrustworthy of all of the overloads
parsed_lights = {}
def add_light(light_type,light_name,light_data):
    if "BILLBOARD_HW" in light_type and light_name not in parsed_lights:
            parsed_lights[light_name] = (L_TYPE_BILLBOARD_HW,[])
    elif "SPILL_HW_DIR" in light_type and light_name not in parsed_lights:
            parsed_lights[light_name] = (L_TYPE_SPILL_HW_DIR,[])
    elif "SPILL_HW_FLA" in light_type and light_name not in parsed_lights:
            parsed_lights[light_name] = (L_TYPE_SPILL_HW_FLA,[])
    elif "LIGHT_PARAM_DEF" and light_name not in parsed_lights:
        parsed_lights[light_name] = (tuple(light_str_split[3:]),[])
        return

    parsed_lights[light_name][1].append((light_type,tuple(light_data)))
    print("Parsed: %s,%s" % (parsed_lights[light_name][0],parsed_lights[light_name][1]))

if __name__ == "__main__":
    with open(LIGHTS_FILEPATH,"r") as f:
        lines = f.read().splitlines()[3:]
        clean_lines = []
        for line in lines:
            line = line.strip()
            if not (line.startswith("#") or\
                line.startswith("BILLBOARD_SW")  or\
                line.startswith("CONE_HW")       or\
                line.startswith("CONE_SW")       or\
                line.startswith("SPILL_GND")     or\
                line.startswith("SPILL_GND_REV") or\
                line.startswith("SPILL_SW") or\
                len(line) == 0              or\
                line.startswith("TEXTURE")     or\
                line.startswith("X_DIVISIONS") or\
                line.startswith("Y_DIVISIONS")):
                clean_lines.append(line)

        for l in clean_lines:
            light_str_split = l.split()
            light_type = light_str_split[0]
            light_name = light_str_split[1]
            light_data = light_str_split[2:]
            add_light(light_type,light_name,light_data)
            parsed_lights[light_name][1].sort(key=functools.cmp_to_key(sort_by_trust))
            
for key,value in sorted(parsed_lights.items()):
    if len(value[1]) >= 2:
        print("%s:%s"%(key,value[0]))
        for overload in value[1]:
            print("\t:%s" % str(overload))
