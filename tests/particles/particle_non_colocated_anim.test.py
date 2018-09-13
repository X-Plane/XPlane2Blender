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
             "EMITTER" in line[0] or\
             "PARTICLE_SYSTEM" in line[0])

class TestParticleNonColocatedAnim(XPlaneTestCase):
    def test_particle_non_colocated_anim(self):
        filename = inspect.stack()[0][3]

        self.assertRootObjectExportEqualsFixture(
            filename, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestParticleNonColocatedAnim])

