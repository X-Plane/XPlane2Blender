import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestMaterials(XPlaneTestCase):

    def test_custom_prop_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('custom_prop') == 0 or \
                   line[0] == 'TRIS')

        filename = 'test_custom_prop'
        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_conditions_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('IF') == 0 or \
                   line[0] == 'ENDIF' or \
                   line[0] == 'TRIS')

        filename = 'test_conditions'
        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_optimize_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0] == 'VT' or \
                   line[0] == 'ID' or \
                   line[0] == 'IDX' or \
                   line[0] == 'TRIS')

        bpy.context.scene.xplane.optimize = True

        filename = 'test_optimize'
        self.assertLayerExportEqualsFixture(
            3, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_texture_coords_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0] == 'VT' or \
                   line[0].find('TEXTURE') == 0)

        filename = 'test_texture_coords'
        self.assertLayerExportEqualsFixture(
            4, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_group_instances_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0] == 'VT' or \
                   line[0] == 'ID' or \
                   line[0] == 'IDX' or \
                   line[0] == 'TRIS')

        filename = 'test_group_instances'
        self.assertLayerExportEqualsFixture(
            5, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_export_in_layers_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0] == 'VT' or \
                   line[0] == 'ID' or \
                   line[0] == 'IDX' or \
                   line[0] == 'TRIS')

        filename = 'test_export_in_layers_enabled'
        self.assertLayerExportEqualsFixture(
            6, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

        filename = 'test_export_in_layers_disabled'
        self.assertLayerExportEqualsFixture(
            7, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_custom_header_props_export(self):
        filename = 'test_custom_header_props'
        self.assertLayerExportEqualsFixture(
            8, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename
        )

    def test_custom_anim_prop_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('ANIM') == 0 or \
                   line[0] == 'TRIS')

        filename = 'test_custom_anim_prop'
        self.assertLayerExportEqualsFixture(
            9, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_show_hide_animation_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('ANIM') == 0 or \
                   line[0] == 'TRIS')

        filename = 'test_show_hide_animation'
        self.assertLayerExportEqualsFixture(
            10, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestMaterials])
