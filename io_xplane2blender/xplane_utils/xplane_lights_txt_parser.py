"""
The main class for parsing and interpring the contents of lights.txt.

First parse the file, then get ParsedLights via get_parsed_light and the light name.

These tell you information about the name, any parameters, and its overloads.
Use it's best_overload function to get get valuable information about how X-Plane will end up
using this light
"""

"""
--- BIG NOTE --------------------------------------------------------
The rules of the Automatic Lights feature:

X-Plane
-------
1. A light may be Omni or Directional. If you want both, use one of each
2. In general, the "WIDTH" column controls if it is omni or directional
3. A dataref can mess with this and change the behavior
4. The "WIDTH" _column_ may be parameterized by something, probably a "WIDTH" parameter
5. BILLBOARD_SW cone lights use a formula for their WIDTH that requires the angle of the light

Lights.txt
----------
1. Just read the whole spec. Seriously.

XPlane2Blender
--------------
1. A user sees this feature through the lens of Blender Light Types and the UI only
2. We will never let them do something shocking like
    > Let a POINT light (which hides directionality in the 3D View, though it has `rotation`) create a directional light
    > Let a SPOT light (which is _very_ directional in the 3D View) create an omni light
3. The rules are deterministic: if we know the WIDTH column, dataref, (and rarely a specific light name)
    we can tell if the light will become Omni or Directional
4. We only have the contents of lights.txt to worry about. If lights.txt got updated, our code would have to be reviewed
    instead of being forced to build entirely general solutions

When well implemented, these neatly make guarantees like
- "A POINT light will never become directional"
- "A light with a 'WIDTH' of 1 came from a POINT light"
- "No POINT light will receive animation to autocorrect"
- "A SPOT light will always have a WIDTH of < 1"
    > Yes, but remember, for BILLBOARD_SW, parameterized-WIDTH columns
      must be figured out after the bake matrix is calculated
- "No light has it's 3rd best overload be its secretly most important"
    > Yes, but only until someone invents a new light that breaks our code
- "If we need to re-calculate "WIDTH", our light type is a BILLBOARD_SW

There are some ideas that are WRONG! For instance
- "SPOT lights always animate to aim a light"
    > No, sometimes autocorrection isn't necessary or we have DXYZ parameters we can fill in
- "DXYZ parameters or columns imply directionality"
    > Knowing "DXYZ" columns are useless without knowing "WIDTH" and dataref
- "Autocorrection will start from (0, 0, -1)"
    > False, some lights need special autocorrection
- "SPOT lights will always have a WIDTH column of < 1"
    > Slightly pedantic, - some overload_types do not have a WIDTH column
- "Because it is deterministic, we can tell just from the light name and Blender Light type"
    > Again, the dataref and "WIDTH" column can mess with the answer
- "Because the "WIDTH" is < 1, it was a SPOT"
    > Remember, billboards can be directional, despite not having a "cone" of light
- "Because the "WIDTH" column == 1, it is omni"
    > Nope! There are special cases and is_omni takes care of this for you
- "If it is omni, "WIDTH" column == 1"
    > If you're using DIR_MAG, is_omni is True
      when DIR_MAG (secretly "WIDTH") is 0

To deal with these extreme subtleties follow these rules while writing code:

1. Let ParsedLightOverload.is_omni drive the conversation
    - It hands much of the complexity and was developed after months of research.
      Use it consistently to reduce sloppy logic
    - Decide for yourself what a ValueError means. You may need the distinction between "Directional, but only later" and "Directional"
2. Don't talk about "WIDTH", "DXYZ", or any parameters
    Since parameters may be ignored or used in bizarre ways they're far less reliable sources of information
3. Use the ParsedLight.best_overload function instead of direct indexing
    It captures edge cases and is easier to read
4. Talk about the UI as little as possible
    POINT is synonymous with "Omni" only because of a properly implemented spec and we got lucky with how Blender's UI works
5. Again, talk about "WIDTH" columns, datarefs, and edge cases as much as possible
    This is how X-Plane thinks, and fixing special rules will come from XPlane2Blender discovering more about X-Plane, not the other way around

Hopefully this guide will help you avoid nasty edge cases and read the sometimes obtuse sounding logic
"""
import collections
import copy
import os
import re
from dataclasses import dataclass
from typing import Dict, Iterator, List, Mapping, Optional, Set, Tuple, Union

