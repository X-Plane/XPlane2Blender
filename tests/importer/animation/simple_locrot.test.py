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


class TestSimpleLocRot(XPlaneTestCase):
    def test_simple_location_animation(self) -> None:
        filename = inspect.stack()[0].function
        import_obj(make_fixture_path(__dirname__, filename))
        self.assertAction(
            bpy.data.collections[filename[5:]].objects[0],
            IntermediateAnimation(
                locations=[
                    Vector((0, 0, 0)).freeze(),
                    Vector((2, 0, 0)).freeze(),
                ],
                rotations=collections.defaultdict(list),
                xp_dataref=[
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_TRANSFORM,
                        loop=0,
                        path="sim/graphics/animation/sin_wave_2",
                        show_hide_v1=0,
                        show_hide_v2=0,
                        values=[-1, 1],
                    )
                ],
            ),
        )

    def test_simple_rotation_animation(self) -> None:
        filename = inspect.stack()[0].function
        import_obj(make_fixture_path(__dirname__, filename))
        self.assertAction(
            bpy.data.collections[filename[5:]].objects[0],
            IntermediateAnimation(
                locations=[],
                rotations={
                    Vector((1, 0, 0)).freeze(): [0, 90],
                    Vector((0, 1, 0)).freeze(): [0, 30],
                    Vector((0, 0, 1)).freeze(): [0, 3],
                },
                xp_dataref=[
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_TRANSFORM,
                        loop=0,
                        path="sim/graphics/animation/sin_wave_2",
                        show_hide_v1=0,
                        show_hide_v2=0,
                        values=[-1, 1],
                    )
                ],
            ),
        )

    def test_simple_loc_and_rot_animation(self) -> None:
        filename = inspect.stack()[0].function
        import_obj(make_fixture_path(__dirname__, filename))
        self.assertAction(
            bpy.data.collections[filename[5:]].objects[0],
            IntermediateAnimation(
                locations=[
                    Vector((0, 0, 0)).freeze(),
                    Vector((2, 0, 0)).freeze(),
                ],
                rotations={
                    Vector((1, 0, 0)).freeze(): [0, 90],
                    Vector((0, 1, 0)).freeze(): [0, 30],
                    Vector((0, 0, 1)).freeze(): [0, 3],
                },
                xp_dataref=[
                    IntermediateDataref(
                        anim_type=xplane_constants.ANIM_TYPE_TRANSFORM,
                        loop=0,
                        path="sim/graphics/animation/sin_wave_2",
                        show_hide_v1=0,
                        show_hide_v2=0,
                        values=[-1, 1],
                    )
                ]
                * 2,
            ),
        )


runTestCases([TestSimpleLocRot])
