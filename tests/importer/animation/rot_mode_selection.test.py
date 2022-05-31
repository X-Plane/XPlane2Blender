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


class TestRotModeSelection(XPlaneTestCase):
    def test_rot_mode_selection(self) -> None:
        filename = Path(inspect.stack()[0].function + ".obj")
        import_obj(__dirname__ / Path("fixtures") / filename)

        for name, rotation_mode in {
            "euler_from_no_rotation": "XYZ",
            "euler_from_static_rotation": "XYZ",
            "euler_from_dynamic_rotation_ZYX": "ZYX",
            "aa_from_static_rotation": "AXIS_ANGLE",
            "aa_from_dynamic_rotation": "AXIS_ANGLE",
        }.items():
            ob = bpy.data.objects[name]
            self.assertEqual(ob.rotation_mode, rotation_mode)


runTestCases([TestRotModeSelection])
