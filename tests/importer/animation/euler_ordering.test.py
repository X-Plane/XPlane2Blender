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


class TestEulerOrdering(XPlaneTestCase):
    def test_euler_ordering(self) -> None:
        filename = Path(inspect.stack()[0].function + ".obj")
        import_obj(__dirname__ / Path("fixtures") / filename)
        bpy.context.scene.frame_set(2)
        test_data = [
            # Single Axis
            ("order_x_pos", "XYZ", (30, 0, 0)),  # +X
            ("order_x_neg", "XYZ", (-30, 0, 0)),  # -X
            ("order_y_pos", "XYZ", (0, 30, 0)),  # +Y
            ("order_y_neg", "XYZ", (0, -30, 0)),  # -Y
            ("order_z_pos", "XYZ", (0, 0, 30)),  # +Z
            ("order_z_neg", "XYZ", (0, 0, -30)),  # -Z
            # Double Axis - ZXY
            ("order_yx_as_zxy_XYZ", "XYZ", (67, 17, 0)),  # YX
            ("order_zy_as_zxy_XYZ", "XYZ", (0, 120, 88)),  # ZY
            ("order_zx_as_zxy_XYZ", "XYZ", (170, 0, 99)),  # ZX
            # Double Axis - XYZ
            ("order_xy_as_xyz_ZYX", "ZYX", (38, 78, 0)),  # XY
            ("order_yz_as_xyz_ZYX", "ZYX", (0, 99, 130)),  # YZ
            ("order_xz_as_xyz_ZYX", "ZYX", (44, 0, 200)),  # XZ
            # Triple Axis
            ("order_xyz_ZYX", "ZYX", (72, 240, 2)),
            ("order_xzy_YZX", "YZX", (221, 223, 196)),
            ("order_yxz_XZY", "XZY", (163, 11, 177)),
            ("order_yxz_ZXY", "ZXY", (72, 241, 2)),
            ("order_zxy_YXZ", "YXZ", (62, 72, 223)),
            ("order_zyx_XYZ", "XYZ", (111, 12, 163)),
        ]
        for ob_name, rotation_mode, euler in test_data:
            ob = bpy.data.objects[ob_name]
            print(
                f"Trying {ob.name}, {rotation_mode} vs {ob.rotation_mode}, {tuple(map(math.degrees, ob.rotation_euler))} vs {euler}"
            )
            self.assertEqual(rotation_mode, ob.rotation_mode)
            self.assertVectorAlmostEqual(ob.rotation_euler, map(math.radians, euler), 1)


runTestCases([TestEulerOrdering])
