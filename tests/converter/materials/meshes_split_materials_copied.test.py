import inspect

from collections import namedtuple, OrderedDict
from typing import Tuple

import os
import sys
import re

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_249_converter import xplane_249_constants as xp249c
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

#TI filter obj output. Define above or in the class level
#def filterLines(line:Tuple[str])->bool:
    #return (isinstance(line[0],str)
             #and ("OBJ_DIRECTIVE" in line[0]
                   #or)
class TestMeshesSplitMaterialsCopied(XPlaneTestCase):
    """
    # New objects will have one material only, made of only grouped faces
    """
    _M25 = "Material_.25" # Red
    _M75 = "Material_.75" # Blue
    _M90 = "Material_.9" # Yellow
    _MDEF = xp249c.DEFAULT_MATERIAL_NAME # Created during material conversion process, grey
    _ObjectDetails = namedtuple(
        "_ObjectDetails",
        ["new_name",
        "mat_name",]
        )

    # Tuple of list of objectnames to a dictionary of TF group types ("TILE", "SHADOW", "DEFAULT", "NONE") and
    # what specularity/diffuse RGB material found to be used for it further code will check that Material
    # not only the specualrty and Diffuse RGB are correct but that the correct dirivative copy is made from it
    # material properties

    _results = OrderedDict() # type: Dict[str,Tuple[Union[str,str]]
    # 1face_tests
    _results["1face_0mat_0tf"] = ("NONE", _MDEF)
    _results["1face_0mat_1tf"] = (xp249c.HINT_TF_TEX, _MDEF)
    _results["1face_1mat_0tf"] = ("NONE", _M25)
    _results["1face_1mat_1tf"] = (xp249c.HINT_TF_TEX, _M25)

    #2face_tests
    _results["2face_0mat_0tf"] = ("NONE", _MDEF)
    _results["2face_0mat_2tf"] = (xp249c.HINT_TF_TEX, _MDEF, xp249c.HINT_TF_SHADOW, _MDEF)

    _results["2face_1mat_0tf"] = ("NONE", _M25)
    _results["2face_1mat_2tf"] = (xp249c.HINT_TF_TEX, _M25, xp249c.HINT_TF_SHADOW, _M25)

    _results["2face_2mat_0tf"] = ("NONE", _M75, _M25)

    _results["2face_2mat_2tf"] = (xp249c.HINT_TF_TEX, _M25, xp249c.HINT_TF_SHADOW, _M75)

    #3test_faces
    _results["3face_3mat_2tf_2used"] = (xp249c.HINT_TF_TEX, _M25, xp249c.HINT_TF_COLL, _M25, _M75)

    #4test_faces
    _results["4face_3mat_1tf"] = (xp249c.HINT_TF_COLL, _M25, _M25, _M75, _M90)
    _results["4face_3mat_2tf"] = (xp249c.HINT_TF_TEX, _M25, _M25, xp249c.HINT_TF_SHADOW, _M75, _M90)
    _results["4face_3mat_3tf_1as"] = ("NONE", _MDEF, _MDEF, _MDEF, xp249c.HINT_TF_SHADOW, _M90)

    def test_no_generated_materials(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertFalse([mat for mat in bpy.data.materials if re.match(r"Material\.TF\.\d{1,5}", mat.name) and mat.users])

    def test_split_groups_carry(self):
        for obj_name, face_sequence in self._results.items():
            face_id = None
            for seq in face_sequence:
                if isinstance(seq, str):
                    hint_suffix = seq
                    try:
                        face_id += 1
                    except TypeError:
                        face_id = 0
                    continue

                obj_suffix = "_%d" % face_id

                # These both turn to no hint
                if hint_suffix in {xp249c.HINT_TF_TEX, "NONE"}:
                    hint_suffix = ""
                else:
                    hint_suffix = "_" + hint_suffix

                obj = bpy.data.object[obj_name + obj_suffix]

                # How do we know the materials are correct? Other unit tests cover it
                self.assertEqual(obj.material_slots[0].material, bpy.data.materials[seq + hint_suffix])

    def test_diffuse_and_specularity_copied(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        for mat in filter(lambda mat: mat.users, bpy.data.materials):
            if ".25" in mat.name:
                self.assertAlmostEqual(mat.specular_intensity, 0.25)
                self.assertAlmostEqual(mat.diffuse_color[0], 0.770)
                self.assertAlmostEqual(mat.diffuse_color[1], 0.000)
                self.assertAlmostEqual(mat.diffuse_color[2], 0.000)
            elif ".75" in mat.name:
                self.assertAlmostEqual(mat.specular_intensity, 0.75)
                self.assertAlmostEqual(mat.diffuse_color[0], 0.000)
                self.assertAlmostEqual(mat.diffuse_color[1], 0.000)
                self.assertAlmostEqual(mat.diffuse_color[2], 0.880)
            elif ".9" in mat.name:
                self.assertAlmostEqual(mat.specular_intensity, 0.90)
                self.assertAlmostEqual(mat.diffuse_color[0], 0.990)
                self.assertAlmostEqual(mat.diffuse_color[1], 0.990)
                self.assertAlmostEqual(mat.diffuse_color[2], 0.0)

    def test_fewest_materials_made(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.REGULAR.name)
        self.assertEqual(len([mat for mat in bpy.data.materials if mat.users]), 11)

runTestCases([TestMeshesSplitMaterialsCopied])