from mathutils import Vector

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


def get_overload_column_info(overload_type: str) -> Dict[str, bool]:
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


def _replace_columns_via_values(
    overload: "ParsedLightOverload", new_values: Mapping[str, float]
):
    for column, value in new_values.items():
        overload[column] = value


def _do_rgb_to_dxyz_w_calc(overload: "ParsedLightOverload") -> None:
    _replace_columns_via_values(
        overload, {"DX": overload["R"], "DY": overload["G"], "DZ": overload["B"]}
    )
    dir_vec = Vector((overload["DX"], overload["DY"], overload["DZ"]))
    overload["WIDTH"] = 1 - dir_vec.magnitude
    dvn = dir_vec.normalized()
    _replace_columns_via_values(overload, {"DX": dvn[0], "DY": dvn[1], "DZ": dvn[2]})
    _replace_columns_via_values(overload, {"R": 1, "G": 1, "B": 1})


def _do_rgb_to_dxyz_dir_mag_calc(overload: "ParsedLightOverload") -> None:
    _replace_columns_via_values(
        overload, {"DX": overload["R"], "DY": overload["G"], "DZ": overload["B"]}
    )
    dir_vec = Vector((overload["DX"], overload["DY"], overload["DZ"]))
    # I don't know what X-Plane does, but this works for our is_omni function.
    # Step through collect with a POINT light to understand this
    # to understand this hack.
    #
    # -Ted, 6/12/2020
    overload["WIDTH"] = round(dir_vec.magnitude, xplane_constants.PRECISION_KEYFRAME)
    dvn = dir_vec.normalized()
    _replace_columns_via_values(overload, {"DX": dvn[0], "DY": dvn[1], "DZ": dvn[2]})
    _replace_columns_via_values(overload, {"R": 1, "G": 1, "B": 1})


def _do_rgba_to_dxyz_w(overload: "ParsedLightOverload") -> None:
    _replace_columns_via_values(
        overload, {"DX": overload["R"], "DY": overload["G"], "DZ": overload["B"]}
    )
    overload["WIDTH"] = overload["A"]
    _replace_columns_via_values(overload, {"R": 1, "G": 1, "B": 1, "A": 1})


def _do_force_WIDTH_1(overload: "ParsedLightOverload") -> None:
    overload["WIDTH"] = 1


# fmt: off
RGB_TO_DXYZ_DIR_MAG_CALC_DREFS = {
    "sim/graphics/animation/lights/airplane_navigation_light_dir": _do_rgb_to_dxyz_dir_mag_calc,
}


RGB_TO_DXYZ_W_CALC_DREFS = {
    "sim/graphics/animation/lights/airplane_beacon_light_dir":     _do_rgb_to_dxyz_w_calc,
    "sim/graphics/animation/lights/airplane_generic_light":        _do_rgb_to_dxyz_w_calc,
    "sim/graphics/animation/lights/airplane_generic_light_flash":  _do_rgb_to_dxyz_w_calc,
}


RGBA_TO_DXYZ_W_DREFS = {
    "sim/graphics/animation/lights/airport_beacon":                _do_rgba_to_dxyz_w, #As of 11/14/2017, all lights with this are commented out
    "sim/graphics/animation/lights/airport_beacon_flash":          _do_rgba_to_dxyz_w, #As of 11/14/2017, none of this dataref appears in lights.txt
}


