"""
Test layout and explanation

Buckets 0, 200
      200, 400
      400, 600
      600, 800

N = No check boxes

                            N   1  2  3  4
layer 5, defines 4  buckets [] [] [] [] []
layer 4, defines 3  buckets [] [] [] []
layer 3, defines 2  buckets [] [] []
layer 2, defines 1  buckets [] []
layer 1, defines no buckets [] [] [] [] []
"""

import bpy
import os
import sys
from io_xplane2blender import xplane_constants
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

LOD_VAL_INCREMENT = 200

def make_cubes(current_layer, layer_index, current_scene):
    """Make cubes for the current layer in setting up the test,"""
    layers_array = [False] * 20
    layers_array[layer_index] = True

    num_cubes = 0
    if layer_index == 0:
        num_cubes = REAL_LOD_BUCKETS
    else:
        num_cubes = layer_index


    print("num_cubes: " + str(num_cubes))
    for i in range(0, num_cubes + 1):
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

    test_creation_helpers.delete_everything()
    test_creation_helpers.create_material_default()

    scene = bpy.context.scene

    #####################
    # Set Scene Options #
    #####################
    scene.xplane.optimize = True
    scene.xplane.debug = True

    ########################
    # Setup X-Plane layers #
    ########################
    scene.xplane.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

    root_objects = [] # type: bpy.types.Object
    for num_lod_buckets in range(xplane_constants.MAX_LODS):
        near = num_lod_buckets * LOD_VAL_INCREMENT
        far = near + LOD_VAL_INCREMENT
        if num_lod_buckets == 0:
            # Root object names are in the form of Root_{# lods}_0_{far}
            root_object_name = "Root_none"
        else:
            root_object_name = "Root_{}_{}_{}".format(num_lod_buckets, 0, num_lod_buckets * LOD_VAL_INCREMENT)

        root_object_db_info = test_creation_helpers.DatablockInfo('EMPTY', root_object_name)
        root_object = test_creation_helpers.create_datablock_empty(root_object_db_info)
        root_object.xplane.isExportableRoot = True
        for idx in range(xplane_constants.MAX_LODS):
            lod = root_object.xplane.layer.lod.add()
            lod.near = idx * LOD_VAL_INCREMENT
            lod.far = lod.near + LOD_VAL_INCREMENT

        layer = root_object.xplane.layer
        layer.name = "test_lod_" + root_object_name
        layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
        layer.lods = str(num_lod_buckets)

        if num_lod_buckets == 0:
            num_cubes = range(xplane_constants.MAX_LODS)
        else:
            num_cubes = range(num_lod_buckets+1)

        for cube_idx in num_cubes:
            ob = test_creation_helpers.create_datablock_mesh(
                    test_creation_helpers.DatablockInfo(datablock_type="MESH",
                                                        name="l{}_{}".format(cube_idx,num_lod_buckets) if num_lod_buckets != 0 else "lnone_none",
                                                        parent_info=test_creation_helpers.ParentInfo(parent=root_object),
                                                        location=(cube_idx * 5, 0, num_lod_buckets * 5)))
            print("Buckets %d" % num_lod_buckets)
            print("Cube idx %d" % cube_idx)
            if num_lod_buckets > 0:
                for j in range(cube_idx):
                    ob.xplane.lod[j] = True



'''

    #For all xplane layers
    for layer in scene.xplane.layers[:MAX_XPLANE_LAYERS]:
        print("layer_index: " + str(layer_index))

        #The collection of actual lods with their near and far
        if layer_index > 0:
            for i in range(len(layer.lod)):
                layer.lod[i].near = LOD_N_F_PAIRS[i][0] #  0, 200, 400...
                layer.lod[i].far = LOD_N_F_PAIRS[i][1] #200, 400, 600...
                print(str(layer.lod[i].near) + "," + str(layer.lod[i].far))

        ###########################
        # Create group of objects #
        ###########################
        #blender_layer = scene.layers[layer_index]
        make_cubes(layer, layer_index, scene)

        # Make layer visible
        scene.layers[layer_index] = True
        layer_index += 1
'''

#Use this to perfectly recreate the initial test
create_test_cubes()

class TestRootLODs(XPlaneTestCase):
    def test_lods_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   (line[0].find('POINT_COUNTS') == 0 or \
                    line[0].find('ATTR_LOD')     == 0 or \
                    line[0].find('TRIS')         == 0)


        for layer_idx in range(0,xplane_constants.MAX_LODS):
            filename = "test_lod_root_" + str(layer_idx + 1)
            self.assertLayerExportEqualsFixture(
                layer_idx,
                os.path.join(__dirname__, 'fixtures', filename + '.obj'),
                filename,
                filterLines)

runTestCases([TestRootLODs])
