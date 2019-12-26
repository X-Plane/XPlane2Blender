import itertools
import inspect

from typing import Any, Dict, Tuple
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_helpers
from io_xplane2blender.xplane_props import XPlaneLayer
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)


class TestLayersToCollections(XPlaneTestCase):
    def assertXPlaneLayerEqual(self, xplane_layer:XPlaneLayer, correct_values:Dict[str,Any]):
        """
        Assert every value of an XPlaneLayer equals some value from
        correct_values. correct_values' keys must match XPlaneLayer's
        properties' identifiers

        Each value is tested per type, floats are tested wtih assertFloatAlmostEqual
        """
        assert (set(xplane_layer.bl_rna.properties.keys()) - {"rna_type", "index", "expanded"}) == correct_values.keys(), "correct_values's keys do not equal XPlaneLayer's properties"

        def assert_prop(prop_id:str, real_value:Union[bool, float, int, str], correct_value:Union[bool, float, int, str])->None:
            if isinstance(real_value, (bool, int, str)):
                self.assertEqual(real_value, correct_value, msg=f"'{prop_id}' real vs correct: {real_value} != {correct_value}")
            elif isinstance(real_value, float):
                self.assertAlmostEqual(real_value, correct_value, msg=f"'{prop_id}' real vs correct: {real_value} != {correct_value}")
            else:
                assert False, f"{real_value} is an unknown type {type(real_value)}"

        def assert_recursive(real_prop_group:bpy.types.PropertyGroup, correct_values):
            for prop in [prop for prop in real_prop_group.bl_rna.properties if prop.identifier not in {"rna_type", "index", "expanded"}]:
                if prop.type == "COLLECTION":
                    for collection_member, collection_value in zip(getattr(real_prop_group, prop.identifier), correct_values[prop.identifier]):
                        assert_recursive(collection_member, collection_value)
                else:
                    if prop.identifier == "name" and not isinstance(real_prop_group, XPlaneLayer):
                        continue
                    layer_value = getattr(real_prop_group, prop.identifier)
                    correct_value = correct_values[prop.identifier]
                    assert_prop(prop.identifier, layer_value, correct_value)
        assert_recursive(xplane_layer, correct_values)


    def get_default_xplane_layer_props_dict(self) -> Dict[str, Any]:
        defaults = {
            prop.identifier: prop.default
            for prop in XPlaneLayer.bl_rna.properties
            if prop.identifier not in {"rna_type", "index", "expanded"} and prop.type != "COLLECTION"
        }
        defaults["cockpit_region"] = [{"expanded":False, "top":0, "left":0,"width":1, "height":1}] * 4
        defaults["customAttributes"]= []
        defaults["export_path_directives"] = []
        defaults["lod"] = [{"expanded":False, "near":0, "far":0}]
        return defaults

    def test_collections_renamed(self)->None:
        # Also tests that collections 'Layer 1', 'Layer 3-8' are the only collections in the .blend file
        self.assertSetEqual({c.name for c in bpy.data.scenes["Scene_first"].collection.children},
                            {f"Layer {i}_Scene_first" for i in itertools.chain([1], range(3,9))})
        self.assertSetEqual({c.name for c in bpy.data.scenes["Scene_second_copy"].collection.children},
                            {f"Layer {i}_Scene_second_copy" for i in itertools.chain([1], range(3,11))})
        self.assertEqual(bpy.data.scenes["Scene_fourth"].collection.children[0].name, "Layer 10_Scene_fourth")

    def test_is_exportable_is_not_hide_render(self)->None:
        self.assertTrue(bpy.data.collections["Layer 1_Scene_first"].xplane.is_exportable_collection)
        for i in range(3, 9):
            self.assertFalse(bpy.data.collections[f"Layer {i}_Scene_first"].xplane.is_exportable_collection)

    def test_layer_4_properties_copied(self)->None:
        layer_first = bpy.data.collections["Layer 4_Scene_first"].xplane.layer
        layer_second_only = bpy.data.collections["Layer 4_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({"name":"found_non_default_choice (this name)"})
        self.assertXPlaneLayerEqual(layer_first, d)
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_5_properties_copied(self)->None:
        layer_first = bpy.data.collections["Layer 5_Scene_first"].xplane.layer
        layer_second_only = bpy.data.collections["Layer 5_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "aircraft_properties_copied",
            "export_type": "aircraft",
            "autodetectTextures": False,
            "texture": "tex",
            "texture_lit": "tex_LIT",
            "texture_normal": "tex_NML",
            "particle_system_file": "some_particle_system",
            "slungLoadWeight": 10.0,
            "export": False,
            "debug": False
        })
        self.assertXPlaneLayerEqual(layer_first, d)
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_6_properties_copied(self)->None:
        layer_first = bpy.data.collections["Layer 6_Scene_first"].xplane.layer
        layer_second_only = bpy.data.collections["Layer 6_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "cockpit_properties_copied",
            "export_type": "cockpit",
            "cockpit_regions": "2",

            "cockpit_region": [
                {
                    "left": 12,
                    "top": 12,  #GRRRRR, this is supposed to be top. See #416
                    "width": 2,
                    "height": 6
                },
                {
                    "left": 13,
                    "top": 13,  #GRRRRR, this is supposed to be top. See #416
                    "width": 3,
                    "height": 7
                },
                {
                    "left": 0,
                    "top": 0,  #GRRRRR, this is supposed to be top. See #416
                    "width": 1,
                    "height": 1
                },
                {
                    "left": 0,
                    "top": 0,  #GRRRRR, this is supposed to be top. See #416
                    "width": 1,
                    "height": 1
                }
            ]
        })
        self.assertXPlaneLayerEqual(layer_first, d)
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_7_properties_copied(self)->None:
        layer_first = bpy.data.collections["Layer 7_Scene_first"].xplane.layer
        layer_second_only = bpy.data.collections["Layer 7_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "scenery_properties_copied",
            "export_type": "scenery",
            "lods": "4",
            "lod": [
                {
                    "near": 0,
                    "far": 100
                },
                {
                    "near": 100,
                    "far": 200
                },
                {
                    "near": 200,
                    "far": 300
                },
                {
                    "near": 300,
                    "far": 400
                },
            ],
            "lod_draped": 0.30,
            "layer_group": "terrain",
            "layer_group_offset": 5,
            "layer_group_draped": "shoulders",
            "layer_group_draped_offset": -5,
            "slope_limit": True,
            "slope_limit_min_pitch": -10.0,
            "slope_limit_max_pitch": 11.0,
            "slope_limit_min_roll": -12.0,
            "slope_limit_max_roll": 13.0,
            "tilted": True,
            "require_surface": "dry",
        })
        self.assertXPlaneLayerEqual(layer_first, d)
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_8_properties_copied(self)->None:
        layer_first = bpy.data.collections["Layer 8_Scene_first"].xplane.layer
        layer_second_only = bpy.data.collections["Layer 8_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "instanced_scenery_properties_copied",
            "export_type": "instanced_scenery",
            "export_path_directives": [
                {"export_path": "export_path_directive_1"},
                {"export_path": "export_path_directive_2"}
            ],
            "customAttributes": [
                {"name": "name1", "value": "value1"},
                {"name": "name2", "value": "value2"}
            ]
        })
        self.assertXPlaneLayerEqual(layer_first, d)
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_9_properties_copied(self)->None:
        layer_second_only = bpy.data.collections["Layer 9_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "second_scene_only_has_nondefault",
        })
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_10_properties_copied(self)->None:
        layer_second_only = bpy.data.collections["Layer 10_Scene_second_copy"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "layer_10_content_in_Scene_second_copy",
        })
        self.assertXPlaneLayerEqual(layer_second_only, d)

    def test_layer_10_in_Scene_fourth_copied(self)->None:
        layer_fourth = bpy.data.collections["Layer 10_Scene_fourth"].xplane.layer
        d = self.get_default_xplane_layer_props_dict()
        d.update({
            "name": "layer_10_content_in_Scene_fourth",
        })
        self.assertXPlaneLayerEqual(layer_fourth, d)
runTestCases([TestLayersToCollections])
