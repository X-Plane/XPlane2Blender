import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestNoDroppedDupKeys(XPlaneTestCase):
    def test_no_drop_dup_keys(self):
        def filterLines(line):
            return isinstance(line[0], str) and (line[0].find('ANIM') == 0)

        filename = 'test_no_drop_dup_trans_rot_'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + 'aa' + '.obj'),
            filterLines,
            filename + 'aa',
        )

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + 'euler' + '.obj'),
            filterLines,
            filename + 'euler',
        )

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + 'quat' + '.obj'),
            filterLines,
            filename + 'quat',
        )

runTestCases([TestNoDroppedDupKeys])

