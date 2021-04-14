import pathlib
import shutil
from typing import Optional

import bpy

from io_xplane2blender import xplane_props
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_constants import MAX_COCKPIT_REGIONS, MAX_LODS
from io_xplane2blender.xplane_ops_dev import *
from io_xplane2blender.xplane_utils import (
    xplane_commands_txt_parser,
    xplane_datarefs_txt_parser,
    xplane_wiper_gradient,
)


# Function: findFCurveByPath
# Helper function to find an FCurve by an data-path.
#
# Parameters:
#   list - FCurves
#   string - data path.
#
# Returns:
#   FCurve or None if no FCurve could be found.
def findFCurveByPath(fcurves, path):
    i = 0
    fcurve = None

    # find fcurve
    while i < len(fcurves):
        if fcurves[i].data_path == path:
            fcurve = fcurves[i]
            i = len(fcurves)
        i += 1
    return fcurve


# Function: makeKeyframesLinear
# Sets interpolation mode of keyframes to linear.
#
# Parameters:
#   obj - Blender object
#   string path - data path.
#
# Todos:
#   - not working
def makeKeyframesLinear(obj, path):
    fcurve = None

    if (
        obj.animation_data != None
        and obj.animation_data.action != None
        and len(obj.animation_data.action.fcurves) > 0
    ):
        fcurve = findFCurveByPath(obj.animation_data.action.fcurves, path)

        if fcurve:
            # find keyframe
            keyframe = None
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = "LINEAR"


# Function: getDatarefValuePath
# Returns the data path for a <XPlaneDataref> value.
#
# Parameters:
#   int index - Index of the <XPlaneDataref>
#
# Returns:
#   string - data path
def getDatarefValuePath(index: int, bone: Optional[bpy.types.Bone] = None) -> str:
    """
    Returns the keyframe data path for an XPlaneDataref value on a bone or object"

    index is tied with the remove_xplane_dataref operator.
    """

    if bone:
        return 'bones["%s"].xplane.datarefs[%d].value' % (bone.name, index)
    else:
        return "xplane.datarefs[" + str(index) + "].value"


