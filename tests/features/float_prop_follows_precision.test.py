import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = Path(__file__).parent


class TestFloatPropFollowsPrecision(XPlaneTestCase):
    def test_float_prec_start_end_height_cmp(self) -> None:
        filename = Path("fixtures", inspect.stack()[0].function + ".obj")
        fixture_path = __dirname__ / filename

        self.assertExportableRootExportEqualsFixture(
            fixture_path.stem[5:], fixture_path, {"ATTR_manip"}, fixture_path.stem
        )

    def test_float_prec_manip_props_wysiwyg(self) -> None:
        filename = Path("fixtures", inspect.stack()[0].function + ".obj")
        fixture_path = __dirname__ / filename

        self.assertExportableRootExportEqualsFixture(
            fixture_path.stem[5:], fixture_path, {"ATTR_manip"}, fixture_path.stem
        )


runTestCases([TestFloatPropFollowsPrecision])
