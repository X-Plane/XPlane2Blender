import bpy
import os
import sysconfig
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

def make_fixture_path(filename):
    return os.path.join(__dirname__, 'fixtures', filename + '.obj')
    
class TestBlendGlass(XPlaneTestCase):

    def test_air_glass_off_expect_no_dir_export(self):
        def filterLines(line):
            return isinstance(line[0],str) and (line[0] == 'VT' or line[0].find('BLEND_GLASS'))
         
        filename = 'test_air_glass_off_expect_no_dir'
        self.assertLayerExportEqualsFixture(
            0, make_fixture_path(filename),
            filename,
            filterLines
        )

    def test_air_glass_on_expect_dir_export(self):
        def filterLines(line):
            return isinstance(line[0],str) and (line[0].find('BLEND_GLASS'))
         
        filename = 'test_air_glass_on_expect_dir'
        self.assertLayerExportEqualsFixture(
            1, make_fixture_path(filename),
            filename,
            filterLines
        )

    def test_ckpt_glass_off_expect_no_dir_export(self):
        def filterLines(line):
            return isinstance(line[0],str) and (line[0] == 'VT' or line[0].find('BLEND_GLASS'))

        filename = 'test_ckpt_glass_off_expect_no_dir'
        self.assertLayerExportEqualsFixture(
            2, make_fixture_path(filename),
            filename,
            filterLines
        )

    def test_ckpt_glass_on_expect_dir_export(self):
        def filterLines(line):
            return isinstance(line[0],str) and (line[0].find('BLEND_GLASS'))
         
        filename = 'test_ckpt_glass_on_expect_dir'
        self.assertLayerExportEqualsFixture(
            3, make_fixture_path(filename),
            filename,
            filterLines
        )

    def test_instanced_glass_illegal(self):
        filename = 'test_instanced_glass_illegal'

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(4)
        out = xplaneFile.write()

        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()
    
    def test_scenery_glass_illegal(self):
        filename = 'test_scenery_glass_illegal'

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(5)
        out = xplaneFile.write()

        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()
        
    def test_glass_2_mats_conflict(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(6)
        out = xplaneFile.write()
        
        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()
        
runTestCases([TestBlendGlass])