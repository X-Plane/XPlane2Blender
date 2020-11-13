import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)

class TestParentOutOfCollectionNoAttrShare(XPlaneTestCase):
    def test_HasManip_Exp(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "CUSTOM_PROP", "ATTR_", "CUSTOM_MATERIAL_PROP", "TRIS"},
            filename,
        )

    def test_HasVisuals_Exp(self)->None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
            {"ANIM", "CUSTOM_PROP", "ATTR_", "CUSTOM_MATERIAL_PROP", "TRIS"},
            filename,
        )


runTestCases([TestParentOutOfCollectionNoAttrShare])
