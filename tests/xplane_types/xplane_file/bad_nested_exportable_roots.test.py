import inspect

from typing import Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.xplane_helpers import XPlaneLogger, logger
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestBadNestedExportableRoots(XPlaneTestCase):
    def test_nested_exportable_roots_caught(self)->None:
        def reset():
            test_creation_helpers.delete_all_text_files()
            logger.clear()
            logger.addTransport(XPlaneLogger.ConsoleTransport())
            logger.addTransport(XPlaneLogger.InternalTextTransport())
        # This test uses an extremely stupid hard-coded brittle method of counting errors,
        # It is literally counting the ','s that appears in the relevant error message's
        # list of "Checkmark only one of these" collections and object to fix
        for i in range(2, -1, -1):
            reset()
            out = self.exportExportableRoot(bpy.data.collections[f"exportable_collection_{i}"], force_visible=False)
            try:
                line = [l for l in XPlaneTestCase.get_XPlane2Blender_log_content() if "Nested roots found" in l][0]
            except IndexError: # i == 0 should have no errors
                self.assertLoggerErrors(0)
            else:
                self.assertEqual(line.count(","), i)

        reset()
        out = self.exportExportableRoot(bpy.data.collections["exportable_collection_has_nested_exportable_object"])
        line = [l for l in XPlaneTestCase.get_XPlane2Blender_log_content() if "Nested roots found" in l][0]
        self.assertEqual(line.count(","), 3)

        for i in range(2, -1, -1):
            reset()
            out = self.exportExportableRoot(bpy.data.objects[f"exportable_object_{i}"], force_visible=False)
            try:
                line = [l for l in XPlaneTestCase.get_XPlane2Blender_log_content() if "Nested roots found" in l][0]
            except IndexError: # i == 0 should have no errors
                self.assertLoggerErrors(0)
            else:
                self.assertEqual(line.count(","), i)


runTestCases([TestBadNestedExportableRoots])
