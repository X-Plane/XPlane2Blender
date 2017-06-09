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
            return isinstance(line[0], str) and (line[0] == 'VT' or line[0].find('ANIM') == 0)

        filenames = [\
                     #'cube_loc_w_parent',\
                     'cube_locrot_w_parent',\
                     'cube_none_w_parent',\
                     'cube_rot_w_parent']
        
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc')
        import pydevd;pydevd.settrace()
        out0 = self.exportLayer(0)
        out1 = self.exportLayer(1)
        out2 = self.exportLayer(2)
        out3 = self.exportLayer(3)
        
        for filename in filenames:
            
            self.assertLayerExportEqualsFixture(
                0, os.path.join(__dirname__, 'fixtures', 'transform_stack', 'test_transform_stack_' + filename + '.obj'),
                filename,
                filterLines
            )

runTestCases([TestTransformStackWParent])
