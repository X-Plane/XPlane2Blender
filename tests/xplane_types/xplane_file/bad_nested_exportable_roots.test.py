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
        for i in range(1, 4):
            out = self.exportRootObject(bpy.data.collections[f"exportable_collection_{i}"])
            print(f"out len {len(out)}")
            print("---------------------")
            # collection_1 has (3-2) nested roots, collection_2 has (3-1) nested roots
            self.assertLoggerErrors(3-i)

        for i in range(1, 4):
            out = self.exportRootObject(bpy.data.objects[f"exportable_object_{i}"])
            print(f"out len {len(out)}")
            print("---------------------")
            # object_1 has (3-2) nested roots, object_2 has (3-1) nested roots
            self.assertLoggerErrors(3-i)


runTestCases([TestBadNestedExportableRoots])
