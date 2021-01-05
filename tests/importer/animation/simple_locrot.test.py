import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestSimpleLocRot(XPlaneTestCase):
    def test_simple_location(self) -> None:
        files = [
            "test_simple_location_animation",
            "test_simple_rotation_animation",
        ]
        for filepath in [
            Path(__dirname__, "fixtures", f"{filename}.obj") for filename in files
        ]:
            with self.subTest(filepath=filepath):
                import_obj(filepath)


runTestCases([TestSimpleLocRot])
