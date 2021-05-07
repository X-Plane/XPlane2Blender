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

class TestV12LightsCDExport(XPlaneTestCase):
    def test_v12_lights_have_candela(self)->None:
        filepath = __dirname__/Path("fixtures", Path(f"{inspect.stack()[0].function}.obj"))

        self.assertExportableRootExportEqualsFixture(
            filepath.stem[5:],
            filepath,
            {"LIGHT"},
            filepath.name,
        )

runTestCases([TestV12LightsCDExport])
