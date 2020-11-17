import os
import sys

import bpy

from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


class TestMaterials(XPlaneTestCase):
    def test_material_attributes(self):
        xplaneFile = self.createXPlaneFileFromPotentialRoot(
            bpy.data.collections["Layer 1"]
        )

        green = xplaneFile._bl_obj_name_to_bone["green"].xplaneObject.material
        red = xplaneFile._bl_obj_name_to_bone["red"].xplaneObject.material
        blue = xplaneFile._bl_obj_name_to_bone["blue"].xplaneObject.material
        emissive = xplaneFile._bl_obj_name_to_bone["emissive"].xplaneObject.material
        cockpit = xplaneFile._bl_obj_name_to_bone["cockpit"].xplaneObject.material
        cockpitPanel = xplaneFile._bl_obj_name_to_bone[
            "cockpit_panel"
        ].xplaneObject.material
        invisible = xplaneFile._bl_obj_name_to_bone["invisible"].xplaneObject.material
        surface = xplaneFile._bl_obj_name_to_bone["surface"].xplaneObject.material
        conditions = xplaneFile._bl_obj_name_to_bone["conditions"].xplaneObject.material
        specular = xplaneFile._bl_obj_name_to_bone["specular"].xplaneObject.material

        defaultAttrs = {
            "ATTR_shiny_rat": 1,
            "ATTR_hard": None,
            "ATTR_hard_deck": None,
            "ATTR_no_hard": True,
            "ATTR_blend": True,
            "ATTR_shadow_blend": None,
            "ATTR_no_blend": None,
            "ATTR_draw_enable": True,
            "ATTR_shadow": True,
            "ATTR_no_shadow": False,
            "ATTR_draw_disable": None,
            "ATTR_solid_camera": None,
            "ATTR_no_solid_camera": True,
            "ATTR_light_level": None,
            "ATTR_light_level_reset": True,
            "ATTR_poly_os": None,
            "ATTR_draped": None,
            "ATTR_no_draped": True,
        }
        defaultCockpitAttrs = {
            "ATTR_cockpit_device": None,
            "ATTR_cockpit": None,
            "ATTR_cockpit_lit_only": None,
            "ATTR_cockpit_region": None,
            "ATTR_no_cockpit": True,
        }

        redAttrs = defaultAttrs.copy()

        greenAttrs = defaultAttrs.copy()

        blueAttrs = defaultAttrs.copy()

        emissiveAttrs = defaultAttrs.copy()

        cockpitAttrs = defaultAttrs.copy()
        cockpitAttrs["ATTR_shiny_rat"] = 1.0
        cockpitAttrs["ATTR_blend"] = True
        cockpitAttrs["ATTR_draw_enable"] = True
        cockpitAttrs["ATTR_solid_camera"] = True
        cockpitAttrs["ATTR_no_solid_camera"] = False
        cockpitAttrs["ATTR_light_level"] = [1.0, 2.0, "light-level-test"]
        cockpitAttrs["ATTR_light_level_reset"] = False
        cockpitCockpitAttrs = defaultCockpitAttrs.copy()
        cockpitCockpitAttrs["ATTR_cockpit"] = None
        cockpitCockpitAttrs["ATTR_no_cockpit"] = True
        cockpitCockpitAttrs["ATTR_cockpit_region"] = None

        cockpitPanelAttrs = defaultAttrs.copy()
        cockpitPanelAttrs["ATTR_shiny_rat"] = None
        cockpitPanelAttrs["ATTR_blend"] = None
        cockpitPanelAttrs["ATTR_draw_enable"] = True
        cockpitPanelAttrs["ATTR_shadow"] = None
        cockpitPanelAttrs["ATTR_no_shadow"] = None
        cockpitPanelAttrs["ATTR_solid_camera"] = True
        cockpitPanelAttrs["ATTR_no_solid_camera"] = False
        cockpitPanelCockpitAttrs = defaultCockpitAttrs.copy()
        cockpitPanelCockpitAttrs["ATTR_cockpit"] = True
        cockpitPanelCockpitAttrs["ATTR_cockpit_lit_only"] = None
        cockpitPanelCockpitAttrs["ATTR_cockpit_region"] = 0
        cockpitPanelCockpitAttrs["ATTR_no_cockpit"] = None

        invisibleAttrs = defaultAttrs.copy()
        invisibleAttrs["ATTR_shiny_rat"] = None
        invisibleAttrs["ATTR_blend"] = None
        invisibleAttrs["ATTR_draw_enable"] = None
        invisibleAttrs["ATTR_draw_disable"] = True
        invisibleAttrs["ATTR_shadow"] = None
        invisibleAttrs["ATTR_no_shadow"] = None

        surfaceAttrs = defaultAttrs.copy()
        surfaceAttrs["ATTR_no_hard"] = None
        surfaceAttrs["ATTR_hard_deck"] = "asphalt"
        surfaceAttrs["ATTR_poly_os"] = 2

        conditionsAttrs = defaultAttrs.copy()
        conditionsAttrs["custom_prop"] = "10"

        specularAttrs = defaultAttrs.copy()
        specularAttrs["ATTR_shiny_rat"] = 0.25

        self.assertAttributesEqualDict(red.attributes, redAttrs)
        self.assertAttributesEqualDict(red.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(blue.attributes, blueAttrs)
        self.assertAttributesEqualDict(blue.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(green.attributes, greenAttrs)
        self.assertAttributesEqualDict(green.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(emissive.attributes, emissiveAttrs)
        self.assertAttributesEqualDict(emissive.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(cockpit.attributes, cockpitAttrs)
        self.assertAttributesEqualDict(cockpit.cockpitAttributes, cockpitCockpitAttrs)

        self.assertAttributesEqualDict(cockpitPanel.attributes, cockpitPanelAttrs)
        self.assertAttributesEqualDict(
            cockpitPanel.cockpitAttributes, cockpitPanelCockpitAttrs
        )

        self.assertAttributesEqualDict(invisible.attributes, invisibleAttrs)
        self.assertAttributesEqualDict(invisible.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(surface.attributes, surfaceAttrs)
        self.assertAttributesEqualDict(surface.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(conditions.attributes, conditionsAttrs)
        self.assertAttributesEqualDict(
            conditions.cockpitAttributes, defaultCockpitAttrs
        )

        self.assertAttributesEqualDict(specular.attributes, specularAttrs)
        self.assertAttributesEqualDict(specular.cockpitAttributes, defaultCockpitAttrs)

    def test_export_materials(self):
        def filterLines(line):
            return isinstance(line[0], str) and line[0].find("ATTR_") == 0

        filename = "test_materials"
        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )


runTestCases([TestMaterials])
