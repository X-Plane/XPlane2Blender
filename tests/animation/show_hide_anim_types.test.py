import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestShowHideAnimTypes(XPlaneTestCase):
    def setUp(self):
        super(TestShowHideAnimTypes,self).setUp()
    
    def test_show_hide_anim_types(self):
        def filterLines(line):
            return isinstance(line[0], str) and (line[0].find('ANIM') == 0)
        
        self.assertLayerExportEqualsFixture(0,
                                            os.path.join(__dirname__, 'fixtures', 'test_show_hide_hide_near_0.obj'),
                                            'test_show_hide_hide_near_0.obj',
                                            filterLines)

        self.assertLayerExportEqualsFixture(1,
                                            os.path.join(__dirname__, 'fixtures', 'test_show_hide_show_near_0.obj'),
                                            'test_show_hide_show_near_0.obj',
                                            filterLines)
runTestCases([TestShowHideAnimTypes])