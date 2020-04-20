import collections
import copy
import os
import re
from dataclasses import dataclass
from mathutils import Vector
from typing import Dict, List, Optional, Set, Tuple, Union

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger


LIGHT_TYPE_PROTOTYPES = {
    #                 0, 1,  2,  3,  4,     5,          6,         7,         8,   9,   10,  11,     12,    13,     14,   15
    "BILLBOARD_HW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH","FREQ","PHASE","AMP","DAY"),
    #                0,  1,  2,  3,  4      6,          6,         7,         8,   9,   10,  11,                                12
    "BILLBOARD_SW": ("R","G","B","A","SIZE","CELL_SIZE","CELL_ROW","CELL_COL","DX","DY","DZ","WIDTH",                           "DREF"),
    #                                0,     1,          2,         3
    "SPILL_GND":    (                "SIZE","CELL_SIZE","CELL_ROW","CELL_COL"),
    "SPILL_GND_REV":(                "SIZE","CELL_SIZE","CELL_ROW","CELL_COL"),
    #                0,  1,  2,  3,  4,                                       5,   6,   7,   8,                           9
    "SPILL_HW_DIR": ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                     "DAY"),
    #                0,  1,  2,  3,  4,                                                              5,     6,      7,    8
    "SPILL_HW_FLA": ("R","G","B","A","SIZE",                                                         "FREQ","PHASE","AMP","DAY"),
    #                0,  1,  2,  3,  4,                                       5,   6,   7,   8,                                 9
    "SPILL_SW":     ("R","G","B","A","SIZE",                                  "DX","DY","DZ","WIDTH",                           "DREF")
}


