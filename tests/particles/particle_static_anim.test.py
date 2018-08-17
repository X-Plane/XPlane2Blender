import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM"    in line[0] or\
             "EMITTER" in line[0])

class TestParticleStaticAnim(XPlaneTestCase):
    def test_particle_emitter_animated(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_particle_emitter_static(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestParticleStaticAnim])

