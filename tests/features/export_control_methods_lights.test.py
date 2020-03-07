import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestExportControlMethodsLights(XPlaneTestCase):
    def test_NotAnimated(self)->None:
        bpy.context.window.scene = bpy.data.scenes["Scene_not_animated"]
        exp_roots = [
            "1_NotVisibleByItself_Exp",
            "2_VisibleParent_Exp",
            ]
        for exp_root in exp_roots:
            with self.subTest(exp_root=exp_root):
                self.assertExportableRootExportEqualsFixture(
                    exp_root,
                    os.path.join(__dirname__, "fixtures", f"test_{exp_root}.obj"),
                    {"LIGHT","VLIGHT", "ANIM_"},
                    "test_" + exp_root,
                )

    def test_Animated(self)->None:
        bpy.context.window.scene = bpy.data.scenes["Scene_animated"]
        exp_roots = [
            "1_NotVisibleByItself_Exp_anim",
            "2_VisibleParent_Exp_anim",
            "3_VisibleButSplitParent_Exp_anim",
            "3_SplitParentVisibleChildren_Exp_anim",
            "4_NotVisibleButSplitParent_Exp_anim",
            ]
        for exp_root in exp_roots:
            with self.subTest(exp_root=exp_root):
                self.assertExportableRootExportEqualsFixture(
                    exp_root,
                    os.path.join(__dirname__, "fixtures", f"test_{exp_root}.obj"),
                    {"LIGHT","VLIGHT", "ANIM_"},
                    "test_" + exp_root,
                )


runTestCases([TestExportControlMethodsLights])
