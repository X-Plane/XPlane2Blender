import inspect

from collections import OrderedDict
from typing import Tuple

import os
import sys
import re

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

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
    _M25 = bpy.data.materials["Material_.25"] # Red
    _M75 = bpy.data.materials["Material_.75"] # Blue
    _M90 = bpy.data.materials["Material_.9"] # Yellow
    #_MDEF = bpy.data.materials["249__DEFAULT_MAT"] # Created during material conversion process, grey
    _ObjectDetails = collections.namedtuple(
        "_ObjectDetails",
        ["new_name",
        "mat_name",]
        )

    # Tuple of list of objectnames to a dictionary of TF group types ("TILE", "SHADOW", "DEFAULT", "NONE") and
    # what specularity/diffuse RGB material found to be used for it further code will check that Material
    # not only the specualrty and Diffuse RGB are correct but that the correct dirivative copy is made from it
    # material properties

    #TODO: Currently these dictionaries simply test the faces exist, but they aren't testing the specific faces
    # still have their specific materials
    #  ___________.__________       ___________.___________
    # | Blue Tile | Red Tile | ==  | Red Tile  | Blue Tile |
    #  -----------.-----------      -----------.-----------
    #
    # We needed OrderedDicts (until Python 3.7, sigh), and have the order correspond to specific faces
    _after_report = OrderedDict((# 1face_tests
        ("1face_0mat_0tf", {"NONE" :_MDEF}),
        ("1face_0mat_1tf", {"TILES":_MDEF}),
        ("1face_1mat_0tf", {"NONE" :_M25}),
        ("1face_1mat_1tf", {"TILES":_M25}),

        # 2face_tests
        ("2face_0mat_0tf", {"NONE" :_MDEF}),
        ("2face_0mat_2tf", {"TILES"  :_MDEF,
                            "DYNAMIC":_MDEF}),

        ("2face_1mat_0tf", {"NONE":_M25}),
        ("2face_1mat_2tf", {"TILES"  :_M25,
                            "DYNAMIC":_M25}),

        ("2face_2mat_0tf", {"NONE":(_M75, _M25)}), # Thanks to not splitting, we need to test
        # the EXACT material slot layout. TODO: What if they have an empty slot? How does it affect our algorithm?

        ("2face_2mat_2tf", {"TILES"  :_M25,
                            "DYNAMIC":_M75}),

        # 3test_faces
        ("3face_3mat_2tf_2used", {"TILES":_M25,
                                  "DYNAMIC":(_M25, _M75)}),

        # 4test_faces
        ("4face_3mat_1tf", {"DYNAMIC": (_M25, _M25, _M75, _M90)}),
        ("4face_3mat_2tf", {"TILES": (_M25, _M25), "SHADOW": (_M75,_M90)}),
        ("4face_3mat_3tf_1as", {"NONE": (_MDEF, _MDEF, _MDEF), "SHADOW": _M90}),
        )
    )

    def _check_object(self, name):
        for num in max(1, re.match("(\dtf)", name).group(0)):
            obj = bpy.data.objects[name+"_"+str(num)] #TODO: If we change "prepend _n to split groups", change this too

            # We don't have to worry about empty slots. Right? see above TODO
            # If an object has empty slots it can only mean it wasn't split. The only one that gets that treatment
            material_slots = [slot for slot in obj.material_slots if slot.link == "DATA"]
            mat = material_slots[0].material
            # Did the material end up with draped? Must have been "TILES" (we hope!)
            def cmp_mat(obj, name, tf_mode_type):#, test_mat, generated_mat):
                for i, face in enumerate(obj.data.polygons):
                    self.assertEqual(
                            self._after_report[name][tf_mode_type][i].material.specular_intensity,
                            material_slots[face.material_index].material.specular_intensity
                        )

                    self.assertEqual(
                            self._after_report[name][tf_mode_type][i].material.diffuse_rgb,
                            material_slots[face.material_index].material.diffuse_rgb
                        )

            if mat.xplane.draped:
                cmp_mat(obj, name, "TILES")
            elif mat.xplane.solid_camera:
                cmp_mat(obj, name, "DYNAMIC"), #gonnahave to changethis one
            elif mat.xplane.shadow_local:
                cmp_mat(obj, name, "SHADOW")
            else:
                cmp_mat(obj, name, "NONE")


    def test_fewest_materials_made(self):
        # NONE (aka reuse base materials): MDEF, M25
        # UNUSED Base Materials: M75, M90
        #
        # Derivative Materials
        # TILES: MDEF, M25
        # DYNAMIC: MDEF, M25, M75, M90
        # SHADOW: M75, M90
        # Total: 12
        self.assertEqual(len(bpy.data.materials), 12)

    #TI as per unittest requirements, all test methods must start
    #TI with "test_"
    def test_fixture_or_layer_name_snake_case(self):
        #TI Example of whitebox testing
        #from io_xplane2blender.xplane_types import xplane_
        #access object using bpy.data.objects
        # use constructor for xplane_type, use methods
        #TI
        #TI Testing the results of an export without a fixture
        #out = self.exportLayer(0)

        #TI Example of expecting a failure
        #self.assertLoggerErrors(1)

        #TI Test layer against fixture
        # Note, I would recommend layout out your layers, tests, and names so they are all in order.
        # It makes everything much easier
        #
        #filename = inspect.stack()[0].function

        #self.assertLayerExportEqualsFixture(
        #    0,
        #    os.path.join(__dirname__, "fixtures", filename + ".obj"),
        #    filename,
        #    filterLines
        #)
        #self.assertRootObjectExportEqualsFixture(
        #    bpy.data.objects[filename[5:]],
        #    os.path.join(__dirname__, "fixtures", filename + ".obj"),
        #    filename,
        #    filterLines
        #)
        pass

#TI Class name above
runTestCases([TestMeshesSplitMaterialsCopied])
