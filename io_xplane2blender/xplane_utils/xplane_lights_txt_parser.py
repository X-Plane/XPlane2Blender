import collections
import copy
import os
import re
from dataclasses import dataclass
from mathutils import Vector
from typing import Dict, List, Optional, Set, Tuple, Union

from io_xplane2blender import xplane_constants
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger


OVERLOAD_TYPES = {
    "BILLBOARD_HW",
    "BILLBOARD_SW",
    "SPILL_GND",
    "SPILL_GND_REV",
    "SPILL_HW_DIR",
    "SPILL_HW_FLA",
    "SPILL_SW",
}


def get_overload_column_info(overload_type:str)->Dict[str,bool]:
    """
    Returns a Dict[ColumnName, IsParameterizable].
    The keys of this dict are the overload prototype.

    Raises KeyError if overload_type isn't found.
    """
    return {
        "BILLBOARD_HW": {
            "R": True,
            "G": True,
            "B": True,
            "A": False,
            "SIZE": True,
            "CELL_SIZE": False,
            "CELL_ROW": False,
            "CELL_COL": False,
            "DX": True,
            "DY": True,
            "DZ": True,
            "WIDTH": True,
            "FREQ": True,
            "PHASE": True,
            "AMP": False,
            "DAY": False,
            "DREF": False,
        },
        "BILLBOARD_SW": {
            "R": True,
            "G": True,
            "B": True,
            "A": True,
            "SIZE": True,
            "CELL_SIZE": False,
            "CELL_ROW": False,
            "CELL_COL": False,
            "DX": True,
            "DY": True,
            "DZ": True,
            "WIDTH": True,
            "DREF": False,
        },
        "SPILL_GND": {
            "SIZE": True,
            "CELL_SIZE": False,
            "CELL_ROW": False,
            "CELL_COL": False,
        },
        "SPILL_GND_REV": {
            "SIZE": True,
            "CELL_SIZE": False,
            "CELL_ROW": False,
            "CELL_COL": False,
        },
        "SPILL_HW_DIR": {
            "R": True,
            "G": True,
            "B": True,
            "A": True,
            "SIZE": True,
            "DX": True,
            "DY": True,
            "DZ": True,
            "WIDTH": True,
            "DAY": False,
        },
        "SPILL_HW_FLA": {
            "R": True,
            "G": True,
            "B": True,
            "A": True,
            "SIZE": True,
            "FREQ": True,
            "PHASE": True,
            "AMP": False,
            "DAY": False,
        },
        "SPILL_SW": {
            "R": True,
            "G": True,
            "B": True,
            "A": True,
            "SIZE": True,
            "DX": True,
            "DY": True,
            "DZ": True,
            "WIDTH": True,
            "DREF": False,
        },
    }[overload_type]

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

def _set_xyz(prototype,lhs,value:List[float]):
    lhs[prototype.index("DX"):prototype.index("DZ")+1] = value

def _get_width(prototype,lhs):
    return lhs[prototype.index("WIDTH")]

def _set_width(prototype,lhs,value):
    lhs[prototype.index("WIDTH")] = value

def _do_rgb_to_dxyz_w_calc(overload:"ParsedLightOverload"):
    prototype = get_overload_column_info(overload.overload_type).keys()
    args = overload.arguments
    _set_xyz(prototype, args, args[prototype.index("R"):prototype.index("B")])
    dir_vec = Vector(_get_xyz(prototype,args))
    _set_width(prototype, args, 1 - dir_vec.magnitude)
    _set_xyz(prototype, args, dir_vec.normalized())
    _set_rgb(prototype, args, [1,1,1])

def _do_rgba_to_dxyz_w(overload:"ParsedLightOverload"):
    prototype = get_overload_column_info(overload.overload_type).keys()
    args = overload.arguments
    _set_xyz(prototype,   args, _get_rgb(prototype, args))
    _set_width(prototype, args, args[prototype.index("A")])
    _set_rgb(prototype,   args, [1,1,1])
    _set_a(prototype,     args, 1)

def _do_force_omni(overload:"ParsedLightOverload"):
    prototype = get_overload_column_info(overload.overload_type).keys()
    args = overload.arguments
    _set_width(prototype, args, 1)

