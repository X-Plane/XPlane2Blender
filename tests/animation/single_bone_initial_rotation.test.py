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
            return isinstance(line[0], str) and (line[0] == 'VT' or line[0].find('ANIM') == 0)

        filename = 'test_single_bone_initial_rotation'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestSingleBoneInitialRotation])
