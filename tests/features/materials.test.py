import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestMaterials(XPlaneTestCase):
    def test_material_attributes(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        green = xplaneFile.objects['green'].material
        red = xplaneFile.objects['red'].material
        blue = xplaneFile.objects['blue'].material
        emissive = xplaneFile.objects['emissive'].material
        cockpit = xplaneFile.objects['cockpit'].material
        invisible = xplaneFile.objects['invisible'].material
        surface = xplaneFile.objects['surface'].material
        conditions = xplaneFile.objects['conditions'].material

        defaultAttrs = {
            'ATTR_diffuse_rgb': [0.5, 0.5, 0.5],
            'ATTR_shade_smooth': True,
            'ATTR_shade_flat': None,
            'ATTR_emission_rgb': [0, 0, 0],
            'ATTR_shiny_rat': 1,
            'ATTR_hard': None,
            'ATTR_hard_deck': None,
            'ATTR_no_hard': True,
            'ATTR_cull': True,
            'ATTR_no_cull': None,
            'ATTR_depth': True,
            'ATTR_no_depth': None,
            'ATTR_blend': True,
            'ATTR_shadow_blend': None,
            'ATTR_no_blend': None,
            'ATTR_draw_enable': True,
            'ATTR_draw_disable': None,
            'ATTR_solid_camera': None,
            'ATTR_no_solid_camera': True,
            'ATTR_light_level': None,
            'ATTR_poly_os': None
        }
        defaultCockpitAttrs = {
            'ATTR_cockpit': None,
            'ATTR_no_cockpit': True,
            'ATTR_cockpit_region': None
        }

        redAttrs = defaultAttrs.copy()
        redAttrs['ATTR_diffuse_rgb'] = [1.0, 0.0, 0.0]

        greenAttrs = defaultAttrs.copy()
        greenAttrs['ATTR_diffuse_rgb'] = [0, 1, 0]

        blueAttrs = defaultAttrs.copy()
        blueAttrs['ATTR_diffuse_rgb'] = [0, 0, 1]

        emissiveAttrs = defaultAttrs.copy()
        emissiveAttrs['ATTR_diffuse_rgb'] = [0.5, 0.5, 0.5]
        emissiveAttrs['ATTR_emission_rgb'] = [0.5, 0.5, 0.5]

        cockpitAttrs = defaultAttrs.copy()
        cockpitAttrs['ATTR_diffuse_rgb'] = None
        cockpitAttrs['ATTR_emission_rgb'] = None
        cockpitAttrs['ATTR_shiny_rat'] = None
        cockpitAttrs['ATTR_blend'] = None
        cockpitAttrs['ATTR_draw_enable'] = None
        cockpitAttrs['ATTR_solid_camera'] = True
        cockpitAttrs['ATTR_no_solid_camera'] = None
        cockpitAttrs['ATTR_light_level'] = [1.0, 2.0, 'light-level-test']
        cockpitCockpitAttrs = defaultCockpitAttrs.copy()
        cockpitCockpitAttrs['ATTR_cockpit'] = True
        cockpitCockpitAttrs['ATTR_no_cockpit'] = None
        cockpitCockpitAttrs['ATTR_cockpit_region'] = 0

        invisibleAttrs = defaultAttrs.copy()
        invisibleAttrs['ATTR_diffuse_rgb'] = None
        invisibleAttrs['ATTR_emission_rgb'] = None
        invisibleAttrs['ATTR_shiny_rat'] = None
        invisibleAttrs['ATTR_blend'] = None
        invisibleAttrs['ATTR_draw_enable'] = None
        invisibleAttrs['ATTR_draw_disable'] = True

        surfaceAttrs = defaultAttrs.copy()
        surfaceAttrs['ATTR_no_hard'] = None
        surfaceAttrs['ATTR_hard_deck'] = 'asphalt'
        surfaceAttrs['ATTR_poly_os'] = 2

        conditionsAttrs = defaultAttrs.copy()
        conditionsAttrs['custom_prop'] = '10'

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

        self.assertAttributesEqualDict(invisible.attributes, invisibleAttrs)
        self.assertAttributesEqualDict(invisible.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(surface.attributes, surfaceAttrs)
        self.assertAttributesEqualDict(surface.cockpitAttributes, defaultCockpitAttrs)

        self.assertAttributesEqualDict(conditions.attributes, conditionsAttrs)
        self.assertAttributesEqualDict(conditions.cockpitAttributes, defaultCockpitAttrs)

    def test_export_materials(self):
        def filterLines(line):
            return isinstance(line[0], str) and line[0].find('ATTR_') == 0

        filename = 'test_materials'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestMaterials])
