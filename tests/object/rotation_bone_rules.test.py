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

class TestRotationBoneRules(XPlaneTestCase):
    def test_01_no_animated_rotation_bone(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)
    def test_02_only_rotated_around_one_axis(self):
        out = self.exportLayer(1)
        self.assertLoggerErrors(1)
    def test_03_rot_keyframes_must_be_sorted(self):
        out = self.exportLayer(2)
        self.assertLoggerErrors(1)

    def test_04_must_be_driven_by_only_1_dataref(self):
        out = self.exportLayer(3)
        self.assertLoggerErrors(1)

    def test_05_must_have_at_least_2_non_clamping_keyframes(self):
        out = self.exportLayer(4)
        self.assertLoggerErrors(1)

    def test_06_0_degree_rotation_not_allowed(self):
        out = self.exportLayer(5)
        self.assertLoggerErrors(1)

    def test_07_counter_clockwise_also_allowed(self):
        filename = inspect.stack()[0][3]
        self.assertLayerExportEqualsFixture(
            6, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    # See github issue #360
    def test_08_neg_15_15_degree_animation_allowed(self):
        filename = inspect.stack()[0][3]
        self.assertLayerExportEqualsFixture(
            7, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_09_dataref_values_descending_allowed(self):
        out = self.exportLayer(8)
        self.assertLoggerErrors(0)

    def test_10_no_rounding_bug_from_unnormalized_vector(self):
        out = self.exportLayer(9)
        self.assertLoggerErrors(0)

    def test_11_known_good_rotation_bone(self):
        filename = inspect.stack()[0][3]
        self.assertLayerExportEqualsFixture(
            10, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestRotationBoneRules])
