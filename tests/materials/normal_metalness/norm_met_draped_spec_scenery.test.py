import bpy
import os
import sysconfig
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

#Tests Normal Metalness Draped Specularity cases for Scenery type exports
class TestNormMetDrapedSpecScenery(XPlaneTestCase):
    def test_norm_met_off_one_drap_inst(self):
        out = xplane_file.createFileFromBlenderLayerIndex(0).write()
        self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_off_one_drap_inst",sub_dir="draped_spec_scenery"))

    def test_norm_met_off_one_drap_scen(self):
        out = xplane_file.createFileFromBlenderLayerIndex(1).write()
        self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_off_one_drap_scen",sub_dir="draped_spec_scenery"))

    def test_norm_met_off_two_drap_inst(self):
        expected_logger_errors = 1
        out = xplane_file.createFileFromBlenderLayerIndex(2).write()
        self.assertEqual(len(logger.findErrors()), expected_logger_errors)
        logger.clearMessages()

    def test_norm_met_off_two_drap_scen(self):
        out = xplane_file.createFileFromBlenderLayerIndex(3).write()
        print(out)
        self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_off_two_drap_scen",sub_dir="draped_spec_scenery"))

    def test_norm_met_on_one_drap_inst(self):
        out = xplane_file.createFileFromBlenderLayerIndex(4).write()
        self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_one_drap_inst",sub_dir="draped_spec_scenery"))

    def test_norm_met_on_one_drap_scen(self):
        out = xplane_file.createFileFromBlenderLayerIndex(5).write()
        self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_one_drap_scen",sub_dir="draped_spec_scenery"))

    def test_norm_met_on_two_drap_inst(self):
         out = xplane_file.createFileFromBlenderLayerIndex(6).write()
         self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_two_drap_inst",sub_dir="draped_spec_scenery"))

    def test_norm_met_on_two_drap_scen(self):
         out = xplane_file.createFileFromBlenderLayerIndex(7).write()
         self.assertFileEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_two_drap_scen",sub_dir="draped_spec_scenery"))

runTestCases([TestNormMetDrapedSpecScenery])