# This code is based off of Christian Brinkmann (p2or)
# and Janne Karhu (jahka)'s "Sequency Bakery" Addon. It is also released under
# the same GPL license as XPlane2Blender
class XPLANE_OT_render_bake_xp(bpy.types.Operator):
    bl_label = "Make Wiper Gradient Texture"
    bl_idname = "xplane.render_bake_xp"
    bl_description = "Makes the Wiper Gradient Texture from the Rain Settings of the active collection (may take more than 30 minutes)"

    def execute(self, context):
        # TODO: Automate making the nodes set up?

        is_cycles = context.scene.render.engine == "CYCLES"
        scene = context.scene

        debug_skip_bake = False
        start, end = 1, 250
        slots = [1, 2, 3, 4]

        rain = bpy.context.collection.xplane.layer.rain
        try:
            windshield = bpy.data.objects[rain.wiper_ext_glass_object]
        except KeyError:
            if rain.wiper_ext_glass_object:
                msg = f"Cannot find objected used for exterior glass '{rain.wiper_ext_glass_object}'. Check your spelling."
            else:
                msg = f"Must have object name for exterior glass to bake"

            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        def find_baking_image(bake_object: bpy.types.Object):
            img = None

            # find the image that's used for rendering
            if is_cycles:
                # XXX This tries to mimic nodeGetActiveTexture(), but we have no access to 'texture_active' state from RNA...
                #     IMHO, this should be a func in RNA nodetree struct anyway?
                inactive = None
                selected = None
                for mat_slot in bake_object.material_slots:
                    mat = mat_slot.material
                    if not mat or not mat.node_tree:
                        continue
                    trees = [mat.node_tree]
                    while trees and not img:
                        tree = trees.pop()
                        node = tree.nodes.active
                        if node.type in {"TEX_IMAGE", "TEX_ENVIRONMENT"}:
                            img = node.image
                            break
                        for node in tree.nodes:
                            if (
                                node.type in {"TEX_IMAGE", "TEX_ENVIRONMENT"}
                                and node.image
                            ):
                                if node.select:
                                    if not selected:
                                        selected = node
                                else:
                                    if not inactive:
                                        inactive = node
                            elif node.type == "GROUP":
                                trees.add(node.node_tree)
                    if img:
                        break
                if not img:
                    if selected:
                        img = selected.image
                    elif inactive:
                        img = inactive.image
            else:
                for uvtex in bake_object.data.uv_textures:
                    if uvtex.active_render == True:
                        for uvdata in uvtex.data:
                            if uvdata.image is not None:
                                img = uvdata.image
                                break
            return img

        # --- Errors with what you're trying to bake --------------------------
        # Only single object baking for now
        if windshield.type != "MESH":
            self.report({"ERROR"}, "The baked object must be a mesh object")
            return {"CANCELLED"}

        if windshield.mode == "EDIT":
            self.report({"ERROR"}, "Can't bake in edit-mode")
            return {"CANCELLED"}
        # ---------------------------------------------------------------------
        img = find_baking_image(windshield)
        # --- Errors with the bake image --------------------------------------
        if img is None:
            self.report({"ERROR"}, "No valid image found to bake to")
            return {"CANCELLED"}

        if img.is_dirty:
            self.report({"ERROR"}, "Save the image that's used for baking before use")
            return {"CANCELLED"}

        if img.packed_file is not None:
            # TODO: Why? Autopack messed me up
            self.report({"ERROR"}, "Can't animation-bake packed file")
            return {"CANCELLED"}
        # ---------------------------------------------------------------------

        def select_objects(slot: int) -> None:
            for obj in bpy.context.selected_objects:
                obj.select_set(False)

            try:
                object_name = getattr(rain, f"wiper_{slot}").object_name
                object_datablock = bpy.data.objects[object_name]
            except KeyError:
                if object_name:
                    msg = f"Could not find '{object_name}'. Check your spelling"
                else:
                    msg = f"Wiper slot #{slot} must have an object name"
                self.report({"ERROR"}, msg)
                raise KeyError
            else:
                object_datablock.select_set(True)
                windshield.select_set(True)

        paths = []
        for slot in [slot for slot in slots if getattr(rain, f"wiper_{slot}_enabled")]:
            try:
                select_objects(slot)
            except KeyError:
                break

            print("Animated baking for frames (%d - %d)" % (start, end))

            for cfra in range(start, end + 1):
                print("Baking frame %d" % cfra)

                # update scene to new frame and bake to template image
                scene.frame_set(cfra)
                if is_cycles:
                    if debug_skip_bake:
                        print("Skipping baking process")
                        ret = ""
                    else:
                        ret = bpy.ops.object.bake(type=scene.cycles.bake_type)
                else:
                    ret = bpy.ops.object.bake_image()
                if "CANCELLED" in ret:
                    return {"CANCELLED"}

                # Currently the api has no img.save_as()
                # !!! IMPORTANT! You must use filepath_raw! !!!
                orig = img.filepath_raw
                new_img_filepath = xplane_wiper_gradient.make_tmp_filepath(
                    pathlib.Path(bpy.path.abspath(img.filepath, library=img.library)),
                    cfra,
                    slot,
                )
                img.filepath_raw = str(new_img_filepath)
                paths.append(pathlib.Path(img.filepath_raw))
                if not debug_skip_bake:
                    img.save()
                    print("Saved %r" % new_img_filepath)
                img.filepath_raw = orig
            print("Baking done!")

        xplane_wiper_gradient.make_wiper_images(paths)
        return {"FINISHED"}


class OBJECT_OT_add_xplane_axis_detent_range(bpy.types.Operator):
    bl_label = "Add X-Plane Axis Detent Range"
    bl_idname = "object.add_xplane_axis_detent_range"
    bl_description = "Add X-Plane Axis Detent Range"

    def execute(self, context):
        obj = context.object
        obj.xplane.manip.axis_detent_ranges.add()
        return {"FINISHED"}


class OBJECT_OT_remove_xplane_axis_detent_range(bpy.types.Operator):
    bl_label = "Remove Axis Detent Range"
    bl_idname = "object.remove_xplane_axis_detent_range"
    bl_description = "Remove axis detent range"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.manip.axis_detent_ranges.remove(self.index)
        return {"FINISHED"}


