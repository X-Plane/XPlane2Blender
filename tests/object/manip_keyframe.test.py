import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or \
             "ATTR_manip_keyframe" in line[0] or \
             "ATTR_axis_detent_range" in line[0] or\
             "ATTR_manip_drag_rotate" in line[0])

class TestManipKeyframe(XPlaneTestCase):
    def test_01_2_rot_kf_0_detents_0_manip_kf(self):
        filename = inspect.stack()[0].function # type: str
        print(filename)
        print("adsfasdfasdf")
        self.assertExportableRootExportEqualsFixture(
            filename.replace("test_",""),
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines)

    def test_02_3_rot_kf_0_detents_1_manip_kf(self):
        filename = inspect.stack()[0].function # type: str
        self.assertExportableRootExportEqualsFixture(
            filename.replace("test_",""),
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines)

    def test_03_4_rot_kf_0_detents_2_manip_kf(self):
        filename = inspect.stack()[0].function # type: str
        self.assertExportableRootExportEqualsFixture(
            filename.replace("test_",""),
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines)

    def test_04_5_rot_kf_3_detents_3_manip_kf(self):
        filename = inspect.stack()[0].function # type: str
        self.assertExportableRootExportEqualsFixture(
            filename.replace("test_",""),
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines)

    def test_05_6_rot_kf_4_detents_1_pit_4_manip_kf(self):
        filename = inspect.stack()[0].function # type: str
        self.assertExportableRootExportEqualsFixture(
            filename.replace("test_",""),
            os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines)

runTestCases([TestManipKeyframe])
