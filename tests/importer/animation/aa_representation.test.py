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


class TestAARepresentation(XPlaneTestCase):
    def test_aa_representation(self) -> None:
        filename = Path(inspect.stack()[0].function + ".obj")

        import_obj(__dirname__ / Path("fixtures") / filename)

        def assertAAEqual(ob: bpy.types.Object, axis: Vector, degrees: float):
            """Tests object rotation as axis angle. Angle given in degrees"""
            self.assertVectorAlmostEqual(
                ob.rotation_axis_angle[1:], axis, xplane_constants.PRECISION_KEYFRAME
            )
            self.assertAlmostEqual(
                ob.rotation_axis_angle[0], math.radians(degrees), PRECISION_KEYFRAME
            )

        assertAAEqual(
            bpy.data.objects["case_a_static_as_pure_static"],
            Vector((0.44721361994743347, 0.7745967507362366, 0.44721361994743347)),
            math.degrees(0.8127555251121521),
        )
        assertAAEqual(
            bpy.data.objects["case_d_static_as_pure_dynamic"],
            Vector((0.40290534496307373, 0.608830451965332, 0.6833687424659729)),
            math.degrees(1.9800684452056885),
        )
        assertAAEqual(
            bpy.data.objects["dynamic"],
            Vector((-0.015596865676343441, 0.826873779296875, 0.5621715188026428)),
            math.degrees(1.45448637008667),
        )


runTestCases([TestAARepresentation])
