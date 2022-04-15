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

# ONBOARDING: I was pressed for time and couldn't deal with
# making this environment agnostic. If you're reading this because you need to
# debug this code, I'm sorry for the trouble.
@unittest.skipIf(
    Path("C:/Users/Ted/XPlane2Blender/tests/xplane_types/xplane_file") != __dirname__,
    "This test is environment specific. You'll need to make it agnostic or change the paths for your computer.",
)
class TestResourcePaths(XPlaneTestCase):
    def test_resource_paths_cases_1_4(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TEXTURE"},
            filename,
        )

    def test_resource_paths_cases_5_and_10(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"TEXTURE"},
            filename,
        )

    def test_errors_6_7(self) -> None:
        filename = inspect.stack()[0].function

        out = self.exportExportableRoot(filename[5:])
        self.assertLoggerErrors(5)


runTestCases([TestResourcePaths])