# WARNING! Most affect lights are unidirectional, despite having a WIDTH of 1!
# Use is_omni for better coverage of these cases!
FORCE_WIDTH_1_DREFS = {
    "sim/graphics/animation/lights/airplane_beacon_light_rotate":  _do_force_WIDTH_1,
    "sim/graphics/animation/lights/carrier_waveoff":               _do_force_WIDTH_1,

    "sim/graphics/animation/lights/fresnel_horizontal":            _do_force_WIDTH_1,
    "sim/graphics/animation/lights/fresnel_vertical":              _do_force_WIDTH_1,
    "sim/graphics/animation/lights/strobe":                        _do_force_WIDTH_1,
    "sim/graphics/animation/lights/strobe_sp":                     _do_force_WIDTH_1,
    "sim/graphics/animation/lights/vasi_papi":                     _do_force_WIDTH_1,
    "sim/graphics/animation/lights/vasi_papi_tint":                _do_force_WIDTH_1,
    "sim/graphics/animation/lights/vasi3":                         _do_force_WIDTH_1,
    "sim/graphics/animation/lights/rabbit":                        _do_force_WIDTH_1,
    "sim/graphics/animation/lights/rabbit_sp":                     _do_force_WIDTH_1,
    "sim/graphics/animation/lights/wigwag":                        _do_force_WIDTH_1,
    "sim/graphics/animation/lights/wigwag_sp":                     _do_force_WIDTH_1
}
# fmt: on


SW_CALLBACK_DREFS = {
    **RGB_TO_DXYZ_DIR_MAG_CALC_DREFS,
    **RGB_TO_DXYZ_W_CALC_DREFS,
    **RGBA_TO_DXYZ_W_DREFS,
    **FORCE_WIDTH_1_DREFS,
}