@dataclass
class ParsedLightOverload:
    """
    Represents a specific overload for a light, with the added ability to use [ ] indexing instead of messing with overload_arguments
    """
    overload_type:str
    name:str
    arguments:List[Union[float,str]]

    def __post_init__(self)->None:
        def tryfloat(s:str)->Union[float,str]:
            try:
                return float(s)
            except ValueError:
                return s

        self.arguments = list(map(tryfloat,self.arguments))

    def __contains__(self, item:str):
        """For ParsedLightOverloads, 'contains' means 'this overload contain this column'"""
        return item in LIGHT_TYPE_PROTOTYPES[self.overload_type]

    def __getitem__(self, key:Union[int,str])->Union[float,str]:
        """
        Passing in an int will get you the index in the list of arguments,
        passing in a key will get you the contents of that column of the
        prototype
        Raises IndexError index out of range or KeyError if param is not in overload
        """
        global LIGHT_TYPE_PROTOTYPES
        prototype = LIGHT_TYPE_PROTOTYPES[self.overload_type]
        if isinstance(key, int):
            return self.arguments[key]
        elif isinstance(key, str):
            if key.startswith("UNUSED"):
                raise KeyError(f"{key} cannot represent a real index in the argument's list")
            try:
                # HACK! So far every light in the lights.txt file that uses
                # INDEX uses it to replace the A column
                return self.arguments[prototype.index(key if key != "INDEX" else "A")]
            except ValueError as ve:
                raise KeyError(f"{key} not found in overload's {self.overload_type} prototype") from ve

    def __setitem__(self, key:Union[int,str], value:float)->None:
        """Sets a record's argument by column number or column ID from it's prototype"""
        global LIGHT_TYPE_PROTOTYPES
        prototype = LIGHT_TYPE_PROTOTYPES[self.overload_type]
        if isinstance(key, int):
            try:
                self.arguments[key] = value
            except IndexError:
                raise
        elif isinstance(key, str):
            if key.startswith("UNUSED"):
                raise KeyError(f"{key} cannot represent a real index in the argument's list")
            try:
                # HACK! So far every light in the lights.txt file that uses
                # INDEX uses it to replace the A column
                self.arguments[prototype.index(key if key != "INDEX" else "A")] = value
            except ValueError as ve:
                raise KeyError(f"{key} not found in overload's {self.overload_type} prototype") from ve

    def __iter__(self):
        yield from self.arguments

    def apply_sw_callback(self):
        """
        Pre-emptively apply X-Plane's _sw callback for a dataref on a
        fully or partially completed overload's arguments.

        If the overload has no relavent DREF, nothing is mutated.
        """
        def get_rgb(prototype,lhs):
            return lhs[prototype.index("R"):prototype.index("B") + 1]

        def set_rgb(prototype,lhs,value):
            lhs[prototype.index("R"):prototype.index("B")+1] = value

        def get_a(prototype,lhs):
            return lhs[prototype.index("A")]

        def set_a(prototype,lhs,value):
            lhs[prototype.index("A")] = value

        def get_xyz(prototype,lhs):
            return lhs[prototype.index("DX"):prototype.index("DZ")+1]

        def set_xyz(prototype,lhs,value:List[float]):
            lhs[prototype.index("DX"):prototype.index("DZ")+1] = value

        def get_width(prototype,lhs):
            return lhs[prototype.index("WIDTH")]

        def set_width(prototype,lhs,value):
            lhs[prototype.index("WIDTH")] = value

        def do_rgb_to_dxyz_w_calc(overload):
            global LIGHT_TYPE_PROTOTYPES

            prototype = LIGHT_TYPE_PROTOTYPES[overload.overload_type]
            args = self.arguments
            set_xyz(prototype, args, args[prototype.index("R"):prototype.index("B")])
            dir_vec = Vector(get_xyz(prototype,args))
            set_width(prototype, args, 1 - dir_vec.magnitude)
            set_xyz(prototype, args, dir_vec.normalized())
            set_rgb(prototype, args, [1,1,1])

        #def do_rgba_to_dxyz_w(overload):
            #global LIGHT_TYPE_PROTOTYPES

            #prototype = LIGHT_TYPE_PROTOTYPES[overload.overload_type]
            #args = self.arguments
            #set_xyz(prototype,   args, get_rgb(prototype, args))
            #set_width(prototype, args, args[prototype.index("A")])
            #set_rgb(prototype,   args, [1,1,1])
            #set_a(prototype,     args, 1)

        def do_force_omni(overload):
            global LIGHT_TYPE_PROTOTYPES

            prototype = LIGHT_TYPE_PROTOTYPES[overload.overload_type]
            args = self.arguments
            set_width(prototype, args, 1)

        drefs = {
            "sim/graphics/animation/lights/airplane_beacon_light_dir":     do_rgb_to_dxyz_w_calc,
            "sim/graphics/animation/lights/airplane_generic_light":        do_rgb_to_dxyz_w_calc,
            "sim/graphics/animation/lights/airplane_generic_light_flash":  do_rgb_to_dxyz_w_calc,
            "sim/graphics/animation/lights/airplane_navigation_light_dir": do_rgb_to_dxyz_w_calc,

            #"sim/graphics/animation/lights/airport_beacon":                do_rgba_to_dxyz_w, #As of 11/14/2017, all lights with this are commented out
            #"sim/graphics/animation/lights/airport_beacon_flash":          do_rgba_to_dxyz_w, #As of 11/14/2017, none of this dataref appears in lights.txt

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
            drefs[self["DREF"]](self)
        except KeyError:
            print(f"couldn't find {self['DREF']}")
            pass

    def prototype(self)->Tuple[str,...]:
        global LIGHT_TYPE_PROTOTYPES
        return LIGHT_TYPE_PROTOTYPES[self.overload_type]

    #TODO: better argument name needed, check speck
    def replace_argument(self, argument:str, value:float):
        """Replaces paramerter argument with value if possible, else throws ValueError"""
        self.arguments[self.arguments.index(argument)] = value


class ParsedLight:
    """
    A parsed light represents a light and all its overloads
    from lights.txt

    self.overloads is sorted from most to least confident a software_callback should be applied.
    This is not applicable to most lights.

    One can tell a light is a parameterized light by if self.light_param_def is empty
    """
    def __init__(self, name:str)->None:
        self.name = name
        self.overloads:List[ParsedLightOverload] = []
        self.light_param_def:Tuple[str] = tuple()

    def __str__(self)->str:
        return "{self.light_name}: {" ".join(self.light_param_def) if self.light_param_def else ""}, {self.light_overloads[0]}"


_parsed_lights_txt_content = {} # type: Dict[str, ParsedLight]


def get_parsed_light(light_name:str)->ParsedLight:
    """
    Return is a copy from _parsed_lights_txt_content dict.
    Raises KeyError if light not found
    """
    try:
        return copy.deepcopy(_parsed_lights_txt_content[light_name])
    except KeyError as ke:
        raise KeyError(f"{light_name} not found in parsed lights dict") from ke


def parse_lights_file():
    """
    Parse the lights.txt file, building the dictionary of parsed lights.

    If already parsed, does nothing. Raises OSError or ValueError
    if file not found or content invalid,
    logger errors and warnings will have been collected
    """
    global _parsed_lights_txt_content
    if _parsed_lights_txt_content:
        return

    num_logger_problems = len(logger.findErrors()) + len(logger.findWarnings())
    LIGHTS_FILEPATH = os.path.join(xplane_constants.ADDON_RESOURCES_FOLDER,"lights.txt")
    if not os.path.isfile(LIGHTS_FILEPATH):
        logger.error(f"lights.txt file was not found in resource folder {LIGHTS_FILEPATH}")

    with open(LIGHTS_FILEPATH,"r") as f:
        lines = f.read().splitlines()[3:]
        if len(lines) == 0:
            logger.error("lights.txt file is empty")

        for line in filter(
                lambda l: l.startswith(tuple(LIGHT_TYPE_PROTOTYPES.keys()) + ("LIGHT_PARAM_DEF",)),
                map(str.strip,lines)
            ):
            try:
                overload_type, light_name, *light_args = line.split()
            except ValueError: # not enough values to unpack
                logger.error("Line '{line}' could not be parsed to 'RECORD_TYPE <light_name> <params or args list>")
                continue

            if not re.match("[A-Za-z0-9_]+", light_name):
                logger.error("Light name '{light_name}' must be upper/lower case letters, numbers, or underscores only")
            try:
                _parsed_lights_txt_content[light_name]
            except KeyError:
                _parsed_lights_txt_content[light_name] = ParsedLight(light_name)
            finally:
                parsed_light = _parsed_lights_txt_content[light_name]

                if overload_type == "LIGHT_PARAM_DEF":
                    if parsed_light.light_param_def:
                        logger.error(f"{light_name} has more than one LIGHT_PARAM_DEF")
                    light_argc, *light_argv = light_args
                    parsed_light.light_param_def = light_argv # Skip the count
                    if not set(parsed_light.light_param_def) < {*LIGHT_TYPE_PROTOTYPES["BILLBOARD_HW"], "DREF", "INDEX", "UNUSED1"}:
                        logger.error(f"LIGHT_PARAM_DEF for '{light_name}' contains unknown parameters: {parsed_light.light_param_def}")
                elif overload_type not in LIGHT_TYPE_PROTOTYPES:
                    logger.error(f"{overload_type} is not a valid OVERLOAD_TYPE. Update lights.txt or fix manually")
                elif len(light_args) != len(LIGHT_TYPE_PROTOTYPES[overload_type]):
                    logger.error(f"Arguments list for '{overload_type} {light_name} {' '.join(light_args)}' is not the right length ")
                else:
                    #TODO: Errors needed, argument is not a valid parameter or a float we like, no NaN or 2e-15 even thought those technically converts
                    #TODO: Need test that light_params_def will only have real parameters and no arguments
                    #TODO: Test lights overloads always sorted correctly
                    #TODO: Test for duplicates, update spec on duplicates, ask Ben about duplicates for overloads
                    parsed_light.overloads.append(ParsedLightOverload(overload_type=overload_type, name=light_name, arguments=light_args))
                    rankings = ["SPILL_GND_REV", #Least trustworthy
                                "SPILL_GND",
                                "BILLBOARD_SW",
                                "BILLBOARD_HW",
                                "SPILL_SW",
                                "SPILL_HW_FLA",
                                "SPILL_HW_DIR"] #Most trustworthy

                    # Semantically speaking, overloads[0] must ALWAYS be the most trustworthy
                    parsed_light.overloads.sort(key=lambda l: rankings.index(l.overload_type), reverse=True)

    if (len(logger.findErrors()) + len(logger.findWarnings())) - num_logger_problems:
        raise ValueError