class COLLECTION_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = "Add Layer Property"
    bl_idname = "collection.add_xplane_layer_attribute"
    bl_description = "Add a custom X-Plane Layer Property"

    collection_name: bpy.props.StringProperty()

    def execute(self, context):
        coll = bpy.data.collections[self.collection_name]
        coll.xplane.layer.customAttributes.add()
        return {"FINISHED"}


class COLLECTION_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = "Remove Layer Property"
    bl_idname = "collection.remove_xplane_layer_attribute"
    bl_description = "Remove the custom X-Plane Layer Property"

    collection_name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    def execute(self, context):
        coll = bpy.data.collections[self.collection_name]
        coll.xplane.layer.customAttributes.remove(self.index)
        return {"FINISHED"}


class OBJECT_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = "Add Layer Property"
    bl_idname = "object.add_xplane_layer_attribute"
    bl_description = "Add a custom X-Plane Layer Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.customAttributes.add()
        return {"FINISHED"}


class OBJECT_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = "Remove Layer Property"
    bl_idname = "object.remove_xplane_layer_attribute"
    bl_description = "Remove the custom X-Plane Layer Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.customAttributes.remove(self.index)
        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_object_attribute
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_attribute(bpy.types.Operator):
    bl_label = "Add Object Property"
    bl_idname = "object.add_xplane_object_attribute"
    bl_description = "Add a custom X-Plane Object Property"

    def execute(self, context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_attribute(bpy.types.Operator):
    bl_label = "Remove Object Property"
    bl_idname = "object.remove_xplane_object_attribute"
    bl_description = "Remove the custom X-Plane Object Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.customAttributes.remove(self.index)
        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_object_anim_attribute
# Adds a custom animation attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = "Add Animation Property"
    bl_idname = "object.add_xplane_object_anim_attribute"
    bl_description = "Add a custom X-Plane Animation Property"

    def execute(self, context):
        obj = context.object
        obj.xplane.customAnimAttributes.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_object_anim_attribute
# Removes a custom animation attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = "Remove Animation Property"
    bl_idname = "object.remove_xplane_object_anim_attribute"
    bl_description = "Remove the custom X-Plane Animation Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.customAnimAttributes.remove(self.index)
        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_material_attribute
# Adds a custom attribute to a Blender Material.
class OBJECT_OT_add_xplane_material_attribute(bpy.types.Operator):
    bl_label = "Add Material Property"
    bl_idname = "object.add_xplane_material_attribute"
    bl_description = "Add a custom X-Plane Material Property"

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.customAttributes.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Material.
class OBJECT_OT_remove_xplane_material_attribute(bpy.types.Operator):
    bl_label = "Remove Material Property"
    bl_idname = "object.remove_xplane_material_attribute"
    bl_description = "Remove the custom X-Plane Material Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.customAttributes.remove(self.index)
        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_light_attribute
# Adds a custom attribute to a Blender Light.
class OBJECT_OT_add_xplane_light_attribute(bpy.types.Operator):
    bl_label = "Add Light Property"
    bl_idname = "object.add_xplane_light_attribute"
    bl_description = "Add a custom X-Plane Light Property"

    def execute(self, context):
        obj = context.object.data
        obj.xplane.customAttributes.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Light.
class OBJECT_OT_remove_xplane_light_attribute(bpy.types.Operator):
    bl_label = "Remove Light Property"
    bl_idname = "object.remove_xplane_light_attribute"
    bl_description = "Remove the custom X-Plane Light Property"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.data
        obj.xplane.customAttributes.remove(self.index)
        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender Object.
class OBJECT_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = "Add Dataref"
    bl_idname = "object.add_xplane_dataref"
    bl_description = "Add an X-Plane Dataref"

    def execute(self, context):
        obj = context.object
        obj.xplane.datarefs.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender Object.
class OBJECT_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = "Remove Dataref"
    bl_idname = "object.remove_xplane_dataref"
    bl_description = "Remove the X-Plane Dataref"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.datarefs.remove(self.index)

        path = getDatarefValuePath(self.index)

        # remove FCurves too
        if (
            obj.animation_data != None
            and obj.animation_data.action != None
            and len(obj.animation_data.action.fcurves) > 0
        ):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves, path)
            if fcurve:
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_dataref_keyframe
# Adds a Keyframe to the value of a <XPlaneDataref> of an object.
class OBJECT_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = "Add Dataref keyframe"
    bl_idname = "object.add_xplane_dataref_keyframe"
    bl_description = "Add/Update an X-Plane Dataref keyframe"

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        value = obj.xplane.datarefs[self.index].value

        if "XPlane Datarefs" not in obj.animation_data.action.groups:
            obj.animation_data.action.groups.new("XPlane Datarefs")

        obj.xplane.datarefs[self.index].keyframe_insert(
            data_path="value", group="XPlane Datarefs"
        )
        makeKeyframesLinear(obj, path)

        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of an object.
