import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class MonkeyTest(XPlaneTestCase):
    def filterLine(self, line):
        # only keep ANIM_ lines
        return isinstance(line[0], str) and line[0].find('ANIM_') == 0

    def test_monkey_against_249_export(self):
        filename = 'test_monkey_249'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            self.filterLine
        )

    def test_monkey_export(self):
        filename = 'test_monkey'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            self.filterLine
        )


runTestCases([MonkeyTest])
