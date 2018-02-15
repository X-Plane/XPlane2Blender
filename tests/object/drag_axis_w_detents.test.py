import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or\
             "ATTR_axis_detented" in line[0] or\
             "ATTR_axis_detent_range" in line[0])

class TestDragAxisWDetents(XPlaneTestCase):
    def test_01_parent_driven_by_two_datarefs(self):
        out  = self.exportLayer(0)
        self.assertLoggerErrors(2)

    def test_02_parent_has_three_non_clamping_keyframes(self):
        out  = self.exportLayer(1)
        self.assertLoggerErrors(2)

    def test_03_translation_bone_driven_by_two_datarefs(self):
        out  = self.exportLayer(2)
        self.assertLoggerErrors(2)

    def test_04_translation_bone_has_three_non_clamping_keyframes(self):
        out  = self.exportLayer(3)
        self.assertLoggerErrors(2)

    def test_05_translation_bone_not_a_leaf(self):
        out  = self.exportLayer(4)
        self.assertLoggerErrors(1)

    def test_06_translation_bone_has_non_anim_parent(self):
        out  = self.exportLayer(5)
        self.assertLoggerErrors(2)

    def test_07_translation_bone_does_not_start_or_end_at_origin(self):
        out  = self.exportLayer(6)
        self.assertLoggerErrors(1)

    def test_08_translation_bone_pos_not_both_zero(self):
        out  = self.exportLayer(7)
        self.assertLoggerErrors(1)

    def test_09_translation_bone_must_have_axis_detent_ranges(self):
        out  = self.exportLayer(8)
        self.assertLoggerErrors(2)

    def test_10_known_good_drag_axis_w_detents(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            9, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestDragAxisWDetents])
