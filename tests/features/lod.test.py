"""
Test layout and explanation

Buckets 0, 200
      200, 400
      400, 600
      600, 800

N = No check boxes
[] = An Exported Cube
                            N   1  2  3  4
layer 5, defines 4  buckets [] [] [] [] []
layer 4, defines 3  buckets [] [] [] []
layer 3, defines 2  buckets [] [] []
layer 2, defines 1  buckets [] []
layer 1, defines no buckets
"""

import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_constants import MAX_LODS
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

REAL_LOD_BUCKETS = MAX_LODS - 1
MAX_XPLANE_LAYERS = 5
LOD_VAL_INCREMENT = 200

#TODO: This horribly stupid unit test is a time suck.
# I recommend simply praying you don't have to ever have to make this stupid function work
# Lesson learned: You ain't going to need it
"""
def create_test_cubes():
    '''Creates the test blender file programmatically, an trophy shape cut in half with cubes placed in different layers in different buckets'''

    test_creation_helpers.create_initial_test_setup()
    scene = bpy.data.scenes[0]

    #####################
    # Set Scene Options #
    #####################
    scene.xplane.version = "1050"
    scene.xplane.debug = True

    ########################
    # Setup X-Plane layers #
    ########################
    [test_creation_helpers.create_datablock_collection(f"Layer {i}", scene) for i in range(1, MAX_XPLANE_LAYERS)]
    LOD_N_F_PAIRS = [(LOD_VAL_INCREMENT * i, LOD_VAL_INCREMENT * i + LOD_VAL_INCREMENT) for i in range(0, REAL_LOD_BUCKETS)]
    for layer_index, layer in enumerate((coll.xplane.layer for coll in scene.collection.children), start=1):
        print("layer_index: " + str(layer_index))

        if layer_index == 0:
            layer.name = "layer_1_no_lods"
        else:
            lod_val_far_str = ((layer_index - 1) * LOD_VAL_INCREMENT) + LOD_VAL_INCREMENT
            #layer_i+1_LOD-near_LOD-far (increments of 200)
            layer.name = "layer_%i_%i_%i" % (layer_index + 1, 0, lod_val_far_str)

        layer.export_type = "instanced_scenery"

        #The number of lods in this layer
        layer.lods = str(layer_index)

        #The collection of actual lods with their near and far
        if layer_index > 0:
            for i in range(len(layer.lod)):
                layer.lod[i].near = LOD_N_F_PAIRS[i][0] #  0, 200, 400...
                layer.lod[i].far = LOD_N_F_PAIRS[i][1] #200, 400, 600...
                print(str(layer.lod[i].near) + "," + str(layer.lod[i].far))

        ###########################
        # Create group of objects #
        ###########################
        num_cubes = layer_index if layer_index else REAL_LOD_BUCKETS
        for i in range(0, num_cubes + 1):
            current_cube = test_creation_helpers.create_datablock_mesh(
                test_creation_helpers.DatablockInfo(
                    datablock_type="MESH",
                    name=f"Cube_l{layer_index + 1}_{i}_{num_cubes}",
                    location=(i * 5, 0, layer_index * 5),
                    collection=f"Layer {layer_index}"))
            if layer_index > 0:
                current_cube.xplane.lod[0:i] = [True] * i

#Use this to perfectly recreate the initial test
create_test_cubes()
"""

class TestLODs(XPlaneTestCase):
    def test_lods_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('POINT_COUNTS') == 0 or \
                    line[0].find('ATTR_LOD')     == 0 or \
                    line[0].find('TRIS')         == 0)


        for layer_idx in range(0,MAX_XPLANE_LAYERS):
            filename = "test_lod_layer_" + str(layer_idx + 1)
            self.assertLayerExportEqualsFixture(
                layer_idx,
                os.path.join(__dirname__, 'fixtures', filename + '.obj'),
                filterLines,
                filename,
            )

runTestCases([TestLODs])
