import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_types import xplane_light
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestAutomaticLightProperties(XPlaneTestCase):
    def test_automatic_light_properties(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "LIGHT"},
            filename,
        )

    def test_parsed_lazily_when_table_empty(self) -> None:
        # Enabling the add-on mid-session, or exporting from a script before
        # any .blend has been opened, means load_post never parsed lights.txt.
        # The table has to fill itself on first use: with it empty every
        # Automatic light was "unknown" and came out as a bare LIGHT_NAMED,
        # its params and its orientation animation dropped
        filename = "test_automatic_light_properties"
        xplane_lights_txt_parser._parsed_lights_txt_content.clear()
        try:
            self.assertExportableRootExportEqualsFixture(
                filename[5:],
                os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
                {"ANIM", "LIGHT"},
                filename,
            )
        finally:
            xplane_lights_txt_parser.parse_lights_file()


runTestCases([TestAutomaticLightProperties])
