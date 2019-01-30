"""
Test layout and explanation

Bucket | Near | Far
-------|------|----
1. | 0   | 200
2. | 200 | 400
3. | 400 | 600
4. | 600 | 800

N = No check boxes

                            N   1  2  3  4
layer 5, defines 4  buckets [] [] [] [] []
layer 4, defines 3  buckets [] [] [] []
layer 3, defines 2  buckets [] [] []
layer 2, defines 1  buckets [] []
layer 1, None, always seen  [] [] [] [] []
"""

import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

MAX_LODS = 5
REAL_LOD_BUCKETS = MAX_LODS - 1
MAX_XPLANE_LAYERS = 5
LOD_VAL_INCREMENT = 200
LOD_N_F_PAIRS = []

def make_lod_near_far_pairs():
    ''' Makes the LOD near and fair pairs, initializing this test's LOD_N_F_PAIRS'''
    for i in range(0,REAL_LOD_BUCKETS):
        n = LOD_VAL_INCREMENT * i
        f = n + LOD_VAL_INCREMENT
        LOD_N_F_PAIRS.append((n, f))

make_lod_near_far_pairs()

def make_cubes(current_layer, layer_index, current_scene):
    """Make cubes for the current layer in setting up the test,"""
    layers_array = [False] * 20
    layers_array[layer_index] = True

    num_cubes = 0
    if layer_index == 0:
        num_cubes = REAL_LOD_BUCKETS
    else:
        num_cubes = layer_index

    #print("num_cubes: " + str(num_cubes))
    for i in range(num_cubes + 1):
        #Add cube mesh at place in mesh
        bpy.ops.mesh.primitive_cube_add(location=(i*5,0,layer_index*5),layers=layers_array)

        #Set the current cube the last added object in the scene, choose a material, and name it
        current_cube = current_scene.objects[0]
        current_cube.data.materials.append(bpy.data.materials['Material'])
        current_cube.name = "Cube_" + ("l%i_%i_%i" % (layer_index + 1,i,num_cubes))

        if layer_index > 0:
            current_cube.xplane.lod[0:i] = [True]*i

def create_test_cubes():
    """Creates the test blender file programmatically, an trophy shape cut in half with cubes placed in different layers in different buckets"""

    #For now, delete everything by hand if needed
    # delete all existing objects
    bpy.ops.object.select_all(action="SELECT")
    for blender_obj in bpy.data.objects:
        bpy.data.objects.remove(blender_obj, do_unlink=True)

    scene = bpy.data.scenes[0]

    if len(scene.xplane.layers) == 0:
        bpy.ops.scene.add_xplane_layers()

    #####################
    # Set Scene Options #
    #####################
    scene.xplane.version = '1050'
    scene.xplane.optimize = True    
    scene.xplane.debug = True    

    ################################
    # Material and Texture Options #
    ################################
    bpy.data.materials["Material"].texture_slots['Tex'].texture_coords = 'UV'
    
    ########################
    # Setup X-Plane layers #
    ########################
    scene.xplane.exportMode = 'layers'

    layer_index = 0
    #For all xplane layers
    for layer in scene.xplane.layers[:MAX_XPLANE_LAYERS]:
        #print("layer_index: " + str(layer_index))

        if layer_index == 0:
            layer.name = "test_layer_1_no_lods"
        else:
            lod_val_far_str = ((layer_index - 1) * LOD_VAL_INCREMENT) + LOD_VAL_INCREMENT
            #layer_i+1_LOD-near_LOD-far (increments of 200)
            layer.name = "test_layer_%i_%i_%i" % (layer_index + 1, 0, lod_val_far_str)

        layer.export_type = "instanced_scenery"

        #The number of lods in this layer
        layer.lods = str(layer_index)

        #The collection of actual lods with their near and far
        if layer_index > 0:
            for i in range(len(layer.lod)):
                layer.lod[i].near = LOD_N_F_PAIRS[i][0] #  0, 200, 400... 
                layer.lod[i].far = LOD_N_F_PAIRS[i][1] #200, 400, 600... 
                #print(str(layer.lod[i].near) + "," + str(layer.lod[i].far))

        ###########################
        # Create group of objects #
        ###########################
        #blender_layer = scene.layers[layer_index]
        make_cubes(layer, layer_index, scene)

        # Make layer visible
        scene.layers[layer_index] = True
        layer_index += 1

#Use this to perfectly recreate the initial test
#create_test_cubes()

class TestLODs(XPlaneTestCase):
    def test_lods_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('POINT_COUNTS') == 0 or \
                    line[0].find('ATTR_LOD')     == 0 or \
                    line[0].find('TRIS')         == 0)
                   
        for layer_idx in range(MAX_XPLANE_LAYERS):
            if layer_idx == 0:
                filename = "test_layer_1_no_lods"
            else:
                lod_val_far_str = ((layer_idx - 1) * LOD_VAL_INCREMENT) + LOD_VAL_INCREMENT
                filename = "test_layer_%i_%i_%i" % (layer_idx + 1, 0, lod_val_far_str)
            #print(filename)

            self.assertLayerExportEqualsFixture(
                layer_idx,
                os.path.join(__dirname__, 'fixtures', filename + '.obj'),
                filename,
                filterLines)

runTestCases([TestLODs])
