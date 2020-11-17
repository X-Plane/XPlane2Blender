import math

import bpy
import mathutils

from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_helpers import floatToStr, logger
from io_xplane2blender.xplane_types import XPlaneObject


class XPlaneEmpty(XPlaneObject):
    def __init__(self, blenderObject):
        assert blenderObject.type == "EMPTY"
        super().__init__(blenderObject)
        self.magnet_type = ""

    def collect(self) -> None:
        super().collect()
        special_empty_props = self.blenderObject.xplane.special_empty_props
        if special_empty_props.special_type == EMPTY_USAGE_MAGNET:
            magnet_props = special_empty_props.magnet_props
            magnet_props.debug_name = magnet_props.debug_name.strip()
            if self.xplaneBone.xplaneFile.options.export_type != EXPORT_TYPE_COCKPIT:
                logger.error("Magnets can only be used when Export Type is 'Cockpit'")
            if not magnet_props.debug_name:
                logger.error(
                    "Empty '{}' must have a non-blank Debug Name".format(
                        self.blenderObject.name
                    )
                )
            if (
                not magnet_props.magnet_type_is_xpad
                and not magnet_props.magnet_type_is_flashlight
            ):
                logger.error(
                    "Magnet {debug_name} must have 'xpad' and/or 'flashlight'".format(
                        debug_name=magnet_props.debug_name
                    )
                )

            if special_empty_props.magnet_props.magnet_type_is_xpad:
                self.magnet_type = "xpad"
            if special_empty_props.magnet_props.magnet_type_is_flashlight:
                if self.magnet_type:
                    self.magnet_type += "|"
                self.magnet_type += "flashlight"

    def write(self) -> str:
        """
        Writes the combined Blender and XPlane2Blender data,
        raises UnwritableXPlaneType if logger errors found
        """
        debug = xplane_config.getDebug()
        indent = self.xplaneBone.getIndent()
        o = super().write()

        special_empty_props = self.blenderObject.xplane.special_empty_props

        if int(bpy.context.scene.xplane.version) >= 1130 and (
            special_empty_props.special_type == EMPTY_USAGE_EMITTER_PARTICLE
            or special_empty_props.special_type == EMPTY_USAGE_EMITTER_SOUND
        ):
            if not self.xplaneBone.xplaneFile.options.particle_system_file.endswith(
                ".pss"
            ):
                logger.error(
                    "Particle emitter {} is used, despite no .pss file being set".format(
                        self.blenderObject.name
                    )
                )
                return ""
            elif special_empty_props.emitter_props.name.strip() == "":
                logger.error(
                    "Particle name for emitter {} can't be blank".format(
                        self.blenderObject.name
                    )
                )
                return ""

            bake_matrix = self.xplaneBone.getBakeMatrixForAttached()
            em_location = xplane_helpers.vec_b_to_x(bake_matrix.to_translation())
            # yaw,pitch,roll
            theta, psi, phi = tuple(map(math.degrees, bake_matrix.to_euler()[:]))

            o += "{indent}EMITTER {name} {x} {y} {z} {phi} {theta} {psi}".format(
                indent=indent,
                name=special_empty_props.emitter_props.name,
                x=floatToStr(em_location.x),
                y=floatToStr(em_location.y),
                z=floatToStr(em_location.z),
                phi=floatToStr(-phi),  # yaw right
                theta=floatToStr(theta),  # pitch up
                psi=floatToStr(psi),
            )  # roll right

            if (
                special_empty_props.emitter_props.index_enabled
                and special_empty_props.emitter_props.index >= 0
            ):
                o += " {}".format(special_empty_props.emitter_props.index)

            o += "\n"
        elif (
            int(bpy.context.scene.xplane.version) >= 1130
            and special_empty_props.special_type == EMPTY_USAGE_MAGNET
        ):
            bake_matrix = self.xplaneBone.getBakeMatrixForAttached()
            em_location = xplane_helpers.vec_b_to_x(bake_matrix.to_translation())
            # yaw,pitch,roll
            theta, psi, phi = tuple(map(math.degrees, bake_matrix.to_euler()[:]))

            o += "{indent}MAGNET {debug_name} {magnet_type} {x} {y} {z} {phi} {theta} {psi}\n".format(
                indent=indent,
                debug_name=special_empty_props.magnet_props.debug_name,
                magnet_type=self.magnet_type,
                x=floatToStr(em_location.x),
                y=floatToStr(em_location.y),
                z=floatToStr(em_location.z),
                phi=floatToStr(-phi),  # yaw right
                theta=floatToStr(theta),  # pitch up
                psi=floatToStr(psi),
            )  # roll right

        return o