class OBJECT_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = "Remove Dataref keyframe"
    bl_idname = "object.remove_xplane_dataref_keyframe"
    bl_description = "Remove the X-Plane Dataref keyframe"

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        obj.xplane.datarefs[self.index].keyframe_delete(
            data_path="value", group="XPlane Datarefs"
        )

        return {"FINISHED"}


class COLLECTION_OT_add_xplane_export_path_directive(bpy.types.Operator):
    bl_label = "Add Laminar Library Directive"
    bl_idname = "collection.add_xplane_export_path_directive"
    bl_description = "Add Laminar Library Directive"

    collection_name: bpy.props.StringProperty()

    def execute(self, context):
        coll = bpy.data.collections[self.collection_name]
        coll.xplane.layer.export_path_directives.add()
        return {"FINISHED"}


class COLLECTION_OT_remove_xplane_export_path_directive(bpy.types.Operator):
    bl_label = "Remove Laminar Library Directive"
    bl_idname = "collection.remove_xplane_export_path_directive"
    bl_description = "Remove Laminar Library Directive"

    collection_name: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    def execute(self, context):
        coll = bpy.data.collections[self.collection_name]
        coll.xplane.layer.export_path_directives.remove(self.index)
        return {"FINISHED"}


class OBJECT_OT_add_xplane_export_path_directive(bpy.types.Operator):
    bl_label = "Add Laminar Library Directive"
    bl_idname = "object.add_xplane_export_path_directive"
    bl_description = "Add Laminar Library Directive"

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.export_path_directives.add()
        return {"FINISHED"}


class OBJECT_OT_remove_xplane_export_path_directive(bpy.types.Operator):
    bl_label = "Remove Laminar Library Directive"
    bl_idname = "object.remove_xplane_export_path_directive"
    bl_description = "Remove Laminar Library Directive"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.export_path_directives.remove(self.index)
        return {"FINISHED"}


