import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestMoveGlobalMatProps(XPlaneTestCase):
    def test_properties_updated(self):
        names = [
            "01_NoMaterials_BecomesFalse",
            "02_MaterialsAllTrue_BecomesTrue",
            "03_MaterialsAllFalse_BecomesFalse",
            "04_MaterialsMixed_BecomesTrue",
            "05_MaterialsInHierarchyCollection_BecomesTrue",
            "07_NoMaterialsInHierarchyCollection_BecomesFalse",
            "10_MaterialsAllTrue_BecomesTrue",
            "06_MaterialsInHierarchyObject_BecomesTrue",
            "08_NoMaterialsHierarchyObject_BecomesFalse",
            "09_MaterialTrueObject_BecomesTrue",
        ]

        for name in names:
            if "Object" in name:
                test_block = bpy.data.objects[name]
            else:
                test_block = bpy.data.collections[name]

            if "BecomesTrue" in name:
                assertFn = self.assertTrue
            elif "BecomesFalse" in name:
                assertFn = self.assertFalse
            assertFn(
                test_block.xplane.layer.blend_glass, msg=f"{name} did not set properly"
            )
            assertFn(
                test_block.xplane.layer.normal_metalness,
                msg=f"{name} did not set properly",
            )

            if name.startswith(("01",)):
                tint, tint_albedo, tint_emissive = (False, 0.0, 0.0)
            elif name.startswith(
                (
                    "02",
                    "05",
                    "06",
                    "09",
                    "10",
                )
            ):
                tint, tint_albedo, tint_emissive = (True, 0.2, 0.8)
            elif name.startswith(
                (
                    "03",
                    "04",
                    "07",
                    "08",
                )
            ):
                tint, tint_albedo, tint_emissive = (False, 0.1, 0.9)

            self.assertEqual(test_block.xplane.layer.tint, tint)
            self.assertAlmostEqual(
                test_block.xplane.layer.tint_albedo, tint_albedo, places=1
            )
            self.assertAlmostEqual(
                test_block.xplane.layer.tint_emissive, tint_emissive, places=1
            )


runTestCases([TestMoveGlobalMatProps])