@dataclass
class ParsedLightOverload:
    """
    Represents a specific overload for a light, with the added ability
    to use [ ] to index into _columns_ instead of messing with it's arguments member.

    DON'T GET CONFUSED! This API is prototype-column based, not param-based.

    For example take

        LIGHT_PARAM_DEF    airplane_landing_size        3    SIZE    WIDTH    INDEX
        BILLBOARD_SW       airplane_landing_size        0    0    WIDTH    INDEX    SIZE    1    0    7    0    0    0    1    sim/graphics/animation/lights/airplane_landing_light

    `my_landing_light["WIDTH"]` asks about the 12th index in my_landing_light.arguments,
    NOT about the contents of the 3rd index where the param "WIDTH" is used.
    """

    overload_type: str
    name: str
    arguments: List[Union[float, str]]

    def __contains__(self, item: str) -> bool:
        """For ParsedLightOverloads, 'contains' means 'this overload contain this column'"""
        return item in get_overload_column_info(self.overload_type)

    def __getitem__(self, key: Union[int, str]) -> Union[float, str]:
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
                raise KeyError(
                    f"{key} cannot represent a real index in the argument's list"
                )
            try:
                if key == "INDEX":
                    key = "A"
                elif key == "DIR_MAG" and self.name in {"airplane_nav_tail_size"}:
                    key = "B"
                elif key == "DIR_MAG" and self.name in {
                    "airplane_nav_left_size",
                    "airplane_nav_right_size",
                }:
                    key = "R"
                return self.arguments[tuple(prototype).index(key)]
            except ValueError as ve:
                raise KeyError(
                    f"{key} not found in \"{self.name}\"'s overload's {self.overload_type} prototype"
                ) from ve

    def __setitem__(self, key: Union[int, str], value: float) -> None:
        """Sets a record's argument by column number or column ID from it's prototype"""
        prototype = get_overload_column_info(self.overload_type)
        if isinstance(key, int):
            try:
                self.arguments[key] = value
            except IndexError:
                raise
        elif isinstance(key, str):
            if key.startswith("UNUSED"):
                raise KeyError(
                    f"{key} cannot represent a real index in the argument's list"
                )
            try:
                if key == "INDEX":
                    key = "A"
                elif key == "DIR_MAG" and self.name in {"airplane_nav_tail_size"}:
                    key = "B"
                elif key == "DIR_MAG" and self.name in {
                    "airplane_nav_left_size",
                    "airplane_nav_right_size",
                }:
                    key = "R"
                self.arguments[tuple(prototype).index(key)] = value
            except ValueError as ve:
                raise KeyError(
                    f"{key} not found in overload's {self.overload_type} prototype"
                ) from ve

    def __str__(self) -> str:
        return f"{self.overload_type} {self.name} {self.arguments}"

    def __iter__(self) -> Iterator[Union[float, str]]:
        yield from self.arguments

    def apply_sw_callback(self) -> None:
        """
        Pre-emptively apply X-Plane's _sw callback for a dataref on a
        fully or partially completed overload's arguments.

        If the overload has no relevant DREF, nothing is mutated.
        """

        try:
            SW_CALLBACK_DREFS[self["DREF"]](self)
        except KeyError:
            # print(f"couldn't find {self['DREF']}")
            pass

    def is_omni(self) -> bool:
        """
        Checks if overload is omni. This method understands
        the complex rules and special cases, as opposed to simply checking
        the 'WIDTH' column

        May raise ValueError if "WIDTH" column is unreplaced
        and no other special case knows what to return.

        Note: Since a SPOT will never be omni, "function not ready"
        will always eventually mean "not omni". The distinction is still useful
        information

        Since an overload's arguments are mutable and may have unreplaced parameters
        the return value for this is not constant
        """

        # --- WARNING ---------------------------------------------------------
        # This method is the result of months of careful study
        # and investigation, along with weeks of talking with
        # Ben and Alex about the nuanced and _HIGHLY_ undocumented
        # behavior of X-Plane's light systems, along with it's oral
        # history, and map of where the bodies are buried.
        #
        # In other words: don't mess with it unless you have a damn
        # good reason to
        # ---------------------------------------------------------------------

        from_do_RGB_TO_DXYZ_W_CALC = {
            "airplane_beacon_size",
            "airplane_generic_core",
            "airplane_generic_flare",
            "airplane_generic_flash",
            "airplane_generic_glow",
            "airplane_generic_size",
        }

        from_do_RGB_TO_DXYZ_DIR_MAG_CALC = {
            "airplane_nav_left_size",
            "airplane_nav_right_size",
            "airplane_nav_tail_size",
        }

        from_force_WIDTH_1_omni = {
            "airplane_beacon_rotate",
            "airplane_beacon",
            "appch_rabbit_o",
            "appch_strobe_o",
            "inset_appch_rabbit_o",
            "inset_appch_rabbit_o_sp",
            "inset_appch_strobe_o",
            "inset_appch_strobe_o_sp",
        }

        from_force_WIDTH_1_unidirectional = {
            "VASI",
            "VASI3",
            "appch_rabbit_u",
            "appch_strobe_u",
            "inset_appch_rabbit_u",
            "inset_appch_rabbit_u_sp",
            "inset_appch_strobe_u",
            "inset_appch_strobe_u_sp",
            "wigwag_y1",
            "wigwag_y2",
            "hold_short_y1",
            "hold_short_y2",
            "pad_SGSI_lo",
            "pad_SGSI_on",
            "pad_SGSI_hi",
            "carrier_datum",
            "carrier_waveoff",
            "carrier_meatball1",
            "carrier_meatball2",
            "carrier_meatball3",
            "carrier_meatball4",
            "carrier_meatball5",
            "frigate_SGSI_lo",
            "frigate_SGSI_on",
            "frigate_SGSI_hi",
        }

        if self.overload_type in {"SPILL_HW_FLA", "SPILL_GND", "SPILL_GND_REV"}:
            return True
        elif self.name in from_force_WIDTH_1_omni:
            return True
        elif (
            self.name in from_do_RGB_TO_DXYZ_W_CALC
            and self.name not in from_do_RGB_TO_DXYZ_DIR_MAG_CALC
        ):
            return False
        elif self.name in from_force_WIDTH_1_unidirectional:
            return False
        else:
            w = self.get("WIDTH")

            if w == "WIDTH":
                raise ValueError(
                    f"{self.name}'s 'WIDTH' column does not contain a float, omni-ness cannot be determined yet"
                )
            elif w is not None:
                if self.name in from_do_RGB_TO_DXYZ_DIR_MAG_CALC:
                    return round(w, xplane_constants.PRECISION_KEYFRAME) == 0
                else:
                    return round(w, xplane_constants.PRECISION_KEYFRAME) == 1
            else:
                # No WIDTH column and we know
                # we're not a special "always omni" case?
                # We're "Always Directional"
                return False

    def get(
        self, key: str, default: Optional[Union[float, str]] = None
    ) -> Optional[float]:
        """ "Return the value for key if key is in the dictionary, else default.
        Uses __getitem__ under the hood"""
        try:
            return self[key]
        except KeyError:
            return default

    def prototype(self) -> Tuple[str, ...]:
        return tuple(get_overload_column_info(self.overload_type))

    def replace_parameterization_argument(
        self, parameterization_argument: str, value: float
    ) -> None:
        """Replaces parameter-argument with value if possible, else throws ValueError"""
        assert isinstance(
            parameterization_argument, str
        ), f"'{parameterization_argument}' is not a string"
        self.arguments[self.arguments.index(parameterization_argument)] = value


