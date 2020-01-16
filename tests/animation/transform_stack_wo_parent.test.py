import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestTransformStackWOParent(XPlaneTestCase):
    def setUp(self):
        super(TestTransformStackWOParent, self).setUp()

    def test_transform_stack_wo(self):
        def filterLines(line):
            return isinstance(line[0], str) and (line[0].find('ANIM') == 0)

        filenames = ['cube_loc_wo_parent','cube_locrot_wo_parent','cube_rot_wo_parent','cube_none_wo_parent']

        layer_num = 0
        for filename in filenames:
            self.assertLayerExportEqualsFixture(
                layer_num, os.path.join(__dirname__, 'fixtures', 'transform_stack', 'test_transform_stack_' + filename + '.obj'),
                'test_transform_stack_' + filename + '.obj',
                filterLines
            )
            layer_num += 1

runTestCases([TestTransformStackWOParent])
