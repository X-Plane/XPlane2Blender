import inspect
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

from io_xplane2blender import xplane_constants, xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_constants import PRECISION_KEYFRAME, PRECISION_OBJ_FLOAT

__dirname__ = Path(__file__).parent


class TestRotationAxisNormalized(XPlaneTestCase):
    def test_rotation_axis_normalized(self) -> None:
        filename = Path(inspect.stack()[0].function + ".obj")

        import_obj(__dirname__ / Path("fixtures") / filename)

        def deg_euler(comps: Tuple[float]) -> Euler:
            return Euler(map(math.radians, comps))

        self.assertAlmostEqual(
            bpy.data.objects["anim_rotate_aa_off_axis"].rotation_axis_angle[0],
            math.radians(9.8963823),
            places=PRECISION_KEYFRAME,
        )
        self.assertVectorAlmostEqual(
            bpy.data.objects["anim_rotate_aa_off_axis"].rotation_axis_angle[1:],
            Vector(
                (
                    0.706446,
                    0.706446,
                    -0.043208,
                )
            ),
            places=PRECISION_KEYFRAME,
        )
        self.assertVectorAlmostEqual(
            bpy.data.objects["anim_rotate_axis_aligned"].rotation_euler,
            deg_euler((0, -5, 0)),
            places=PRECISION_KEYFRAME,
        )

        self.assertAlmostEqual(
            bpy.data.objects["anim_rotate_begin_aa_off_axis"].rotation_axis_angle[0],
            math.radians(83.335944),
            places=PRECISION_KEYFRAME,
        )
        self.assertVectorAlmostEqual(
            bpy.data.objects["anim_rotate_begin_aa_off_axis"].rotation_axis_angle[1:],
            Vector((-0.015596, 0.826873, 0.562171)),
            places=PRECISION_KEYFRAME,
        )

        self.assertVectorAlmostEqual(
            bpy.data.objects["anim_rotate_begin_axis_aligned"].rotation_euler,
            deg_euler((0, 0, -80)),
            places=PRECISION_KEYFRAME,
        )


runTestCases([TestRotationAxisNormalized])
