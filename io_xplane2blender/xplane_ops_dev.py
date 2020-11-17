# File: xplane_ops_dev.py
# Defines Operators specifically for plugin development

import os
import re
from collections import OrderedDict

import bpy

import io_xplane2blender
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_utils import xplane_lights_txt_parser


class SCENE_OT_dev_apply_default_material_to_all(bpy.types.Operator):
    bl_label = "Apply the 'Material' datablock to all objects"
    bl_idname = "scene.dev_apply_default_material_to_all"
    bl_description = "Applies the 'Material' datablock to all without a material. If 'Material' does not exist, it will be created"

    def execute(self, context):
        mat = test_creation_helpers.create_material_default()
        for obj in bpy.data.objects:
            try:
                if not obj.data.materials:
                    obj.data.materials.append(mat)
                elif not obj.material_slots[0].material:
                    obj.material_slots[0].material = mat
            except:
                pass
        return {"FINISHED"}


class SCENE_OT_dev_create_lights_txt_summary(bpy.types.Operator):
    bl_label = "Create lights.txt Summary"
    bl_idname = "scene.dev_create_lights_txt_summary"
    bl_description = (
        "Create a text block listing all known lights and attributes about them"
    )

    def execute(self, context):
        xplane_lights_txt_parser.parse_lights_file()
        # Use an internal text file called "Manipulator Type Differeces
        filename = "lights.txt Summary"
        if bpy.data.texts.find(filename) == -1:
            text_file = bpy.data.texts.new(filename)
        else:
            text_file = bpy.data.texts[filename]
            text_file.clear()

        content = xplane_lights_txt_parser._parsed_lights_txt_content
        named_lights = [
            parsed_light
            for light_name, parsed_light in content.items()
            if not parsed_light.light_param_def
        ]
        param_lights = [
            parsed_light
            for light_name, parsed_light in content.items()
            if parsed_light.light_param_def
            and "SPILL_GND" not in parsed_light.overloads[0].overload_type
        ]
        other_lights = [
            parsed_light
            for light_name, parsed_light in content.items()
            if not parsed_light.light_param_def
            and "SPILL_GND" in parsed_light.overloads[0].overload_type
        ]

        text_file.write("Named Lights\n")
        text_file.write("------------\n")
        for named_light in named_lights:
            text_file.write("%s\n" % named_light.name)

        text_file.write(
            "\nParam Lights (Light name, followed by parameters required)\n"
        )
        text_file.write("------------\n")
        for param_light in param_lights:
            text_file.write(
                "%s\n%s\n\n" % (param_light.name, " ".join(param_light.light_param_def))
            )

        text_file.write("Old X-Plane 8 Lights\n")
        text_file.write("------------\n")
        for other_light in other_lights:
            text_file.write("%s\n" % other_light.name)

        return {"FINISHED"}


class SCENE_OT_dev_root_names_from_objects(bpy.types.Operator):
    bl_label = "Create Fixture Names From Roots"
    bl_idname = "scene.dev_root_names_from_objects"
    bl_description = (
        "Changes each exportable root's Name property to 'test_' + root.name"
    )

    name_prefix = "test_"

    def execute(self, context: bpy.types.Context):
        for root in xplane_helpers.get_exportable_roots_in_scene(
            context.scene, context.view_layer
        ):
            root.xplane.layer.name = self.name_prefix + root.name
        return {"FINISHED"}


class SCENE_OT_dev_rerun_updater(bpy.types.Operator):
    bl_label = "Re-run Updater"
    bl_idname = "scene.dev_rerun_updater"
    bl_description = (
        "Re-runs the updater. This does not undo an update that happened on load!"
    )

    def execute(self, context):
        logger = xplane_helpers.logger
        logger.clear()
        logger.addTransport(
            xplane_helpers.XPlaneLogger.InternalTextTransport("Updater Log")
        )
        logger.addTransport(xplane_helpers.XPlaneLogger.ConsoleTransport())

        fake_version_str = bpy.context.scene.xplane.dev_fake_xplane2blender_version
        io_xplane2blender.xplane_updater.update(
            xplane_helpers.VerStruct.parse_version(fake_version_str), logger
        )
        return {"FINISHED"}


_ops_dev = (
    SCENE_OT_dev_apply_default_material_to_all,
    SCENE_OT_dev_create_lights_txt_summary,
    SCENE_OT_dev_root_names_from_objects,
    SCENE_OT_dev_rerun_updater,
)

register, unregister = bpy.utils.register_classes_factory(_ops_dev)
