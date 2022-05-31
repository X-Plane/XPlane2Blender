import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestLibraryHeader(XPlaneTestCase):
    def test_library_header_good(self) -> None:
        try:
            xplane_imp_parser.import_obj(
                pathlib.Path(__dirname__, "fixtures", "test_library_header_good.obj")
            )
        except xplane_imp_parser.UnrecoverableParserError:
            self.fail(msg="test_library_header_good.obj did not parse correctly")

    def test_library_header_bad(self) -> None:
        files = [
            "test_library_header_bad_comment.obj",
            "test_library_header_bad_empty.obj",
            "test_library_header_bad_nl_in_middle.obj",
            "test_library_header_bad_no_800.obj",
            "test_library_header_bad_no_I.obj",
            "test_library_header_bad_no_OBJ.obj",
        ]

        for filepath in [
            Path(__dirname__, "fixtures", f"{filename}") for filename in files
        ]:
            with self.subTest(filepath=filepath):
                self.assertRaises(
                    xplane_imp_parser.UnrecoverableParserError,
                    lambda: xplane_imp_parser.import_obj(filepath),
                )


runTestCases([TestLibraryHeader])
