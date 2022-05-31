import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy
from mathutils import Vector

from io_xplane2blender import xplane_constants, xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_cmd_builder import (
    IntermediateAnimation,
    IntermediateDataref,
)
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestShowHideShow(XPlaneTestCase):
    def test_show_hide_show_animation(self) -> None:
        filename = inspect.stack()[0].function
        import_obj(make_fixture_path(__dirname__, filename))
        self.assertAction(
            bpy.data.collections[filename[5:]].objects[0],
            IntermediateAnimation(
                locations=[],
                rotations=[],
                xp_datarefs=[
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_SHOW,
                        loop=0,
                        path="dref_1",
                        show_hide_v1=-1.0,
                        show_hide_v2=-0.5,
                        values=[],
                    ),
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_HIDE,
                        loop=0,
                        path="dref_2",
                        show_hide_v1=-0.5,
                        show_hide_v2=-0.6666666666,
                        values=[],
                    ),
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_HIDE,
                        loop=0,
                        path="dref_3",
                        show_hide_v1=0.6666666666,
                        show_hide_v2=-1.0,
                        values=[],
                    ),
                ],
            ),
        )


runTestCases([TestShowHideShow])
