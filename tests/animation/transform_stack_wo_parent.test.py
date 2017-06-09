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
            return isinstance(line[0], str) and (line[0] == 'VT' or line[0].find('ANIM') == 0)

        filenames = ['cube_loc_wo_parent','cube_locrot_wo_parent','cube_none_wo_parent','cube_rot_wo_parent']
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        import pydevd;pydevd.settrace()
        for filename in filenames:
            self.assertLayerExportEqualsFixture(
                0, os.path.join(__dirname__, 'fixtures', 'transform_stack', 'test_transform_stack_' + filename + '.obj'),
                'test_transform_stack_' + filename + '.obj',
                filterLines
            )

runTestCases([TestTransformStackWOParent])
