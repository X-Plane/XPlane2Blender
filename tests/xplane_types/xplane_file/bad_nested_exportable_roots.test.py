import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestBadNestedExportableRoots(XPlaneTestCase):
    def test_nested_exportable_roots_caught(self)->None:
        for i in range(2, -1, -1):
            out = self.exportExportableRoot(bpy.data.collections[f"exportable_collection_{i}"])
            self.assertLoggerErrors(i)

        out = self.exportExportableRoot(bpy.data.collections["exportable_collection_has_nested_exportable_object"])
        self.assertLoggerErrors(3)

        for i in range(2, -1, -1):
            out = self.exportExportableRoot(bpy.data.objects[f"exportable_object_{i}"])
            self.assertLoggerErrors(i)


runTestCases([TestBadNestedExportableRoots])
