import bpy
import os
import sysconfig
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

#There is a small chance that this filterLines function looks for more than it needs to, but that could only create (unlikely) false negatives, not false positives.
def filterLines(line):
    return isinstance(line[0],str) and (line[0].find('ATTR_draped')      == 0 or \
                                        line[0].find('ATTR_no_draped')   == 0 or \
                                        line[0].find('ATTR_shiney_rat')  == 0 or \
                                        line[0].find('GLOBAL_specular')  == 0 or \
                                        line[0].find('NORMAL_METALNESS') == 0 or \
                                        line[0].find('TEXTURE')          == 0 or \
                                        line[0].find('TEXTURE_DRAPED')   == 0 or \
                                        line[0].find('TEXTURE_NORMAL')   == 0)

#Tests Normal Metalness Draped Specularity cases for Scenery type exports
class TestNormMetDrapedSpecScenery(XPlaneTestCase):
    def test_norm_met_off_one_drap_inst(self):
        out = self.exportLayer(0)
        self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_off_one_drap_inst",sub_dir="draped_spec_scenery"),filterLines)

    def test_norm_met_off_one_drap_scen(self):
        out = self.exportLayer(1)
        self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_off_one_drap_scen",sub_dir="draped_spec_scenery"),filterLines)

    def test_norm_met_off_two_drap_inst(self):
        expected_logger_errors = 1
        out = self.exportLayer(2)
        self.assertLoggerErrors(expected_logger_errors)

    def test_norm_met_off_two_drap_scen(self):
        expected_logger_errors = 1
        out = self.exportLayer(3)
        self.assertLoggerErrors(expected_logger_errors)

    def test_norm_met_on_one_drap_inst(self):
        out = self.exportLayer(4)
        self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_one_drap_inst",sub_dir="draped_spec_scenery"),filterLines)

    def test_norm_met_on_one_drap_scen(self):
        out = self.exportLayer(5)
        self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_one_drap_scen",sub_dir="draped_spec_scenery"),filterLines)

    def test_norm_met_on_two_drap_inst(self):
         out = self.exportLayer(6)
         self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_two_drap_inst",sub_dir="draped_spec_scenery"),filterLines)

    def test_norm_met_on_two_drap_scen(self):
         out = self.exportLayer(7)
         self.assertFileOutputEqualsFixture(out,make_fixture_path(__dirname__, "test_norm_met_on_two_drap_scen",sub_dir="draped_spec_scenery"),filterLines)

runTestCases([TestNormMetDrapedSpecScenery])
