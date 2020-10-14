# TI To use
# TI 1. Copy and rename to match your blend files name - "name.test.py"
# TI 2. Delete all lines that begin with #TI, like this one
# TI    (otherwise it will NOT pass code review)
# TI 3. Rename as needed, following conventions
# TI
# TI Guidelines for .test.blend files
# TI (Developed after many many many tests made)
# TI - An active text window with text block called "Unit Test Overview" should be shown featuring an outline of what the test is for and what the names, data, etc means
# TI - The textblock "Unit Test Overview" should start with the header "Unit Test Overview", followed by a blank line and text starting after 4 spaces
# TI - The textblock should be manually word wrapped so the contents don't change when you adjust the size of the window
# TI - Layers are alphabetical, start with "test", and take their names from object names
# TI - Use "01_","02_", etc to enforce alphabetical layer order, rather than abusing a thesaurus
# TI - The console should also be open with the code "bpy.ops.export.xplane_obj()" typed. It should be the focused window allowing a person to open the .blend file and press enter
# TI - Scene > Advanced Settings > Debug (and Object > Advanced Options > Debug for every OBJ Setting) turned on
# TI - In Blender file, select some useful object to immediatly see, or select the last object in the outliner
# TI (Nearly entirely arbitrary: consistency is generally useful someday)
import inspect
import os
import sys
from typing import Tuple

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers

__dirname__ = os.path.dirname(__file__)


class TestMoveNormalMetalnessBlendGlass(XPlaneTestCase):
    def test_properties_updated(self):
        names = [
            "01_NoMaterials_BecomesFalse",
            "02_MaterialsAllTrue_BecomesTrue",
            "03_MaterialsAllFalse_BecomesFalse",
            "04_MaterialsMixed_BecomesTrue",
            "05_MaterialsInHierarchyCollection_BecomesTrue",
            "07_NoMaterialsInHierarchyCollection_BecomesFalse",
            "10_MaterialsAllTrue_BecomesTrue",
            "06_MaterialsInHierarchyObject_BecomesTrue",
            "08_NoMaterialsHierarchyObject_BecomesFalse",
            "09_MaterialTrueObject_BecomesTrue",
        ]
        for name in names:
            if "Object" in name:
                test_block = bpy.data.objects[name]
            else:
                test_block = bpy.data.collections[name]

            if "BecomesTrue" in name:
                assertFn = self.assertTrue
            elif "BecomesFalse" in name:
                assertFn = self.assertFalse
            assertFn(
                test_block.xplane.layer.blend_glass, msg=f"{name} did not set properly"
            )
            assertFn(
                test_block.xplane.layer.normal_metalness,
                msg=f"{name} did not set properly",
            )


runTestCases([TestMoveNormalMetalnessBlendGlass])
