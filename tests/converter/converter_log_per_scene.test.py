import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import LOG_NAME, ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

class TestConvertLogPerScene(XPlaneTestCase):
    def test_converter_log_per_scene(self)->None:
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.REGULAR.name)
        def _try(name:str)->Optional[bpy.types.Text]:
            try:
                return bpy.data.texts[name]
            except:
                 return None

        scene_wings_txt =       _try(LOG_NAME + ", Scene_wings")
        scene_cockpit_txt =     _try(LOG_NAME + ", Scene_cockpit")
        scene_pre_convert_txt = _try(LOG_NAME + ", Pre-Convert Fixes")
        self.assertIsNotNone(scene_wings_txt,       msg="Scene_wings was not found")
        self.assertIsNotNone(scene_cockpit_txt,     msg="Scene_cockpit was not found")
        self.assertIsNotNone(scene_pre_convert_txt, msg="Pre-Convert Fixes was not found")
        self.assertGreater(len(scene_wings_txt.lines), 15) # 15 is arbitrary, > 1 seemed prone to False Positives
        self.assertGreater(len(scene_cockpit_txt.lines), 15) # 15 is arbitrary, > 1 seemed prone to False Positives
        # TODO: Come up with something better or better hueristics. Obviously the content is going to change so much
        # we can't check literal files
        self.assertGreater(len(scene_pre_convert_txt.lines), 1) # Given that this is just going to say "We don't have any fixes", I'll probably be short


runTestCases([TestConvertLogPerScene])

