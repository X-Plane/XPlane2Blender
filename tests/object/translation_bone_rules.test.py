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
             "ATTR_manip" in line[0])

class TestTranslationBoneRules(XPlaneTestCase):
    # Tests that assert 2 logger errors include the specific
    # error and the general "See online docs"
    def test_01_bone_must_be_leaf_bone(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_02_bone_must_have_parent_w_rotation(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(1)

    def test_03_must_only_be_driven_by_only_1_dataref(self):
        out = self.exportLayer(2)
        self.assertLoggerErrors(1)

    def test_04_must_have_exactly_2_keyframes(self):
        out = self.exportLayer(3)
        self.assertLoggerErrors(1)

    def test_05_must_not_animate_along_rotation_axis(self):
        out = self.exportLayer(4)
        self.assertLoggerErrors(1)

    def test_06_positions_at_each_keyframe_must_not_be_same(self):
        out = self.exportLayer(5)
        self.assertLoggerErrors(1)

    def test_07_position_at_each_keyframe_must_not_both_be_0(self):
        out = self.exportLayer(6)
        self.assertLoggerErrors(1)

    def test_08_must_not_be_animated_for_rotation(self):
        out = self.exportLayer(7)
        self.assertLoggerErrors(1)

    def test_09_must_have_axis_detent_ranges(self):
        out = self.exportLayer(8)
        self.assertLoggerErrors(1)

    def test_10_known_good_translation_bone(self):
        filename = inspect.stack()[0][3]
        self.assertLayerExportEqualsFixture(
            9, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestTranslationBoneRules])