# Class: BONE_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender bone.
class BONE_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = "Add Dataref"
    bl_idname = "bone.add_xplane_dataref"
    bl_description = "Add/Update an X-Plane Dataref"

    def execute(self, context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.add()
        return {"FINISHED"}


# Class: BONE_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender bone.
class BONE_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = "Remove Dataref"
    bl_idname = "bone.remove_xplane_dataref"
    bl_description = "Remove the X-Plane Dataref"

    index: bpy.props.IntProperty()

    def execute(self, context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.remove(self.index)
        path = getDatarefValuePath(self.index, bone)

        # remove FCurves too
        if (
            obj.animation_data != None
            and obj.animation_data.action != None
            and len(obj.animation_data.action.fcurves) > 0
        ):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves, path)
            if fcurve:
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {"FINISHED"}


# Class: BONE_OT_add_xplane_dataref_keyframe
# Adds a Keyframe to the value of a <XPlaneDataref> of a bone.
class BONE_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = "Add Dataref keyframe"
    bl_idname = "bone.add_xplane_dataref_keyframe"
    bl_description = "Add/Update an X-Plane Dataref keyframe"

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index: bpy.props.IntProperty()

    # bpy.data.objects["Armature"].data.keyframe_insert(data_path='bones["Bone"].my_prop_group.nested', group="Nested Property")
    def execute(self, context):
        bone = (
            context.active_bone
        )  # context.bone is not always available, for instance, during test_creation_helpers
        # Other uses will be replaced as needed. context.object doesn't appear to be affected
        # See also: https://blender.stackexchange.com/q/31759
        armature = context.object
        path = getDatarefValuePath(self.index, bone)

        groupName = "XPlane Datarefs " + bone.name

        if groupName not in armature.animation_data.action.groups:
            armature.animation_data.action.groups.new(groupName)

        armature.data.keyframe_insert(data_path=path, group=groupName)

        return {"FINISHED"}


# Class: BONE_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of a bone.
class BONE_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = "Remove Dataref keyframe"
    bl_idname = "bone.remove_xplane_dataref_keyframe"
    bl_description = "Remove the X-Plane Dataref keyframe"

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index: bpy.props.IntProperty()

    def execute(self, context):
        bone = context.bone
        path = getDatarefValuePath(self.index)
        armature = context.object
        path = getDatarefValuePath(self.index, bone)
        armature.data.keyframe_delete(
            data_path=path, group="XPlane Datarefs " + bone.name
        )

        return {"FINISHED"}


# Class: OBJECT_OT_add_xplane_object_condition
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_condition(bpy.types.Operator):
    bl_label = "Add Condition"
    bl_idname = "object.add_xplane_object_condition"
    bl_description = "Add an X-Plane condition"

    def execute(self, context):
        obj = context.object
        obj.xplane.conditions.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_object_condition
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_condition(bpy.types.Operator):
    bl_label = "Remove Condition"
    bl_idname = "object.remove_xplane_object_condition"
    bl_description = "Remove X-Plane Condition"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.conditions.remove(self.index)
        return {"FINISHED"}

    # Class: OBJECT_OT_add_xplane_material_condition


# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_material_condition(bpy.types.Operator):
    bl_label = "Add Condition"
    bl_idname = "object.add_xplane_material_condition"
    bl_description = "Add an X-Plane condition"

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.conditions.add()
        return {"FINISHED"}


# Class: OBJECT_OT_remove_xplane_material_condition
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_material_condition(bpy.types.Operator):
    bl_label = "Remove Condition"
    bl_idname = "object.remove_xplane_material_condition"
    bl_description = "Remove X-Plane Condition"

    index: bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.conditions.remove(self.index)
        return {"FINISHED"}


# Class: SCENE_OT_export_to_relative_dir
# Exports OBJS into the same folder as the .blend file, and/or folders beneath it
class SCENE_OT_export_to_relative_dir(bpy.types.Operator):
    bl_label = "Export OBJs"
    bl_idname = "scene.export_to_relative_dir"
    bl_description = "Exports OBJs relative to the .blend file"

    # initial_dir that will be prepended to the path.
    initial_dir: bpy.props.StringProperty()

    def execute(self, context):
        bpy.ops.export.xplane_obj(filepath=self.initial_dir, export_is_relative=True)
        return {"FINISHED"}


class XPLANE_OT_CommandSearchToggle(bpy.types.Operator):
    """
    This operator very simply passes it's associated command to the search window, which then opens it in the UI.
    """

    bl_label = "Open/Close Command Search Window"
    bl_description = "Open/Close Command Search Window"
    bl_idname = "xplane.command_search_toggle"

    # Each operator is placed next to a command string property,
    #
    paired_command_prop: bpy.props.StringProperty()

    def execute(self, context):
        command_search_window_state = context.scene.xplane.command_search_window_state
        # Load on first use
        if len(command_search_window_state.command_search_list) == 0:
            filepath = pathlib.Path(
                xplane_helpers.get_plugin_resources_folder(), "Commands.txt"
            )
            get_commands_txt_result = xplane_commands_txt_parser.get_commands_txt_file_content(
                filepath.as_posix()
            )
            if isinstance(get_commands_txt_result, str):
                short_filepath = "..." + os.path.sep.join(filepath.parts[-3:])
                bpy.ops.xplane.error(
                    "INVOKE_DEFAULT",
                    msg_text=short_filepath + " could not be parsed",
                    report_text=get_commands_txt_result,
                )
                return {"CANCELLED"}
            else:
                file_content = get_commands_txt_result

            command_search_list = (
                bpy.context.scene.xplane.command_search_window_state.command_search_list
            )

            for command_info in file_content:
                command_search_list.add()
                command_search_list[-1].command = command_info.command
                command_search_list[-1].command_description = command_info.description

        prop = command_search_window_state.command_prop_dest

        # Toggle ourselves
        if prop == self.paired_command_prop:
            command_search_window_state.command_prop_dest = ""
        else:
            command_search_window_state.command_prop_dest = self.paired_command_prop

        return {"FINISHED"}


class XPLANE_OT_DatarefSearchToggle(bpy.types.Operator):
    """
    This operator very simply passes it's associated dataref to the search window, which then opens it in the UI.
    """

    bl_label = "Open/Close Dataref Search Window"
    bl_description = "Open/Close Dataref Search Window"
    bl_idname = "xplane.dataref_search_toggle"

    # Each operator is placed next to a dataref string property,
    #
    paired_dataref_prop: bpy.props.StringProperty()

    def execute(self, context):
        dataref_search_window_state = context.scene.xplane.dataref_search_window_state
        # Load on first use
        if len(dataref_search_window_state.dataref_search_list) == 0:
            filepath = pathlib.Path(
                xplane_helpers.get_plugin_resources_folder(), "DataRefs.txt"
            )
            get_datarefs_txt_result = xplane_datarefs_txt_parser.get_datarefs_txt_file_content(
                filepath.as_posix()
            )
            if isinstance(get_datarefs_txt_result, str):
                short_filepath = "..." + os.path.sep.join(filepath.parts[-3:])
                bpy.ops.xplane.error(
                    "INVOKE_DEFAULT",
                    msg_text=short_filepath + " could not be parsed",
                    report_text=get_datarefs_txt_result,
                )
                return {"CANCELLED"}
            else:
                file_content = get_datarefs_txt_result

            dataref_search_list = (
                bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list
            )

            for dref_info in file_content:
                dataref_search_list.add()
                dataref_search_list[-1].dataref_path = dref_info.path
                dataref_search_list[-1].dataref_type = dref_info.type
                dataref_search_list[-1].dataref_is_writable = dref_info.is_writable
                dataref_search_list[-1].dataref_units = dref_info.units
                dataref_search_list[-1].dataref_description = dref_info.description

        prop = dataref_search_window_state.dataref_prop_dest

        # Toggle ourselves
        if prop == self.paired_dataref_prop:
            dataref_search_window_state.dataref_prop_dest = ""
        else:
            dataref_search_window_state.dataref_prop_dest = self.paired_dataref_prop

        return {"FINISHED"}


_ops = (
    COLLECTION_OT_add_xplane_export_path_directive,
    COLLECTION_OT_remove_xplane_export_path_directive,
    COLLECTION_OT_add_xplane_layer_attribute,
    COLLECTION_OT_remove_xplane_layer_attribute,
    OBJECT_OT_add_xplane_axis_detent_range,
    OBJECT_OT_remove_xplane_axis_detent_range,
    OBJECT_OT_add_xplane_layer_attribute,
    OBJECT_OT_remove_xplane_layer_attribute,
    OBJECT_OT_add_xplane_object_attribute,
    OBJECT_OT_remove_xplane_object_attribute,
    OBJECT_OT_add_xplane_object_anim_attribute,
    OBJECT_OT_remove_xplane_object_anim_attribute,
    OBJECT_OT_add_xplane_material_attribute,
    OBJECT_OT_remove_xplane_material_attribute,
    OBJECT_OT_add_xplane_light_attribute,
    OBJECT_OT_remove_xplane_light_attribute,
    OBJECT_OT_add_xplane_dataref,
    OBJECT_OT_remove_xplane_dataref,
    OBJECT_OT_add_xplane_dataref_keyframe,
    OBJECT_OT_remove_xplane_dataref_keyframe,
    OBJECT_OT_add_xplane_export_path_directive,
    OBJECT_OT_remove_xplane_export_path_directive,
    BONE_OT_add_xplane_dataref,
    BONE_OT_remove_xplane_dataref,
    BONE_OT_add_xplane_dataref_keyframe,
    BONE_OT_remove_xplane_dataref_keyframe,
    OBJECT_OT_add_xplane_object_condition,
    OBJECT_OT_remove_xplane_object_condition,
    OBJECT_OT_add_xplane_material_condition,
    OBJECT_OT_remove_xplane_material_condition,
    SCENE_OT_export_to_relative_dir,
    XPLANE_OT_CommandSearchToggle,
    XPLANE_OT_DatarefSearchToggle,
    XPLANE_OT_render_bake_xp,
)

register, unregister = bpy.utils.register_classes_factory(_ops)
