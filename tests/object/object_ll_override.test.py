import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestObjectLLOverride(XPlaneTestCase):
    def test_01_mesh_ll_overload_emits(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TRIS", "ATTR_light_level"},
            filename,
        )

    def test_02_mesh_ll_overload_emits_not_material(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TRIS", "ATTR_light_level"},
            filename,
        )

    def test_03_mesh_ll_overload_weird_cases(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TRIS", "ATTR_light_level"},
            filename,
        )

    def test_04_mesh_ll_overload_emits_not_material_nts(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TRIS", "ATTR_light_level"},
            filename,
        )


runTestCases([TestObjectLLOverride])
