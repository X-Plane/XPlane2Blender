import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("PARTICLE_SYSTEM" in line[0])

class TestParticlePssFile(XPlaneTestCase):
    def test_file_not_dot_pss(self):
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_file_pss_but_not_real(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_file_pss_and_real(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_empties_without_pss_fails(self):
        out = self.exportLayer(3)
        self.assertLoggerErrors(1)

#TI Class name above
runTestCases([TestParticlePssFile])
