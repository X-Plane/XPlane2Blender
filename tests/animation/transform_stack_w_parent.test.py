import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestTransformStackWParent(XPlaneTestCase):
    def setUp(self):
        super(TestTransformStackWParent, self).setUp()

    def test_transform_stack_w(self):
        def filterLines(line):
            return isinstance(line[0], str) and (line[0].find('ANIM') == 0)

        filenames = ['cube_loc_w_parent','cube_locrot_w_parent','cube_rot_w_parent','cube_none_w_parent']

        layer_num = 0
        for filename in filenames:
            self.assertLayerExportEqualsFixture(
                layer_num, os.path.join(__dirname__, 'fixtures', 'transform_stack', 'test_transform_stack_' + filename + '.obj'),
                filterLines,
                'test_transform_stack_' + filename + '.obj',
            )
            layer_num += 1

runTestCases([TestTransformStackWParent])
