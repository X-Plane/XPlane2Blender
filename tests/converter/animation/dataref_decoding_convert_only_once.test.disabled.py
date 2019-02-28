"""
As it turns out, this isn't needed. Maybe one day it will
"""
import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType, WORKFLOW_DEFAULT_ROOT_NAME


__dirname__ = os.path.dirname(__file__)

class TestDatarefsConvertOnlyConvertedOnce(XPlaneTestCase):
    def test_armature_only_converted_once(self):
        """This tests that.... the converter converts without crashing? Yea. Its pretty simple."""
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)


runTestCases([TestDatarefsConvertOnlyConvertedOnce])