SW_CALLBACK_DREFS = {
    "sim/graphics/animation/lights/airplane_beacon_light_dir":     _do_rgb_to_dxyz_w_calc,
    "sim/graphics/animation/lights/airplane_generic_light":        _do_rgb_to_dxyz_w_calc,
    "sim/graphics/animation/lights/airplane_generic_light_flash":  _do_rgb_to_dxyz_w_calc,
    "sim/graphics/animation/lights/airplane_navigation_light_dir": _do_rgb_to_dxyz_w_calc,

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


@dataclass
class ParsedLightOverload:
    """
    Represents a specific overload for a light, with the added ability to use [ ] indexing instead of messing with overload_arguments
    """
    overload_type:str
    name:str
    arguments:List[Union[float,str]]

    def __contains__(self, item:str):
        """For ParsedLightOverloads, 'contains' means 'this overload contain this column'"""
        return item in get_overload_column_info(self.overload_type)

    def __getitem__(self, key:Union[int,str])->Union[float,str]:
        """
        Passing in an int will get you the index in the list of arguments,
        passing in a key will get you the contents of that column of the
        prototype
        Raises IndexError index out of range or KeyError if param is not in overload
        """
        prototype = get_overload_column_info(self.overload_type)
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
        prototype = get_overload_column_info(self.overload_type)
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

    def __str__(self)->str:
        return f"{self.overload_type} {self.name} {self.arguments}"

    def __iter__(self):
        yield from self.arguments

    def apply_sw_callback(self):
        """
        Pre-emptively apply X-Plane's _sw callback for a dataref on a
        fully or partially completed overload's arguments.

        If the overload has no relevant DREF, nothing is mutated.
        """

        try:
            SW_CALLBACK_DREFS[self["DREF"]](self)
        except KeyError:
            print(f"couldn't find {self['DREF']}")
            pass

    def prototype(self)->Tuple[str,...]:
        return get_overload_column_info(self.overload_type).keys()

    def replace_parameterization_argument(self, parameterization_argument:str, value:float)->None:
        """Replaces parameter-argument with value if possible, else throws ValueError"""
        assert isinstance(parameterization_argument, str), f"'{parameterization_argument}' is not a string"
        self.arguments[self.arguments.index(parameterization_argument)] = value


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
        return f"{self.name}: {' '.join(self.light_param_def) if self.light_param_def else ''}, {self.overloads[0]}"


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


class LightsTxtFileParsingError(Exception):
    pass

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

    num_logger_problems = len(logger.findErrors())
    LIGHTS_FILEPATH = os.path.join(xplane_constants.ADDON_RESOURCES_FOLDER,"lights.txt")
    if not os.path.isfile(LIGHTS_FILEPATH):
        logger.error(f"lights.txt file was not found in resource folder {LIGHTS_FILEPATH}")
        raise FileNotFoundError

    def is_allowed_param(p:str)->bool:
        return (p in {
            "R",
            "G",
            "B",
            "A",
            "SIZE",
            "DX",
            "DY",
            "DZ",
            "WIDTH",
            "FREQ",
            "PHASE",
            "INDEX",
        }
        or p.startswith(
            ("UNUSED",)#TODO: "NEG_ONE", "ZERO", "ONE")
        ))

    with open(LIGHTS_FILEPATH,"r") as f:
        lines = [(line_num, l.strip())
                for line_num,l in enumerate(f.read().splitlines())
                if l.startswith((*OVERLOAD_TYPES,"LIGHT_PARAM_DEF"))]

        for line_num, line in lines:
            #print(line)
            try:
                overload_type, light_name, *light_args = line.split()
                if not light_args:
                    raise ValueError
            except ValueError: # not enough values to unpack
                logger.error(f"Line '{line}' could not be parsed to '<RECORD_TYPE> <light_name> <params or args list>'")
                continue

            if not re.match("[A-Za-z0-9_]+", light_name):
                logger.error(f"Light name '{light_name}' must be upper/lower case letters, numbers, or underscores only")
                continue

            def get_parsed_light_of_content_dict(light_name:str)->ParsedLight:
                try:
                    _parsed_lights_txt_content[light_name]
                except KeyError:
                    _parsed_lights_txt_content[light_name] = ParsedLight(light_name)
                finally:
                    return _parsed_lights_txt_content[light_name]

            if overload_type == "LIGHT_PARAM_DEF":
                parsed_light = get_parsed_light_of_content_dict(light_name)
                if parsed_light.light_param_def:
                    logger.error(f"{light_name} cannot have more than one LIGHT_PARAM_DEF")
                    continue
                light_argc, *light_argv = light_args
                try:
                    light_argc = int(light_argc)
                except ValueError:
                    logger.error(f"Parameter count must be an int, is '{light_argc}'")
                    continue
                else:
                    if not light_argc or not light_argv or (light_argc != len(light_argv)):
                        logger.error(f"{light_name}'s LIGHT_PARAM_DEF must have a count > 0 and an parameter list of the same length")
                        continue
                    elif len(set(light_argv)) < len(light_argv):
                        logger.error(f"{light_name}'s LIGHT_PARAM_DEF has duplicate parameters in it")
                        continue
                #TODO: Need test that light_params_def will only have real parameters and no arguments
                parsed_light.light_param_def = light_argv # Skip the count
                if parsed_light.light_param_def and any(
                    not is_allowed_param(param) for param in parsed_light.light_param_def
                ):
                    logger.error(f"LIGHT_PARAM_DEF for '{light_name}' contains unknown or invalid parameters: {parsed_light.light_param_def}")
                    continue
            elif overload_type not in OVERLOAD_TYPES:
                logger.error(f"{overload_type} is not a valid OVERLOAD_TYPE. Update lights.txt or fix manually")
                continue
            elif len(light_args) < len(get_overload_column_info(overload_type)):
                logger.error(f"Arguments list for '{overload_type} {light_name} {' '.join(light_args)}' is not long enough")
                continue
            elif len(light_args) > len(get_overload_column_info(overload_type)):
                logger.error(f"Arguments list for '{overload_type} {light_name} {' '.join(light_args)}' is too long")
                continue
            else:
                parsed_light = get_parsed_light_of_content_dict(light_name)
                def validate_arguments()->bool:
                    def validate_parameterization_arg(i, arg)->bool:
                        try:
                            light_param_def = get_parsed_light(light_name).light_param_def
                            if (arg in light_param_def
                                and list(get_overload_column_info(overload_type).values())[i]):
                                return True
                        except KeyError:
                            return False
                        else:
                            if ((arg == "NOOP" or arg.startswith("sim/"))
                                and i == len(light_args) - 1):
                                return True
                            elif re.match("-?\d+(\.\d+)?", arg):
                                return True
                            else:
                                return False

                    prev_logger_errors = len(logger.findErrors())
                    for i, arg in enumerate(light_args):
                        if not validate_parameterization_arg(i, arg):
                            logger.error(
                                    f"Line {line_num}, arg #{i+1}: ('{arg}')"
                                    f" is not a correctly formatted number or is invalid"
                                )
                            continue

                    #print((len(logger.findErrors()) - prev_logger_errors))
                    return not (len(logger.findErrors()) - prev_logger_errors)
                if not validate_arguments():
                    continue

                def tryfloat(s:str)->float:
                    try:
                        return float(s)
                    except ValueError:
                        return s
                parsed_light.overloads.append(ParsedLightOverload(overload_type=overload_type, name=light_name, arguments=list(map(tryfloat,light_args))))
                # This is a heuristic/careful reading of X-Plane's light system
                # of what is most likely to give us
                # the correct direction to autocorrect
                rankings = [
                    "SPILL_HW_DIR", # Most trustworthy
                    "SPILL_HW_FLA",
                    "SPILL_SW",
                    "BILLBOARD_HW",
                    "BILLBOARD_SW", # Least trustworthy
                    "SPILL_GND", # Ignored by autocorrector, ranked last
                    "SPILL_GND_REV", # Ignored by autocorrector, ranked last
                ]

                # Semantically speaking, overloads[0] must ALWAYS be the most trustworthy
                parsed_light.overloads.sort(key=lambda l: rankings.index(l.overload_type))

    for light_name, pl in _parsed_lights_txt_content.items():
        if not pl.overloads:
            logger.error(f"{light_name} had a LIGHT_PARAM_DEF but no valid overloads. {light_name} will be ignored")
            continue

    _parsed_lights_txt_content = {
        light_name: pl
        for light_name, pl in _parsed_lights_txt_content.items()
        if pl.overloads
    }

    if not _parsed_lights_txt_content:
        logger.error("lights.txt had no valid light records in it")
    if len(logger.findErrors()) - num_logger_problems:
        raise LightsTxtFileParsingError
