import bpy
import bpy_types
import os
from io_xplane2blender.tests import *

def create_partial_test_env(self):
    C = bpy.context
    D = bpy.data
    if len(D.objects) == 0:
        for i in range(0,8):
            bpy.ops.mesh.primitive_cube_add()

    template_str = "Cube_%s_%d_mat_%s"

    idx = 0

    for cube in D.objects:
        cube.name = ""

    blank_layers = [False] * 20

    norm_or_none = "none"
    D.objects[idx].name = template_str % (norm_or_none, 1, "inst"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 2, "inst"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 1, "scen"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 2, "scen"); idx += 1

    norm_or_none = "norm"
    D.objects[idx].name = template_str % (norm_or_none, 1, "inst"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 2, "inst"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 1, "scen"); idx += 1
    D.objects[idx].name = template_str % (norm_or_none, 2, "scen"); idx += 1


    layer_index = 0
    for cube in sorted(D.objects.keys()):
        layers_array = [False] * 20
        layers_array[layer_index] = True
        D.objects[cube].layers = layers_array
        layer_index += 1

    #bpy.ops.scene.dev_layer_names_to_current_dir()

#create_partial_test_env()

__dirname__ = os.path.dirname(__file__)

#There is a small chance that this filterLines function looks for more than it needs to, but that could only create (unlikely) false negatives, not false positives.
def filterLines(line):
    return isinstance(line[0],str) and (line[0].find('ATTR_draped')      == 0 or \
                                        line[0].find('ATTR_no_draped')   == 0 or \
                                        line[0].find('ATTR_shiney_rat')  == 0 or \
                                        line[0].find('GLOBAL_specular')  == 0 or \
                                        line[0].find('NORMAL_METALNESS') == 0 or \
                                        line[0].find('TEXTURE')          == 0 or \
                                        line[0].find('TEXTURE_DRAPED')   == 0 or \
                                        line[0].find('TEXTURE_NORMAL')   == 0)

class TestNormMetSpec(XPlaneTestCase):
    def test_none_1_mat_inst(self):
        filename = "test_none_1_mat_inst"
        self.assertLayerExportEqualsFixture(
            0, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_none_1_mat_scen(self):
        filename = "test_none_1_mat_scen"
        self.assertLayerExportEqualsFixture(
            1, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_none_2_mat_inst(self):
        out = self.exportLayer(2)
        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()

    def test_none_2_mat_scen(self):
        filename = "test_none_2_mat_scen"
        self.assertLayerExportEqualsFixture(
            3, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_norm_1_mat_inst(self):
        filename = "test_norm_1_mat_inst"
        self.assertLayerExportEqualsFixture(
            4, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_norm_1_mat_scen(self):
        filename = "test_norm_1_mat_scen"
        self.assertLayerExportEqualsFixture(
            5, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_norm_2_mat_inst(self):
        filename = "test_norm_2_mat_inst"
        self.assertLayerExportEqualsFixture(
            6, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

    def test_norm_2_mat_scen(self):
        filename = "test_norm_2_mat_scen"
        self.assertLayerExportEqualsFixture(
            7, make_fixture_path(__dirname__,filename,sub_dir="norm_met_spec"),
            filename,
            filterLines
        )

runTestCases([TestNormMetSpec])