class ParsedLight:
    """
    A parsed light represents a light and all its overloads
    from lights.txt

    self.overloads is sorted from most to least confident about what the is supposed to represent
    and which (if any) software_callback should be applied. It is guaranteed.
    This is not applicable to most lights.

    One can tell a light is a parameterized light by if self.light_param_def is empty
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.overloads: List[ParsedLightOverload] = []
        self.light_param_def: Tuple[str] = tuple()

    def __str__(self) -> str:
        return f"{self.name}: {' '.join(self.light_param_def) if self.light_param_def else ''}, {self.overloads[0]}"

    def best_overload(self) -> ParsedLightOverload:
        if self.name == "radio_obs_flash":
            return self.overloads[1]
        else:
            return self.overloads[0]


def is_automatic_light_compatible(light_name: str) -> bool:
    """
    Returns True if light is compatible, false if not. Throws KeyError if not found in parsed_lights_content
    """
    try:
        get_parsed_light(light_name)
    except KeyError:
        raise
    else:
        return not light_name in {
            # Old v9 lights
            "airplane_landing_size",
            "airplane_landing_flash",
            "airplane_taxi_size",
            "airplane_taxi_flash",
            "airplane_generic_size",
            "airplane_generic_flash",
            "airplane_beacon_size",
            "airplane_strobe_size",
            # Typo
            "full_custom_halo_",
            # Weird test lights
            "apt_light_halo_test",
            "test_lamp0",
            "test_lamp1",
            "test_lamp2",
            "test_lamp3",
            "SW_bb",
            "SW_sp",
            "srgb_test0",
            "srgb_test1",
            "srgb_test2",
            "srgb_test3",
        }


_parsed_lights_txt_content = {}  # type: Dict[str, ParsedLight]


def get_parsed_light(light_name: str) -> ParsedLight:
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
    LIGHTS_FILEPATH = os.path.join(
        xplane_constants.ADDON_RESOURCES_FOLDER, "lights.txt"
    )
    if not os.path.isfile(LIGHTS_FILEPATH):
        logger.error(
            f"lights.txt file was not found in resource folder {LIGHTS_FILEPATH}"
        )
        raise FileNotFoundError

    def is_allowed_param(p: str) -> bool:
        return (
            p
            in {
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
                "DIR_MAG",
            }
            or p.startswith(("UNUSED", "NEG_ONE", "ZERO", "ONE"))
        )

    with open(LIGHTS_FILEPATH, "r") as f:
        lines = [
            (line_num, l.strip())
            for line_num, l in enumerate(f.read().splitlines())
            if l.startswith((*OVERLOAD_TYPES, "LIGHT_PARAM_DEF"))
        ]

        for line_num, line in lines:
            # print(line)
            try:
                overload_type, light_name, *light_args = line.split()
                if not light_args:
                    raise ValueError
            except ValueError:  # not enough values to unpack
                logger.error(
                    f"{line_num}: Line could not be parsed to '<RECORD_TYPE> <light_name> <params or args list>'"
                )
                continue

            if not re.match("[A-Za-z0-9_]+", light_name):
                logger.error(
                    f"{line_num}: Light name '{light_name}' must be upper/lower case letters, numbers, or underscores only"
                )
                continue

            def get_parsed_light_of_content_dict(light_name: str) -> ParsedLight:
                try:
                    _parsed_lights_txt_content[light_name]
                except KeyError:
                    _parsed_lights_txt_content[light_name] = ParsedLight(light_name)
                finally:
                    return _parsed_lights_txt_content[light_name]

            if overload_type == "LIGHT_PARAM_DEF":
                parsed_light = get_parsed_light_of_content_dict(light_name)
                if parsed_light.light_param_def:
                    logger.error(
                        f"{line_num}: {light_name} cannot have more than one LIGHT_PARAM_DEF"
                    )
                    continue
                light_argc, *light_argv = light_args
                try:
                    light_argc = int(light_argc)
                except ValueError:
                    logger.error(
                        f"{line_num}: Parameter count for '{light_name}''s LIGHT_PARAM_DEF must be an int, is '{light_argc}'"
                    )
                    continue
                else:
                    if (
                        not light_argc
                        or not light_argv
                        or (light_argc != len(light_argv))
                    ):
                        logger.error(
                            f"{line_num}: '{light_name}''s LIGHT_PARAM_DEF must have a count > 0 and an parameter list of the same length"
                        )
                        continue
                    elif len(set(light_argv)) < len(light_argv):
                        logger.error(
                            f"{line_num}: '{light_name}''s LIGHT_PARAM_DEF has duplicate parameters in it"
                        )
                        continue
                parsed_light.light_param_def = light_argv  # Skip the count
                if parsed_light.light_param_def and any(
                    not is_allowed_param(param)
                    for param in parsed_light.light_param_def
                ):
                    logger.error(
                        f"{line_num}: LIGHT_PARAM_DEF for '{light_name}' contains unknown or invalid parameters: {parsed_light.light_param_def}"
                    )
                    continue
            elif overload_type not in OVERLOAD_TYPES:
                logger.error(
                    f"{line_num}: '{overload_type}' is not a valid OVERLOAD_TYPE."
                )
                continue
            elif len(light_args) < len(get_overload_column_info(overload_type)):
                logger.error(
                    f"{line_num}: Arguments list for '{overload_type} {light_name} {' '.join(light_args)}' is not long enough"
                )
                continue
            elif len(light_args) > len(get_overload_column_info(overload_type)):
                logger.error(
                    f"{line_num}: Arguments list for '{overload_type} {light_name} {' '.join(light_args)}' is too long"
                )
                continue
            else:
                parsed_light = get_parsed_light_of_content_dict(light_name)

                def validate_arguments() -> bool:
                    def validate_parameterization_arg(i, arg) -> bool:
                        try:
                            light_param_def = get_parsed_light(
                                light_name
                            ).light_param_def
                            if (
                                arg in light_param_def
                                and list(
                                    get_overload_column_info(overload_type).values()
                                )[i]
                            ):
                                return True
                        except KeyError:
                            return False
                        else:
                            if (arg == "NOOP" or arg.startswith("sim/")) and i == len(
                                light_args
                            ) - 1:
                                return True
                            elif re.match("-?\d+(\.\d+)?", arg):
                                return True
                            else:
                                return False

                    prev_logger_errors = len(logger.findErrors())
                    for i, arg in enumerate(light_args):
                        if not validate_parameterization_arg(i, arg):
                            logger.error(
                                f"{line_num}, '{light_name}', arg #{i+1}: ('{arg}')"
                                f" is not a correctly formatted number or is invalid"
                            )
                            continue

                    return not (len(logger.findErrors()) - prev_logger_errors)

                if not validate_arguments():
                    continue

                def tryfloat(s: str) -> float:
                    try:
                        return float(s)
                    except ValueError:
                        return s

                parsed_light.overloads.append(
                    ParsedLightOverload(
                        overload_type=overload_type,
                        name=light_name,
                        arguments=list(map(tryfloat, light_args)),
                    )
                )
                # This is a heuristic/careful reading of X-Plane's light system
                # of what is most likely to give us
                # the correct direction to autocorrect
                rankings = [
                    "SPILL_HW_DIR",  # Most trustworthy
                    "SPILL_HW_FLA",
                    "SPILL_SW",
                    "BILLBOARD_HW",
                    "BILLBOARD_SW",  # Least trustworthy
                    "SPILL_GND",  # Ignored by autocorrector, ranked last
                    "SPILL_GND_REV",  # Ignored by autocorrector, ranked last
                ]

                # Semantically speaking, overloads[0] must ALWAYS be the most trustworthy
                parsed_light.overloads.sort(
                    key=lambda l: rankings.index(l.overload_type)
                )

    for light_name, pl in _parsed_lights_txt_content.items():
        if not pl.overloads:
            logger.error(
                f"Ignoring '{light_name}': Found LIGHT_PARAM_DEF but no valid overloads"
            )
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
