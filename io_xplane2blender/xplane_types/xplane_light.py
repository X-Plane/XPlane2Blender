import math
import re
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain, takewhile, tee, zip_longest
from typing import Dict, List, Optional, Tuple, Union

import bpy
import mathutils
from mathutils import Euler, Matrix, Vector

from io_xplane2blender import xplane_constants, xplane_types, xplane_utils
from io_xplane2blender.xplane_types import xplane_object
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import floatToStr, logger, vec_b_to_x, vec_x_to_b


@dataclass
class _LightSpillCustomParams:
    r: float
    g: float
    b: float

    @property
    def a(self):
        return 1

    size: float
    dx: float
    dy: float
    dz: float
    width: float
    dataref: str

    def __str__(self):
        return " ".join(
            chain(
                map(
                    floatToStr,
                    (
                        self.r,
                        self.g,
                        self.b,
                        self.a,
                        self.size,
                        self.dx,
                        self.dy,
                        self.dz,
                        self.width,
                    ),
                ),
                (self.dataref,),
            )
        )


class XPlaneLight(xplane_object.XPlaneObject):
    def __init__(self, blenderObject: bpy.types.Object):
        super().__init__(blenderObject)
        # Indices for VLIGHTs table
        self.indices = [0, 0]

        # Our light type, not the Blender light type
        self.lightType = blenderObject.data.xplane.type

        # Color, for use by CUSTOM or AUTOMATIC lights
        # change color according to type
        if self.lightType == LIGHT_FLASHING:
            self.color: List[float] = list(blenderObject.data.color)
            self.color[0] = -self.color[0]
        elif self.lightType == LIGHT_PULSING:
            self.color = [9.9] * 3
        elif self.lightType == LIGHT_STROBE:
            self.color = [9.8] * 3
        elif self.lightType == LIGHT_TRAFFIC:
            self.color = [9.7] * 3
        elif blenderObject.data.xplane.enable_rgb_override:
            self.color: List[float] = blenderObject.data.xplane.rgb_override_values[:]
        else:
            self.color: List[float] = list(blenderObject.data.color)

        self.dataref = blenderObject.data.xplane.dataref
        self.energy = blenderObject.data.energy
        # The Size of a Custom Light
        # and the SIZE replacement for an Automatic Light
        self.size = blenderObject.data.xplane.size
        self.uv = blenderObject.data.xplane.uv

        # Our lights.txt light name, not the Blender Object's name
        self.lightName = blenderObject.data.xplane.name.strip()

        # If the lightName is unknown
        #     params_completed and record_completed these will be none
        # Use __getitem__ and __contains__ to ask if there are columns
        # and fields we care about

        # self.params is the eventual content of the
        # LIGHT_PARAM OBJ directive
        if self.lightType == LIGHT_AUTOMATIC:
            self.params = {}
        elif self.lightType == LIGHT_PARAM:
            self.params = blenderObject.data.xplane.params
        elif self.lightType == LIGHT_SPILL_CUSTOM:
            self.params = _LightSpillCustomParams(*([0] * 8), "")
        else:
            self.params = None

        # Possible comment extracted from a param light params text field
        self.comment: Optional[str] = None

        # If applicable, after collection this will be
        # the light's best overload with any parameters replaced
        # and any sw_callbacks, ready for autocorrection
        self.record_completed: Optional[
            xplane_lights_txt_parser.ParsedLightOverload
        ] = None

        self.setWeight(10000)

    def collect(self) -> None:
        super().collect()

        light_data = self.blenderObject.data
        if self.lightType == LIGHT_NON_EXPORTING:
            return
        elif not self.lightName and self.lightType in {
            LIGHT_NAMED,
            LIGHT_PARAM,
            LIGHT_AUTOMATIC,
        }:
            logger.error(
                f"{self.blenderObject.name} is a {self.lightType.title()} light but has no light name"
            )
            return
        try:
            parsed_light = xplane_lights_txt_parser.get_parsed_light(self.lightName)
        except KeyError:
            parsed_light = None

        unknown_light_name_warning = (
            f"\"{self.blenderObject.name}\"'s Light Name '{self.lightName}' is unknown,"
            f" check your spelling or update your lights.txt file"
        )

        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_NAMED        | *          | Yes          | Yes              | Error, "known param used as named light"
        # LIGHT_NAMED        | "POINT"    | Yes          | No               | Apply sw_callback, do not do autocorrect (POINT means OMNI)
        # LIGHT_NAMED        | not "POINT"| Yes          | No               | Apply sw_callback if possible, autocorrect
        # LIGHT_NAMED        | *          | No           | N/A              | Treat as unknown named light, Warning given, NAMED written as is, no SW callbacks applied
        if (
            self.lightType == LIGHT_NAMED
            and parsed_light
            and parsed_light.light_param_def
        ):
            logger.error(
                f"Light name {self.lightName} is a known param light, being used as a name light. Check the light name or light type"
            )
            return
        elif (
            self.lightType == LIGHT_NAMED
            and parsed_light
            and not parsed_light.light_param_def
        ):
            self.record_completed = parsed_light.best_overload()
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()
        elif self.lightType == LIGHT_NAMED and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_PARAM        | "POINT"    | Yes          | Yes              | Parse params, replace self.params_complete
        # LIGHT_PARAM        | not "POINT"| Yes          | Yes              | Parse params, replace self.params_complete, apply sw_callback if possible. Autocorrect with ANIM_
        # LIGHT_PARAM        | *          | Yes          | No               | Error, "known named light used as a param light"
        # LIGHT_PARAM        | *          | No           | N/A              | Warning given, PARAMS written as is, no auto correction_applied
        elif (
            self.lightType == LIGHT_PARAM
            and parsed_light
            and parsed_light.light_param_def
        ):
            # This section is actually validation/apply_sw_callback only, LIGHT_PARAM type inserts
            # xplane.params content directly into the OBJ
            params_formal = parsed_light.light_param_def

            # Parsed params from the params box, stripped and ignoring the commemnt
            # Make the actual parameters, if there are <= than params_formal, its okay
            # if here are more we have a comment.
            # Find nth group of whitespace space after the end the count

            params_actual = []
            params_itr = iter(self.blenderObject.data.xplane.params.lstrip())

            while len(params_actual) < len(params_formal):
                try:
                    n, params_itr = tee(params_itr)
                    next(n)
                except StopIteration:
                    break
                else:
                    actual = "".join(takewhile(lambda c: not c.isspace(), params_itr))
                    if actual:
                        params_actual.append(actual)
            self.comment = "".join(params_itr).lstrip()

            if len(params_actual) < len(params_formal):
                logger.error(
                    f"'{self.blenderObject.name}':Not enough actual parameters ('{' '.join(params_actual)}') to"
                    f" satisfy 'LIGHT_PARAM_DEF {len(params_formal)} {' '.join(params_formal)}'"
                )
                return

            if self.comment and not self.comment.startswith(("//", "#")):
                logger.warn(
                    f"Comment in param light ({self.comment}) does not start with '//' or '#'"
                )

            self.record_completed = parsed_light.best_overload()
            for i, (pformal, pactual) in enumerate(zip(params_formal, params_actual)):
                try:
                    float(pactual)
                except ValueError:  # pactual not a float
                    logger.error(
                        f"Parameter {i} ({pactual}) of {self.blenderObject.name} is not a number"
                    )
                    return
                else:
                    try:
                        self.record_completed.replace_parameterization_argument(
                            pformal, float(pactual)
                        )
                    except ValueError:
                        continue

            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()

            # The only prototypes without DXYZ are SPILL_GND/_REV (of which there are no parameters)
            # and SPILL_HW_FLA overloads, which are in fact omni
            # but none of them are parameterized
            try:
                dir_vec = Vector(
                    map(self.record_completed.__getitem__, ["DX", "DY", "DZ"])
                )
            except KeyError:
                dir_vec = Vector((0, 0, 0))

            try:
                # We use precision keyframe because we don't want to animate unnecissarily
                if (
                    round(dir_vec.magnitude, PRECISION_KEYFRAME) == 0.0
                    and not self.record_completed.is_omni()
                ):
                    logger.error(
                        f"{self.blenderObject.name}'s '{self.lightName}' is directional, but has (0, 0, 0) for direction"
                    )
                    return
            except ValueError:  # is_omni not ready yet
                pass

        elif (
            self.lightType == LIGHT_PARAM
            and parsed_light
            and not parsed_light.light_param_def
        ):
            logger.error(
                f"Light name {self.lightName} is a named light, not a param light."
                f" Check the light type drop down menu"
            )
            return
        # Even if we don't know the PARAM light, we still have to check if we're about to write out no params
        elif self.lightType == LIGHT_PARAM and not parsed_light:
            logger.warn(unknown_light_name_warning)
            if not self.blenderObject.data.xplane.params.split():
                logger.error(f"'{self.blenderObject.name}' has an empty parameters box")
                return
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_CUSTOM       | *          | N/A          | N/A              | Write custom light as is
        elif self.lightType == LIGHT_CUSTOM:
            pass
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Yes          | Yes              | Fill out params, apply any sw_callbacks, and write
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Yes          | No               | Treat as named light, apply any sw_callbacks, write
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| No           | N/A              | Treat as named light, give warning, write as is
        # LIGHT_AUTOMATIC    | Any Others | N/A          | N/A              | Error, "Automatic lights require POINT or SPOT"
        # LIGHT_AUTOMATIC    |"POINT/SPOT"| Incompatible | N/A              | Error, "Light is incompatible", a label in the UI should also mention this
        elif self.lightType == LIGHT_AUTOMATIC and light_data.type not in {
            "POINT",
            "SPOT",
        }:
            logger.error(
                f"Automatic lights must be a Point or Spot light, change {self.blenderObject.name}'s type or change it's X-Plane Light Type"
            )
            return
        elif (
            self.lightType == LIGHT_AUTOMATIC
            and parsed_light
            and not xplane_lights_txt_parser.is_automatic_light_compatible(
                self.lightName
            )
        ):
            logger.error(
                f"Light '{self.lightName}' is not compatible with Automatic Lights."
                f" Pick a different light or use 'Named' or 'Manual Param' instead"
            )
            return
        elif (
            self.lightType == LIGHT_AUTOMATIC
            and parsed_light
            and parsed_light.light_param_def
        ):

            def width_param_new_value() -> float:
                """
                This is not This is not the final WIDTH or the answer to the question
                "is this omni". This is just what we're replacing WIDTH with,
                and other things can change it
                """
                if light_data.type == "POINT":
                    return 1
                elif "BILLBOARD" in parsed_light.best_overload().overload_type:
                    return XPlaneLight.WIDTH_for_billboard(light_data.spot_size)
                elif "SPILL" in parsed_light.best_overload().overload_type:
                    # cos(half the cone angle)
                    return XPlaneLight.WIDTH_for_spill(light_data.spot_size)

            def new_dxyz_vec_x() -> Vector:
                """
                Returns (potentially scaled) light direction
                or (0, 0, 0) for omni lights in X-Plane coords
                """

                if light_data.type == "POINT":
                    return Vector((0, 0, 0))
                elif "BILLBOARD" in parsed_light.best_overload().overload_type:
                    # Works for DIR_MAG as well, but we'll probably never have a case for that
                    scale = 1 - XPlaneLight.WIDTH_for_billboard(light_data.spot_size)
                    dir_vec_b_norm = self.get_light_direction_b()
                    scaled_vec_b = dir_vec_b_norm * scale
                    return vec_b_to_x(scaled_vec_b)
                elif "SPILL" in parsed_light.best_overload().overload_type:
                    return vec_b_to_x(self.get_light_direction_b())

            dxyz_values_x = new_dxyz_vec_x()

            def convert_table(param: str) -> float:
                table = {
                    "R": self.color[0],
                    "G": self.color[1],
                    "B": self.color[2],
                    "A": 1,
                    "INDEX": light_data.xplane.param_index,
                    "SIZE": light_data.xplane.param_size,
                    "DX": dxyz_values_x[0],
                    "DY": dxyz_values_x[1],
                    "DZ": dxyz_values_x[2],
                    "WIDTH": width_param_new_value(),
                    "FREQ": light_data.xplane.param_freq,
                    "PHASE": light_data.xplane.param_phase,
                    "UNUSED": 0,  # We just shove in something here
                    "NEG_ONE": -1,
                    "ZERO": 0,
                    "ONE": 1,
                }

                if light_data.type == "SPOT":
                    table["DIR_MAG"] = XPlaneLight.DIR_MAG_for_billboard(
                        light_data.spot_size
                    )
                elif light_data.type == "POINT":
                    table["DIR_MAG"] = 0
                return table[param]

            self.params = {
                param: convert_table(param.rstrip("_"))
                for param in parsed_light.light_param_def
            }
            self.record_completed = parsed_light.best_overload()
            for p_arg in filter(
                lambda arg: isinstance(arg, str)
                and not arg.startswith(("NOOP", "sim")),
                self.record_completed,
            ):
                self.record_completed.replace_parameterization_argument(
                    p_arg, self.params[p_arg]
                )

            # Leaving DXYZ in a record's arguments is okay
            # - It doesn't affect any sw_callbacks (as of 4/19/2020)
            # - We'll be filling in instead of autocorrecting
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()

            try:
                is_omni = self.record_completed.is_omni()
            except (KeyError, TypeError):  # No WIDTH column or no __round__for str
                is_omni = False

            if is_omni:
                try:
                    self.record_completed.replace_parameterization_argument("DX", 0)
                    self.record_completed.replace_parameterization_argument("DY", 0)
                    self.record_completed.replace_parameterization_argument("DZ", 0)
                    self.params.update({"DX": 0, "DY": 0, "DZ": 0})
                except ValueError:  # No DX, DY, DZ
                    pass

        elif (
            self.lightType == LIGHT_AUTOMATIC
            and parsed_light
            and not parsed_light.light_param_def
        ):
            self.record_completed = parsed_light.best_overload()
            if "DREF" in self.record_completed.prototype():
                self.record_completed.apply_sw_callback()
        elif self.lightType == LIGHT_AUTOMATIC and not parsed_light:
            logger.warn(unknown_light_name_warning)
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_SPILL_CUSTOM |"POINT/SPOT"| N/A          | N/A              | Fillout params, write
        # LIGHT_SPILL_CUSTOM | Any others | N/A          | N/A              | Error
        elif self.lightType == LIGHT_SPILL_CUSTOM and light_data.type not in {
            "POINT",
            "SPOT",
        }:
            logger.error(
                f"Custom Spill lights must be a Point or Spot light, change {self.blenderObject.name}'s type or change it's X-Plane Light Type"
            )
            return
        elif self.lightType == LIGHT_SPILL_CUSTOM and light_data.type in {
            "POINT",
            "SPOT",
        }:
            p = self.params
            p.r, self.params.g, self.params.b = self.color
            p.size = self.size

            def width_param_new_value() -> float:
                if light_data.type == "POINT":
                    return 1
                elif light_data.type == "SPOT":
                    # cos(half the cone angle)
                    return XPlaneLight.WIDTH_for_spill(light_data.spot_size)

            def new_dxyz_vec_x() -> Vector:
                """
                Returns (potentially scaled) light direction
                or (0, 0, 0) for omni lights in X-Plane coords
                """

                if light_data.type == "POINT":
                    return Vector((0, 0, 0))
                elif light_data.type == "SPOT":
                    return vec_b_to_x(self.get_light_direction_b())
                else:
                    assert False, f"What is this light_data.type {light_data.type}"

            p.dx, p.dy, p.dz = new_dxyz_vec_x()
            p.width = width_param_new_value()
            p.dataref = self.dataref
        # X-Plane Light Type | Light Type | parsed_light | light_param_defs | Result
        # -------------------|------------|--------------|------------------|-------
        # LIGHT_{OLD_TYPES}  | *          | N/A          | N/A              | Write
        elif self.lightType in LIGHTS_OLD_TYPES:
            pass
        else:
            assert (
                False
            ), f"{self.blenderObject.name} had some property configuation that was unaccounted for"

        if self.lightType == LIGHT_AUTOMATIC and self.record_completed:
            try:
                is_omni = self.record_completed.is_omni()
            except ValueError:
                is_omni = False

            if is_omni and light_data.type == "SPOT":
                logger.error(
                    f"{self.blenderObject.name}'s '{self.lightName}' light will be omnidirectional in X-Plane. Use a Point light"
                )
                return
            elif not is_omni and light_data.type == "POINT":
                logger.error(
                    f"{self.blenderObject.name}'s '{self.lightName}' light will be directional in X-Plane. Use a Spot light"
                )
                return

    def write(self) -> None:
        debug = getDebug()
        indent = self.xplaneBone.getIndent()
        if self.lightType == LIGHT_NON_EXPORTING:
            return ""
        o = super().write()

        light_data = self.blenderObject.data
        try:
            parsed_light = xplane_lights_txt_parser.get_parsed_light(self.lightName)
        except KeyError:
            parsed_light = None

        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        translation = bakeMatrix.to_translation()
        has_anim = False

        def find_autocorrect_axis_angle(
            dir_vec_p_norm_b: Vector, bake_matrix: Matrix
        ) -> Tuple[Vector, float]:
            """
            Given a vector of where the light will be pointed in X-Plane and our real rotation,
            find the Axis-Angle for how we need to rotate via animation to make the difference
            """

            def clamp(num: float, minimum: float, maximum: float) -> float:
                if num < minimum:
                    return minimum
                elif num > maximum:
                    return maximum
                else:
                    return num

            # Multiple bake matrix by Vector to get the direction of the Blender object

            dir_vec_b_norm = self.get_light_direction_b()

            # P is start rotation, and B is stop. As such, we have our axis of rotation.
            # "We take the X-Plane light and turn it until it matches what the artist wanted"
            axis_angle_vec_b = dir_vec_p_norm_b.cross(dir_vec_b_norm)

            dot_product_p_b = dir_vec_p_norm_b.dot(dir_vec_b_norm)
            if dot_product_p_b < 0:
                axis_angle_theta = math.pi - math.asin(
                    clamp(axis_angle_vec_b.magnitude, -1.0, 1.0)
                )
            else:
                axis_angle_theta = math.asin(
                    clamp(axis_angle_vec_b.magnitude, -1.0, 1.0)
                )
            return axis_angle_vec_b, axis_angle_theta

        def should_autocorrect_preautomatic() -> bool:
            try:
                return (
                    self.lightType
                    in {
                        xplane_constants.LIGHT_NAMED,
                        xplane_constants.LIGHT_PARAM,
                    }
                    and not self.record_completed.is_omni()
                    # Yes, '!= "POINT"' matters for historical reasons
                    and light_data.type != "POINT"
                    and all(
                        param in self.record_completed for param in ["DX", "DY", "DZ"]
                    )
                )
            except (
                ValueError,
                AttributeError,
            ):  # is_omni not ready, self.record_completed is None
                return False

        def should_autocorrect_automatic() -> bool:
            try:
                is_omni = self.record_completed.is_omni()
            except (
                AttributeError,
                ValueError,
            ):  # self.record_completed is None, is_omni not ready
                is_omni = False

            if self.lightType == LIGHT_AUTOMATIC and not is_omni:
                if self.params:
                    # If we will be LIGHT_PARAM but we won't be filling in DXYZ ourselves
                    return all(param not in self.params for param in ["DX", "DY", "DZ"])
                elif self.record_completed:
                    # If we will be LIGHT_NAMED and our overload has DXYZ columns to correct
                    return all(
                        column in self.record_completed for column in ["DX", "DY", "DZ"]
                    )
            else:
                return False

        if should_autocorrect_preautomatic() or should_autocorrect_automatic():
            axis_angle_vec_b, axis_angle_theta = find_autocorrect_axis_angle(
                vec_x_to_b(
                    Vector(
                        self.record_completed[param] for param in ["DX", "DY", "DZ"]
                    ).normalized()
                ),
                bakeMatrix,
            )
            # Vector P(arameters), in Blender Space

            # Ben says: lights always have some kind of offset because the light itself
            # is "at" 0,0,0, so we treat the translation as the light position.
            # But if there is a ROTATION then in the light's bake matrix, the
            # translation is pre-rotation.  but we want to write a single static rotation
            # and then NOT write a translation every time.
            #
            # Inverse to change our animation order (so we really have rot, trans when we
            # originally had trans, rot) and now we can use the translation in the lamp
            # itself.
            if round(axis_angle_theta, PRECISION_KEYFRAME) != 0.0:
                o += f"{indent}ANIM_begin\n"

                if debug:
                    o += f"{indent}# static rotation\n"

                axis_angle_vec3_x = vec_b_to_x(axis_angle_vec_b).normalized()
                tab = "\t"
                anim_rotate_dir = (
                    f"{indent}ANIM_rotate"
                    f"\t{tab.join(map(floatToStr,axis_angle_vec3_x))}"
                    f"\t{floatToStr(math.degrees(axis_angle_theta))}"
                    f"\t{floatToStr(math.degrees(axis_angle_theta))}"
                    f"\n"
                )
                o += anim_rotate_dir

                rot_matrix = mathutils.Matrix.Rotation(
                    axis_angle_theta, 4, axis_angle_vec_b
                )
                translation = rot_matrix.inverted() @ translation
                has_anim = True
        else:
            # Basically, you're here if the light is
            # - unknown
            # - omni
            # - a real lights the user didn't want autocorrected
            #
            # No animation was emited and no change to self.record_completed/params made
            pass

        if isinstance(self.params, dict):
            assert all(
                isinstance(p, (int, float)) for p in self.params.values()
            ), f"One of {self.lightName} parameters did not get replaced in collect or write: {self.params}"
        if self.record_completed:
            assert all(
                isinstance(c, (float, int)) or c.startswith(("NOOP", "sim"))
                for c in self.record_completed
            ), f"record_completed is not complete {self.record_completed}"

        translation_xp_str = " ".join(map(floatToStr, vec_b_to_x(translation)))
        known_named_automatic = (
            self.lightType == LIGHT_AUTOMATIC
            and parsed_light
            and not parsed_light.light_param_def
        )
        unknown_named_automatic = self.lightType == LIGHT_AUTOMATIC and not parsed_light
        if self.lightType == LIGHT_NAMED or (
            known_named_automatic or unknown_named_automatic
        ):
            o += f"{indent}LIGHT_NAMED\t{self.lightName} {translation_xp_str}\n"
        elif self.lightType == LIGHT_PARAM or (
            self.lightType == LIGHT_AUTOMATIC and parsed_light.light_param_def
        ):
            o += (
                f"{indent}LIGHT_PARAM\t{self.lightName}"
                f" {translation_xp_str}"
                f" {' '.join(map(floatToStr,self.params.values())) if self.lightType == LIGHT_AUTOMATIC else self.params}"
                f"\n"
            )
        elif self.lightType == LIGHT_CUSTOM:
            o += (
                f"{indent}LIGHT_CUSTOM\t{translation_xp_str}"
                f" {' '.join(map(floatToStr,self.color))}"
                f" {' '.join(map(floatToStr,[self.energy, self.size]))}"
                f" {' '.join(map(floatToStr,self.uv))}"
                f" {self.dataref}\n"
            )
        elif self.lightType == LIGHT_SPILL_CUSTOM:
            o += f"{indent}LIGHT_SPILL_CUSTOM {translation_xp_str} {self.params}\n"
        # do not render lights with no indices
        elif self.indices[1] > self.indices[0]:
            offset = self.indices[0]
            count = self.indices[1] - self.indices[0]
            o += f"{indent}LIGHTS\t{offset} {count}\n"

        if has_anim:
            o += f"{indent}ANIM_end\n"

        return o

    def get_light_direction_b(self) -> Vector:
        """
        Returns a unit vector the light's direction,
        even if the light is a POINT light.

        Must be called after self.xplaneBone has been assaigned
        """
        bakeMatrix = self.xplaneBone.getBakeMatrixForAttached()
        dir_vec_b_norm = (bakeMatrix.to_3x3() @ Vector((0, 0, -1))).normalized()
        return dir_vec_b_norm

    @staticmethod
    def DIR_MAG_for_billboard(spot_size: float):
        return 1 - XPlaneLight.WIDTH_for_billboard(spot_size)

    @staticmethod
    def WIDTH_for_billboard(spot_size: float):
        assert spot_size != 0, "spot_size is 0, divide by zero error will occur"
        angle_from_center = spot_size / 2
        return math.cos(angle_from_center) / (math.cos(angle_from_center) - 1)

    @staticmethod
    def WIDTH_for_spill(spot_size: float):
        return math.cos(spot_size * 0.5)
