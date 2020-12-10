import inspect
import os
import sys
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestWhitespaceRulesCorrect(XPlaneTestCase):
    def test_whitespace_rules_correct(self) -> None:
        try:
            import_obj(
                pathlib.Path(
                    __dirname__, "fixtures", "test_whitespace_rules_correct.obj"
                )
            )
        except xplane_imp_parser.UnrecoverableParserError:
            self.fail(
                msg="test_whitespace.test.obj should have parsed correctly but didn't"
            )


runTestCases([TestWhitespaceRulesCorrect])
