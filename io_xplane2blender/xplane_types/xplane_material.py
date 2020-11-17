from typing import List, Tuple

import bpy

import io_xplane2blender
from io_xplane2blender.xplane_types import xplane_object

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import (
    effective_normal_metalness,
    effective_normal_metalness_draped,
    floatToStr,
    logger,
)
from .xplane_attribute import XPlaneAttribute
from .xplane_attributes import XPlaneAttributes


# Class: XPlaneMaterial
# A Material
class XPlaneMaterial:
    # Property: object
    # XPlaneObject - A <XPlaneObject>

    # Property: texture
    # string - Path to the texture in use for this material, or None if no texture is present.
    # This property is no longer important as textures are defined by layer.

    # Property: uv_name
    # string - Name of the uv layer to be used for texture UVs.

    # Property: name
    # string - Name of the Blender material.

    # Property: attributes
    # dict - Material attributes that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines the <attributes> by reading the original Blender material from the <object>.
    # Also adds custom attributes to <attributes>.
    #
    # Parameters:
    #   xplaneObject - A <XPlaneObject>
    def __init__(self, xplaneObject: xplane_object.XPlaneObject):
        from os import path

        self.xplaneObject = xplaneObject
        self.blenderObject = self.xplaneObject.blenderObject
        self.blenderMaterial = None
        # The options from mat.xplane
        self.options = None
        self.texture = None
        self.textureLit = None
        self.textureNormal = None
        self.textureSpecular = None
        self.uv_name = None
        self.name = None

        # Material
        self.attributes = XPlaneAttributes()

        self.attributes.add(XPlaneAttribute("ATTR_shiny_rat"))
        self.attributes.add(XPlaneAttribute("ATTR_hard"))
        self.attributes.add(XPlaneAttribute("ATTR_hard_deck"))
        self.attributes.add(XPlaneAttribute("ATTR_no_hard"))

        self.attributes.add(XPlaneAttribute("ATTR_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_shadow_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_no_blend"))

        self.attributes.add(XPlaneAttribute("ATTR_shadow"))
        self.attributes.add(XPlaneAttribute("ATTR_no_shadow"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_enable"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_disable"))
        self.attributes.add(XPlaneAttribute("ATTR_solid_camera"))
        self.attributes.add(XPlaneAttribute("ATTR_no_solid_camera"))

        self.attributes.add(XPlaneAttribute("ATTR_light_level", None, 1000))
        self.attributes.add(XPlaneAttribute("ATTR_light_level_reset", True, 1000))
        self.attributes.add(XPlaneAttribute("ATTR_poly_os", None, 1000))
        self.attributes.add(XPlaneAttribute("ATTR_draped", None, 1000))
        self.attributes.add(XPlaneAttribute("ATTR_no_draped", True, 1000))

        self.cockpitAttributes = XPlaneAttributes()
        self.cockpitAttributes.add(XPlaneAttribute("ATTR_cockpit_device", None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute("ATTR_cockpit", None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute("ATTR_cockpit_lit_only", None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute("ATTR_cockpit_region", None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute("ATTR_no_cockpit", True, 2000))

        self.conditions = []

    def collect(self) -> None:
        if (
            self.blenderObject.material_slots
            and self.blenderObject.material_slots[0].material
        ):
            mat = self.blenderObject.material_slots[0].material
            self.name = mat.name
            self.blenderMaterial = mat
            self.options = mat.xplane  # type: xplane_props.XPlaneMaterialSettings

            if mat.xplane.draw:
                self.attributes["ATTR_draw_enable"].setValue(True)

                # add cockpit attributes
                self.collectCockpitAttributes(mat)

                # add light level attritubes
                self.collectLightLevelAttributes(mat)

                # add conditions
                self.collectConditions(mat)

                # polygon offsett attribute
                if mat.xplane.poly_os > 0:
                    self.attributes["ATTR_poly_os"].setValue(mat.xplane.poly_os)

                if mat.xplane.cockpit_feature == COCKPIT_FEATURE_NONE:
                    xplane_version = int(bpy.context.scene.xplane.version)
                    self.attributes["ATTR_draw_enable"].setValue(True)
                    eff_fn = (
                        effective_normal_metalness_draped
                        if mat.xplane.draped
                        else effective_normal_metalness
                    )
                    xp_file = self.xplaneObject.xplaneBone.xplaneFile
                    if not eff_fn(xp_file):
                        self.attributes["ATTR_shiny_rat"].setValue(
                            mat.specular_intensity
                        )

                    # blend
                    if xplane_version >= 1000:
                        xplane_blend_enum = mat.xplane.blend_v1000

                    if xplane_version >= 1000:
                        if xplane_blend_enum == BLEND_OFF:
                            self.attributes["ATTR_no_blend"].setValue(
                                mat.xplane.blendRatio
                            )
                        elif xplane_blend_enum == BLEND_ON:
                            self.attributes["ATTR_blend"].setValue(True)
                        elif xplane_blend_enum == BLEND_SHADOW:
                            self.attributes["ATTR_shadow_blend"].setValue(
                                mat.xplane.blendRatio
                            )
                    elif xplane_version < 1000:
                        if mat.xplane.blend:
                            self.attributes["ATTR_no_blend"].setValue(
                                mat.xplane.blendRatio
                            )
                        else:
                            self.attributes["ATTR_blend"].setValue(True)

                    if xplane_version >= 1010:
                        if mat.xplane.shadow_local:
                            self.attributes["ATTR_shadow"].setValue(True)
                            self.attributes["ATTR_no_shadow"].setValue(False)
                        else:
                            self.attributes["ATTR_shadow"].setValue(False)
                            self.attributes["ATTR_no_shadow"].setValue(True)

                # draped
                if mat.xplane.draped:
                    self.attributes["ATTR_draped"].setValue(True)
                    self.attributes["ATTR_no_draped"].setValue(False)
                else:
                    self.attributes["ATTR_no_draped"].setValue(True)
            else:
                self.attributes["ATTR_draw_disable"].setValue(True)

            # surface type
            if mat.xplane.surfaceType != SURFACE_TYPE_NONE:
                if mat.xplane.deck:
                    self.attributes["ATTR_hard_deck"].setValue(mat.xplane.surfaceType)
                else:
                    self.attributes["ATTR_hard"].setValue(mat.xplane.surfaceType)
            else:
                self.attributes["ATTR_no_hard"].setValue(True)

            # camera collision
            if mat.xplane.solid_camera:
                self.attributes["ATTR_solid_camera"].setValue(True)
                self.attributes["ATTR_no_solid_camera"].setValue(False)
            else:
                self.attributes["ATTR_no_solid_camera"].setValue(True)

            # try to find uv layer
            if len(self.blenderObject.data.uv_layers) > 0:
                self.uv_name = self.blenderObject.data.uv_layers.active.name

            # add custom attributes
            self.collectCustomAttributes(mat)

        else:
            logger.error("%s: No Material found." % self.blenderObject.name)

        self.attributes.order()

    def collectCustomAttributes(self, mat: bpy.types.Material) -> None:
        xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
        commands = xplaneFile.commands

        if mat.xplane.customAttributes:
            for attr in mat.xplane.customAttributes:
                if attr.reset:
                    commands.addReseter(attr.name, attr.reset)
                self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

    def collectCockpitAttributes(self, mat: bpy.types.Material) -> None:
        xplane_version = int(bpy.context.scene.xplane.version)
        if xplane_version >= 1100:
            if mat.xplane.cockpit_feature == COCKPIT_FEATURE_DEVICE:
                self.cockpitAttributes["ATTR_cockpit_device"].setValue(
                    [
                        mat.xplane.device_name,
                        bin(
                            sum(
                                getattr(mat.xplane, f"device_bus_{i}") << i
                                for i in range(6)
                            )
                        )[2:],
                        mat.xplane.device_lighting_channel,
                        mat.xplane.device_auto_adjust,
                    ]
                )
                self.cockpitAttributes["ATTR_no_cockpit"].setValue(None)

        if mat.xplane.cockpit_feature == COCKPIT_FEATURE_PANEL:
            xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
            cockpit_panel_mode = xplaneFile.options.cockpit_panel_mode
            cockpit_region = int(mat.xplane.cockpit_region)

            self.cockpitAttributes["ATTR_no_cockpit"].setValue(None)
            if xplane_version >= 1110:
                if cockpit_panel_mode == PANEL_COCKPIT:
                    self.cockpitAttributes["ATTR_cockpit"].setValue(True)
                elif cockpit_panel_mode == PANEL_COCKPIT_LIT_ONLY:
                    self.cockpitAttributes["ATTR_cockpit_lit_only"].setValue(True)
                elif cockpit_panel_mode == PANEL_COCKPIT_REGION and cockpit_region:
                    self.cockpitAttributes["ATTR_cockpit_region"].setValue(
                        cockpit_region - 1
                    )
            elif xplane_version < 1110:
                # TODO: I believe this is wrong!
                # This prints out ATTR_cockpit then region no matter
                self.cockpitAttributes["ATTR_cockpit"].setValue(True)
                if cockpit_region:
                    self.cockpitAttributes["ATTR_cockpit_region"].setValue(
                        cockpit_region - 1
                    )

    def collectLightLevelAttributes(self, mat: bpy.types.Material) -> None:
        if mat.xplane.lightLevel:
            self.attributes["ATTR_light_level"].setValue(
                (
                    mat.xplane.lightLevel_v1,
                    mat.xplane.lightLevel_v2,
                    mat.xplane.lightLevel_dataref,
                )
            )
            self.attributes["ATTR_light_level_reset"].setValue(False)

    def collectConditions(self, mat: bpy.types.Material) -> None:
        if mat.xplane.conditions:
            self.conditions = mat.xplane.conditions

    def write(self) -> str:
        debug = getDebug()
        o = ""
        indent = self.xplaneObject.xplaneBone.getIndent()

        if debug:
            o += indent + "# MATERIAL: %s\n" % (self.name)

        xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
        commands = xplaneFile.commands

        for attr in self.attributes:
            o += commands.writeAttribute(self.attributes[attr], self.xplaneObject)

        # if the file is a cockpit file write all cockpit attributes
        if xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT or (
            bpy.context.scene.xplane.version >= VERSION_1040
            and xplaneFile.options.export_type == EXPORT_TYPE_AIRCRAFT
        ):
            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(
                    self.cockpitAttributes[attr], self.xplaneObject
                )

        return o

    # Method: isCompatibleTo
    # Checks if a material is compatible to other material based on an export type.
    #
    # Parameters:
    # refMat <XPlaneMaterial> - reference material to compare against
    # exportType <string> - one of "aircraft", "cockpit", "scenery", "instanced_scenery"
    #
    # Returns:
    #   list,list - A list of errors and a list of warnings
    def isCompatibleTo(
        self, refMat: "XPlaneMaterial", exportType: str, autodetectTextures: bool
    ) -> Tuple[List[str], List[str]]:
        import io_xplane2blender

        return io_xplane2blender.xplane_types.xplane_material_utils.compare(
            refMat, self, exportType, autodetectTextures
        )

    def isValid(self, exportType: str) -> Tuple[List[str], List[str]]:
        """
        # Method: isValid
        # Checks if material is valid based on an export type.
        #
        # Parameters:
        # exportType <string> - one of "aircraft", "cockpit", "scenery", "instanced_scenery"
        #
        # Returns:
        #   Tuple[List[str],Liststr]] A tuple of a list of errors and a list of warnings
        #   bool, list - True if Material is valid, else False + a list of errors
        """
        return io_xplane2blender.xplane_types.xplane_material_utils.validate(
            self, exportType
        )
