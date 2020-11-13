import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("PARTICLE_SYSTEM" in line[0] or\
            "EMITTER" in line[0])

class TestParticleNameAndIndex(XPlaneTestCase):
    def test_01_Empty_blank_name_fails(self):
        out  = self.exportLayer(0)
        self.assertLoggerErrors(1)

    def test_02_Empty_index_enabled(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

    def test_03_Empty_index_disabled(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestParticleNameAndIndex])
