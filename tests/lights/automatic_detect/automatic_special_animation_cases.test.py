import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestAutomaticSpecialAnimationCases(XPlaneTestCase):
    def test_automatic_special_animation_cases(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"LIGHT_PARAM"},
            filename,
        )

    def test_automatic_special_animation_dir_mag_calc_cases(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"LIGHT_PARAM"},
            filename,
        )


runTestCases([TestAutomaticSpecialAnimationCases])
