import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestSingleBoneInitialRotation(XPlaneTestCase):
    def setUp(self):
        super(TestSingleBoneInitialRotation, self).setUp()

    def test_single_bone_initial_rotation(self):
        def filterLines(line):
            return isinstance(line[0], str) and ("ANIM" in line[0] == 0)

        filename = 'test_single_bone_initial_rotation'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestSingleBoneInitialRotation])
