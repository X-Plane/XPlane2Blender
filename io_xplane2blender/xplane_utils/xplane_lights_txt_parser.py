import abc
import os
import collections
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger

# In lights.txt, many of these have synonyms or variations, where , but this is basically it
LIGHT_TYPE_PROTOTYPES = {
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



#class LightParamDef(collections.UserDict):
    #"""
    #Allows interaction with the LIGHT_PARAM_DEF by index, "standard name", or synonym.
#
    #For example for
#
    #LIGHT_PARAM_DEF        apron_light_billboard        5     X Y Z W S
                                                         #R    G    B    A  SIZE   CS CR CL DX  DY   DZ   WIDTH FREQ PHASE AMP DAY
    #BILLBOARD_HW        apron_light_billboard            1    1    1    1    S    4 2 0    X    Y    Z    W    0    0    0    1
#
    #light_param_def[3]
    #light_param_def["W"]
    #light_param_def["WIDTH"]
#
    #all return the same value. When first read, it is only the list of keys. Later, during collect, it can be combined with user input or automatically collected data
    #"""
    #def __init__(self, light_name:str, original_params:List[str])->None:
        #"""
        #light_name is used for hints as to what the original_params translates to for it's overloads
        #"""
        #SCRATCH ALL THIS, USER PROVIDED VALUES SHUOLDNT BE IN THIS API READING CLASS
        #This class, the ability to use an index or an automaticly translating thing
        #needs to be in xplane_lights.py
#
        #self._data = dict.fromkeys(original_params)
        #self.synonms:Dict[str, str] = {}
        #for param in original_params:
            #x = {
                #"W":"WIDTH",
                #"S":"SIZE",
            #}
#
            #self.synonms[param] = x[param]
#
    #def __getitem__(self, item:Union[int, str])->float:
        #if isinstance(item, int):
            #return self._data[list(self._data.keys())[item]]
        #elif item in self.synonms:
            #return self._data[self.synonms[item]]
        #else:
            #return self._data[item]
#
    #def __setitem__(self, key:str, value:float)->None:
        #if isinstance(key, int):
            #self._data[list(self._data.keys())[key]] = value
        #if key in self.synonms:
            #self._data[self.synonms[key]] = value
        #else:
            #self._data[key] = value
#
    #def __str__(self)->str:
        #return f"LIGHT_PARAM_DEF    {len(self._data)} {self._data.keys()}"
    #"""

@dataclass(frozen=True)
class ParsedLightOverload:
    # What partially or completely filled out type this is
    overload_type:str
    # Always contains stripped strings, even what we know as floats
    overload_arguments:Tuple[str]

class ParsedLight:
    """
    A parsed light represents a light and all its overloads
    from lights.txt

    self.overloads is sorted based on trust worthyness, light_overloads is most trust worthy
    If that light is also a param light, the params are provided
    If light_param_def is empty it indicates it is not a param light
    if not, light_param_defparams
    """
    def __init__(self, name:str)->None:
        self.name = name
        self.overloads:List[ParsedLightOverload] = []
        self.light_param_def:Tuple[str] = tuple()

    def __str__(self)->str:
        return "{self.light_name}: {" ".join(self.light_param_def) if self.light_param_def else ""}, {self.light_overloads[0]}"

_parsed_lights_txt_content:Dict[str, ParsedLight] = {}

def get_parsed_light(light_name:str)->ParsedLight:
    """
    Gets a parsed light from the _parsed_lights_txt_content dictionary
    """
    return _parsed_lights_txt_content[light_name]

def parse_lights_file():
    """
    Parse the lights.txt file, building the dictionary of parsed lights.

    If already parsed, does nothing. Raises OSError or ValueError
    if file not found or content invalid
    """
    global _parsed_lights_txt_content
    if _parsed_lights_txt_content:
        return

    LIGHTS_FILEPATH = os.path.join(xplane_constants.ADDON_RESOURCES_FOLDER,"lights.txt")
    if not os.path.isfile(LIGHTS_FILEPATH):
        logger.error(f"lights.txt file was not found in resource folder %s" % (LIGHTS_FILEPATH))
        raise ValueError

    with open(LIGHTS_FILEPATH,"r") as f:
        lines = f.read().splitlines()[3:]
        if len(lines) == 0:
            logger.error("lights.txt file is empty")
            raise ValueError

        for line in filter(
                lambda l: l.startswith(tuple(LIGHT_TYPE_PROTOTYPES.keys()) + ("LIGHT_PARAM_DEF",)),
                map(str.strip,lines)
            ):
            overload_type, light_name, light_argc, *light_argv = line.split()
            light_argv = tuple(light_argv)
            try:
                _parsed_lights_txt_content[light_name]
            except KeyError:
                _parsed_lights_txt_content[light_name] = ParsedLight(light_name)
            finally:
                parsed_light = _parsed_lights_txt_content[light_name]

                if overload_type == "LIGHT_PARAM_DEF":
                    if parsed_light.light_param_def:
                        logger.error(f"{light_name} has more than one LIGHT_PARAM_DEF")
                        raise ValueError
                    parsed_light.light_param_def = light_argv # Skip the count
                else:
                    parsed_light.overloads.append(ParsedLightOverload(overload_type=overload_type, overload_arguments=light_argv))
                    rankings = ["CONE_SW", #Least trustworthy
                                "CONE_HW",
                                "SPILL_GND_REV",
                                "SPILL_GND",
                                "BILLBOARD_SW",
                                "BILLBOARD_HW",
                                "SPILL_SW",
                                "SPILL_HW_FLA",
                                "SPILL_HW_DIR"] #Most trustworthy

                    # Semantically speaking, overloads[0] must ALWAYS be the most trustworthy
                    parsed_light.overloads.sort(key=lambda l: rankings.index(l.overload_type))
