"""
Creates the User Interface for all X-Plane properties.
"""

import collections
import math
from typing import Optional, Union

import bpy
from bpy.types import Object, UILayout

from io_xplane2blender import xplane_constants, xplane_props, xplane_types, xplane_utils

from .xplane_constants import *
from .xplane_ops import *
from .xplane_props import *


class DATA_PT_xplane(bpy.types.Panel):
    """XPlane Empty/Light Data Panel"""

    bl_label = "X-Plane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        obj = context.object
        version = int(bpy.context.scene.xplane.version)

        if obj.type == "LIGHT":
            light_layout(self.layout, obj)
            custom_layout(self.layout, obj)
        if obj.type == "EMPTY" and version >= 1130:
            empty_layout(self.layout, obj)


# Adds X-Plane Material settings to the material tab. Uses <material_layout> and <custom_layout>.
class MATERIAL_PT_xplane(bpy.types.Panel):
    """XPlane Material Panel"""

    bl_label = "X-Plane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(self, context):
        if context.material:
            return True

    def draw(self, context):
        obj = context.object
        version = int(context.scene.xplane.version)

        if obj and obj.type == "MESH":
            material_layout(self.layout, obj.active_material)
            self.layout.separator()
            cockpit_layout(self.layout, obj.active_material)
            custom_layout(self.layout, obj.active_material)

            if version >= 1000:
                conditions_layout(self.layout, obj.active_material)


# Adds X-Plane Layer settings to the scene tab. Uses <scene_layout>.
class SCENE_PT_xplane(bpy.types.Panel):
    """XPlane Scene Panel"""

    bl_label = "X-Plane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene = context.scene
        scene_layout(self.layout, scene)


# Adds X-Plane settings to the object tab. Uses <mesh_layout>, <cockpit_layout>, <manipulator_layout> and <custom_layout>.
class OBJECT_PT_xplane(bpy.types.Panel):
    """XPlane Object Panel"""

    bl_label = "X-Plane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(self, context):
        obj = context.object

        if obj.type in ("MESH", "EMPTY", "ARMATURE", "LIGHT"):
            return True
        else:
            return False

    def draw(self, context):
        obj = context.object
        version = int(context.scene.xplane.version)

        if obj.type in ("MESH", "EMPTY", "ARMATURE", "LIGHT"):
            object_layer_layout(self.layout, obj)

            animation_layout(self.layout, obj)
            if obj.type == "MESH":
                mesh_layout(self.layout, obj)
                manipulator_layout(self.layout, obj)
            lod_layout(self.layout, obj)
            weight_layout(self.layout, obj)
            if obj.type != "EMPTY":
                custom_layout(self.layout, obj)

            # v1000
            if version >= 1000:
                conditions_layout(self.layout, obj)


# Adds X-Plane settings to the bone tab. Uses <animation_layout>.
class BONE_PT_xplane(bpy.types.Panel):
    """XPlane Bone Panel"""

    bl_label = "X-Plane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(self, context):
        bone = context.bone

        if bone:
            return True
        else:
            return False

    def draw(self, context):
        bone = context.bone
        obj = context.object
        weight_layout(self.layout, bone)
        animation_layout(self.layout, bone, True)


def empty_layout(layout: bpy.types.UILayout, empty_obj: bpy.types.Object):
    assert empty_obj.type == "EMPTY"

    # Note: Even though this is being displayed on the Empty > Data
    # tab in the properties Window, the propery still comes
    # from bpy.types.Object.xplane because there is no bpy.types.Empty
    emp = empty_obj.xplane.special_empty_props

    layout.row().prop(empty_obj.xplane.special_empty_props, "special_type")

    if (
        emp.special_type == EMPTY_USAGE_EMITTER_PARTICLE
        or emp.special_type == EMPTY_USAGE_EMITTER_SOUND
    ):
        box = layout.box()
        box.label(text="Emitter Settings")
        row = box.row()
        row.prop(emp.emitter_props, "name", text="Name")
        # Adapted from properties_texture.py, factor_but
        sub = row.row()
        sub.prop(emp.emitter_props, "index_enabled", text="")
        sub.active = getattr(emp.emitter_props, "index_enabled")
        sub.prop(emp.emitter_props, "index", text="Index")
    elif emp.special_type == EMPTY_USAGE_MAGNET:
        box = layout.box()
        box.label(text="Magnet Settings")
        row = box.row()
        row.prop(emp.magnet_props, "debug_name")
        row = box.row(align=True)
        row.label(text="Magnet Type:")
        sub_row = row.row(align=True)
        sub_row.alignment = "RIGHT"
        sub_row.prop(emp.magnet_props, "magnet_type_is_xpad")
        sub_row.prop(emp.magnet_props, "magnet_type_is_flashlight")


def scene_layout(layout: bpy.types.UILayout, scene: bpy.types.Scene):
    layout.row().operator("scene.export_to_relative_dir", icon="EXPORT")
    layout.row().prop(scene.xplane, "version")
    layout.row().prop(scene.xplane, "compositeTextures")

    xp2b_ver = xplane_helpers.VerStruct.current()
    if (
        xp2b_ver.build_type == xplane_constants.BUILD_TYPE_RC
        and xp2b_ver.build_number != xplane_constants.BUILD_NUMBER_NONE
    ):
        layout.row().label(
            text="XPlane2Blender Version: " + str(xp2b_ver), icon="FILE_TICK"
        )
    else:
        layout.row().label(text="XPlane2Blender Version: " + str(xp2b_ver), icon="NONE")

    needs_warning = False
    if (
        xp2b_ver.build_type == xplane_constants.BUILD_TYPE_ALPHA
        or xp2b_ver.build_type == xplane_constants.BUILD_TYPE_BETA
    ):
        layout.row().label(
            text="BEWARE: "
            + xp2b_ver.build_type.capitalize()
            + " versions can damage files!",
            icon="ERROR",
        )
        needs_warning = True
    elif xp2b_ver.build_type == xplane_constants.BUILD_TYPE_DEV:
        layout.row().label(
            text="Developer versions are DANGEROUS and UNSTABLE!", icon="ORPHAN_DATA"
        )
        needs_warning = True

    if xp2b_ver.build_number == xplane_constants.BUILD_NUMBER_NONE:
        layout.row().label(
            text="No build number: addon may be EXTRA UNSTABLE.", icon="CANCEL"
        )
        needs_warning = True

    if needs_warning is True:
        layout.row().label(text="     Make backups or switch to a more stable release!")

    exp_box = layout.box()
    exp_box.label(text="Root Collections")
    for collection in [
        coll
        for coll in xplane_helpers.get_collections_in_scene(scene)[1:]
        if coll.xplane.is_exportable_collection
    ]:
        collection_layer_layout(exp_box, collection)

    non_exp_box = layout.box()

    non_exp_box.prop(
        scene.xplane,
        "expanded_non_exporting_collections",
        expand=True,
        emboss=False,
        icon="TRIA_DOWN"
        if scene.xplane.expanded_non_exporting_collections
        else "TRIA_RIGHT",
    )
    if scene.xplane.expanded_non_exporting_collections:
        for collection in [
            coll
            for coll in xplane_helpers.get_collections_in_scene(scene)[1:]
            if not coll.xplane.is_exportable_collection
        ]:
            collection_layer_layout(non_exp_box, collection)

    advanced_box = layout.box()
    advanced_box.label(text="Advanced Settings")
    advanced_column = advanced_box.column()
    advanced_column.prop(scene.xplane, "optimize")
    advanced_column.prop(scene.xplane, "debug")

    if scene.xplane.debug:
        debug_box = advanced_column.box()
        debug_box.prop(scene.xplane, "log")

    scene_dev_layout(layout, scene)


def scene_dev_layout(layout: bpy.types.UILayout, scene: bpy.types.Scene):
    dev_box = layout.box()
    dev_box_row = dev_box.column_flow(columns=2, align=True)
    dev_box_row.prop(scene.xplane, "plugin_development")
    dev_box_row.label(text="", icon="ERROR")
    if scene.xplane.plugin_development:
        dev_box_column = dev_box.column()
        dev_box_column.prop(scene.xplane, "dev_enable_breakpoints")
        dev_box_column.prop(scene.xplane, "dev_continue_export_on_error")
        dev_box_column.prop(scene.xplane, "dev_export_as_dry_run")
        # Exact same operator, more convient place
        dev_box_column.operator("scene.export_to_relative_dir", icon="EXPORT")
        op = dev_box_column.operator(
            "scene.export_to_relative_dir",
            text="Export to fixtures folder",
            icon="EXPORT",
        )
        op.initial_dir = "fixtures"
        dev_box_column.operator("scene.dev_apply_default_material_to_all")
        dev_box_column.operator("scene.dev_root_names_from_objects")
        updater_row = dev_box_column.row()
        updater_row.prop(scene.xplane, "dev_fake_xplane2blender_version")
        updater_row.operator("scene.dev_rerun_updater")
        updater_row = dev_box_column.row()
        updater_row.operator("scene.dev_create_lights_txt_summary")

        history_box = dev_box_column.box()
        history_box.label(text="XPlane2Blender Version History")
        history_list = list(scene.xplane.xplane2blender_ver_history)
        history_list.reverse()
        for entry in history_list:
            icon_str = "NONE"
            if entry.build_type == xplane_constants.BUILD_TYPE_LEGACY:
                icon_str = "GHOST_ENABLED"
            if entry.build_type == xplane_constants.BUILD_TYPE_DEV:
                icon_str = "ORPHAN_DATA"
            elif (
                entry.build_type == xplane_constants.BUILD_TYPE_ALPHA
                or entry.build_type == xplane_constants.BUILD_TYPE_BETA
            ):
                icon_str = "ERROR"
            elif (
                entry.build_type == xplane_constants.BUILD_TYPE_RC
                and entry.build_number != BUILD_NUMBER_NONE
            ):
                icon_str = "FILE_TICK"

            history_box.label(text=str(entry), icon=icon_str)


def collection_layer_layout(
    layout: bpy.types.UILayout, collection: bpy.types.Collection
):
    version = int(bpy.context.scene.xplane.version)
    layer_props = collection.xplane.layer
    row = layout.row()
    box = row.box()

    if layer_props.expanded:
        expandIcon = "TRIA_DOWN"
    else:
        expandIcon = "TRIA_RIGHT"
    column = box.column_flow(columns=2, align=True)
    column.prop(
        layer_props,
        "expanded",
        text=collection.name,
        expand=True,
        emboss=False,
        icon=expandIcon,
    )
    column.prop(collection.xplane, "is_exportable_collection")  # , text = "Export)

    if layer_props.expanded:
        layer_layout(box, layer_props, version, "object")
        export_path_dir_layer_layout(box, collection, version)
        custom_layer_layout(box, collection, version)


def object_layer_layout(layout: bpy.types.UILayout, obj: bpy.types.Object):
    version = int(bpy.context.scene.xplane.version)
    layer_props = obj.xplane.layer
    row = layout.row()

    row.prop(obj.xplane, "isExportableRoot")

    if obj.xplane.isExportableRoot:
        row = layout.row()
        box = row.box()

        if layer_props.expanded:
            expandIcon = "TRIA_DOWN"
            expanded = True
        else:
            expandIcon = "TRIA_RIGHT"
            expanded = False

        box.prop(
            layer_props,
            "expanded",
            text="Root Object",
            expand=True,
            emboss=False,
            icon=expandIcon,
        )

        if expanded:
            layer_layout(box, layer_props, version, "object")
            export_path_dir_layer_layout(box, obj, version)
            custom_layer_layout(box, obj, version)


def layer_layout(
    layout: bpy.types.UILayout,
    layer_props: xplane_props.XPlaneLayer,
    version: int,
    context: str,
):
    """Draws OBJ File Settings and advanced options"""
    canHaveDraped = version >= 1000 and layer_props.export_type not in [
        "aircraft",
        "cockpit",
    ]
    isInstanced = version >= 1000 and layer_props.export_type == "instanced_scenery"
    canHaveSceneryProps = layer_props.export_type not in ["aircraft", "cockpit"]

    # column = layout.column()
    layout.prop(layer_props, "name")
    layout.prop(layer_props, "export_type")

    tex_box = layout.box()
    tex_box.label(text="Textures")
    # tex_box.prop(layer_props, "autodetectTextures")
    # if not layer_props.autodetectTextures:
    if True:  # Hack until autodetectTextures means something again
        tex_box.prop(layer_props, "texture", text="Default")
        tex_box.prop(layer_props, "texture_lit", text="Night")
        tex_box.prop(layer_props, "texture_normal", text="Normal / Specular")

        if canHaveDraped:
            tex_box.prop(layer_props, "texture_draped", text="Draped")
            tex_box.prop(
                layer_props, "texture_draped_normal", text="Draped Normal / Specular"
            )

    global_mat_box = layout.box()
    global_mat_box.label(text="Global Material Options")
    if version >= 1100:
        global_mat_box.row().prop(layer_props, "blend_glass")
        global_mat_box.row().prop(layer_props, "normal_metalness")
        if layer_props.export_type in {
            EXPORT_TYPE_INSTANCED_SCENERY,
            EXPORT_TYPE_SCENERY,
        }:
            global_mat_box.row().prop(layer_props, "normal_metalness_draped")
            row = global_mat_box.row()
            row.active = layer_props.tint
            row.prop(layer_props, "tint")
            if layer_props.tint:
                row.prop(layer_props, "tint_albedo", text="Albedo", slider=True)
                row.prop(layer_props, "tint_emissive", text="Emissive", slider=True)

    # cockpit regions
    if layer_props.export_type in {EXPORT_TYPE_AIRCRAFT, EXPORT_TYPE_COCKPIT}:
        cockpit_box = layout.box()
        cockpit_box.label(text="Cockpit Panel Options")
        if version >= 1110:
            cockpit_box.row().prop(layer_props, "cockpit_panel_mode")

        if layer_props.cockpit_panel_mode == PANEL_COCKPIT:
            pass
        elif (
            version >= 1110 and layer_props.cockpit_panel_mode == PANEL_COCKPIT_LIT_ONLY
        ):
            pass
        elif layer_props.cockpit_panel_mode == PANEL_COCKPIT_REGION or version < 1110:
            cockpit_box.prop(layer_props, "cockpit_regions", text="Regions")
            for i, cockpit_region in enumerate(
                layer_props.cockpit_region[: int(layer_props.cockpit_regions)]
            ):
                region_box = cockpit_box.box()
                region_box.prop(
                    cockpit_region,
                    "expanded",
                    text="Cockpit region %i" % (i + 1),
                    expand=True,
                    emboss=False,
                    icon=("TRIA_DOWN" if cockpit_region.expanded else "TRIA_RIGHT"),
                )

                if cockpit_region.expanded:
                    region_box.prop(cockpit_region, "left")
                    region_box.prop(cockpit_region, "top")
                    region_split = region_box.split(factor=0.5)
                    region_split.prop(cockpit_region, "width")
                    region_split.label(text="= %d" % (2 ** cockpit_region.width))
                    region_split = region_box.split(factor=0.5)
                    region_split.prop(cockpit_region, "height")
                    region_split.label(text="= %d" % (2 ** cockpit_region.height))

        # v1010
        if version < 1100:
            # cockpit_lit
            cockpit_lit_box = cockpit_box.row()
            cockpit_lit_box.prop(layer_props, "cockpit_lit")
    # LODs
    lods_box = layout.box()
    lods_box.label(text="Levels of Detail")
    lods_box.prop(layer_props, "lods", text="LODs")
    num_lods = int(layer_props.lods)

    if num_lods:
        # Bad naming, I know
        for i, lod in enumerate(layer_props.lod[:num_lods]):
            if lod.expanded:
                expandIcon = "TRIA_DOWN"
            else:
                expandIcon = "TRIA_RIGHT"

            lod_box = lods_box.box()
            lod_box.prop(
                lod,
                "expanded",
                text="Level of detail %i" % (i + 1),
                expand=True,
                emboss=False,
                icon=expandIcon,
            )

            if lod.expanded:
                lod_box.prop(lod, "near")
                lod_box.prop(lod, "far")

    if canHaveDraped:
        lods_box.prop(layer_props, "lod_draped")

    if canHaveSceneryProps:
        # Scenery Properties Group
        scenery_props_group_box = layout.box()
        scenery_props_group_box.label(text="Scenery Properties")

        layer_group_box = scenery_props_group_box.box()
        layer_group_box.label(text="Layer Grouping")
        layer_group_box.prop(layer_props, "layer_group")
        layer_group_box.prop(layer_props, "layer_group_offset")

        if canHaveDraped:
            layer_group_box.prop(layer_props, "layer_group_draped")
            layer_group_box.prop(layer_props, "layer_group_draped_offset")

        # v1000
        if version >= 1000:
            # slope_limit
            slope_box = scenery_props_group_box.box()
            slope_box.label(text="Slope Properties")
            slope_box.prop(layer_props, "slope_limit")

            if layer_props.slope_limit == True:
                slope_box.row().prop(layer_props, "slope_limit_min_pitch")
                slope_box.row().prop(layer_props, "slope_limit_max_pitch")
                slope_box.row().prop(layer_props, "slope_limit_min_roll")
                slope_box.row().prop(layer_props, "slope_limit_max_roll")

            # tilted
            slope_box.prop(layer_props, "tilted")

            # require surface
            require_box = scenery_props_group_box.row()
            require_box.prop(layer_props, "require_surface", text="Require surface")

    # Advanced Options
    advanced_box = layout.box()
    advanced_box.label(text="Advanced Options")
    if version >= 1130:
        advanced_box.prop(
            layer_props, "particle_system_file", text="Particle System File"
        )
    advanced_box.prop(layer_props, "slungLoadWeight")

    advanced_box.prop(layer_props, "debug")


def custom_layer_layout(
    layout: bpy.types.UILayout,
    has_layer_props: Union[bpy.types.Collection, bpy.types.Object],
    version: int,
) -> None:
    layout.separator()
    row = layout.row()
    row.label(text="Custom Properties")

    if isinstance(has_layer_props, bpy.types.Collection):
        row.operator(
            "collection.add_xplane_layer_attribute"
        ).collection_name = has_layer_props.name
    elif isinstance(has_layer_props, bpy.types.Object):
        row.operator("object.add_xplane_layer_attribute")
    else:
        assert False, f"has_layer_prop is an unknown type {type(has_layer_props)}"

    box = layout.box()

    for i, attr in enumerate(has_layer_props.xplane.layer.customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "name")
        subrow.prop(attr, "value")

        if isinstance(has_layer_props, bpy.types.Collection):
            remove_op = subrow.operator(
                "collection.remove_xplane_layer_attribute",
                text="",
                emboss=False,
                icon="X",
            )
            remove_op.collection_name = has_layer_props.name
            remove_op.index = i
        elif isinstance(has_layer_props, bpy.types.Object):
            subrow.operator(
                "object.remove_xplane_layer_attribute", text="", emboss=False, icon="X"
            ).index = i

        if type in ("MATERIAL", "MESH"):
            subrow = subbox.row()
            subrow.prop(attr, "reset")


def command_search_window_layout(layout):
    scene = bpy.context.scene
    row = layout.row()
    row.template_list(
        "XPLANE_UL_CommandSearchList",
        "",
        scene.xplane.command_search_window_state,
        "command_search_list",
        scene.xplane.command_search_window_state,
        "command_search_list_idx",
    )


def dataref_search_window_layout(layout):
    scene = bpy.context.scene
    row = layout.row()
    row.template_list(
        "XPLANE_UL_DatarefSearchList",
        "",
        scene.xplane.dataref_search_window_state,
        "dataref_search_list",
        scene.xplane.dataref_search_window_state,
        "dataref_search_list_idx",
    )


def export_path_dir_layer_layout(
    layout: bpy.types.UILayout,
    has_layer_props: Union[bpy.types.Collection, bpy.types.Object],
    version: int,
):
    layout.separator()
    row = layout.row()
    row.label(text="Laminar Library Directives")

    if isinstance(has_layer_props, bpy.types.Collection):
        row.operator(
            "collection.add_xplane_export_path_directive"
        ).collection_name = has_layer_props.name
    elif isinstance(has_layer_props, bpy.types.Object):
        row.operator("object.add_xplane_export_path_directive")
    else:
        assert False, f"has_layer_prop is an unknown type {type(has_layer_props)}"

    box = layout.box()

    for i, attr in enumerate(has_layer_props.xplane.layer.export_path_directives):
        row = box.row()
        row.prop(attr, "export_path", text="Special library.txt Directive " + str(i))

        if isinstance(has_layer_props, bpy.types.Collection):
            remove_op = row.operator(
                "collection.remove_xplane_export_path_directive",
                text="",
                emboss=False,
                icon="X",
            )
            remove_op.collection_name = has_layer_props.name
            remove_op.index = i
        elif isinstance(has_layer_props, bpy.types.Object):
            row.operator(
                "object.remove_xplane_export_path_directive",
                text="",
                emboss=False,
                icon="X",
            ).index = i


def mesh_layout(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    """
    Draws the additional UI layout for Mesh. Currently unused.
    """
    pass


def light_layout(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    light_data = obj.data

    def draw_dataref_search_window(
        dataref_row: bpy.types.UILayout, layout: bpy.types.UILayout
    ):
        scene = bpy.context.scene
        expanded = (
            scene.xplane.dataref_search_window_state.dataref_prop_dest
            == "bpy.context.active_object.data.xplane.dataref"
        )
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = row.operator(
            "xplane.dataref_search_toggle", text="", emboss=False, icon=our_icon
        )
        dataref_search_toggle_op.paired_dataref_prop = (
            "bpy.context.active_object.data.xplane.dataref"
        )
        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(layout)

    layout.row().prop(light_data.xplane, "type")

    if light_data.xplane.type == LIGHT_AUTOMATIC and light_data.type not in {
        "POINT",
        "SPOT",
    }:
        layout.row().label(text="Automatic lights must use spot lights")
    elif light_data.xplane.type == LIGHT_AUTOMATIC and light_data.type in {
        "POINT",
        "SPOT",
    }:
        layout.row().prop(light_data.xplane, "name")

        def draw_automatic_ui():
            try:
                if light_data.xplane.name:
                    # Idk why Black was fighing so much about this line
                    gpl = xplane_utils.xplane_lights_txt_parser.get_parsed_light
                    parsed_light = gpl(light_data.xplane.name.strip())
                    # HACK: We take this shortcut because otherwise we'd need to pretend to
                    # fill in the overload and apply the sw_callback which breaks DRY.
                    # We know exactly what happens here, and we don't need to muck with is_omni over the UI
                    # - Ted, 06/18/2020
                    if "DIR_MAG" in parsed_light.light_param_def:
                        is_omni = light_data.type == "POINT"
                    else:
                        is_omni = parsed_light.best_overload().is_omni()

                    omni_conclusively_known = True
                else:
                    return
            except KeyError:
                layout.row().label(
                    text="Unknown Light Name: check spelling or update lights.txt",
                    icon="ERROR",
                )
                return
            except ValueError:
                is_omni = False
                omni_conclusively_known = False

            if not xplane_lights_txt_parser.is_automatic_light_compatible(
                parsed_light.name
            ):
                layout.row().label(
                    text=f"'{light_data.xplane.name} is incompatible with Automatic Lights.",
                    icon="ERROR",
                )
                layout.row().label(
                    text=f"Use a different light or switch X-Plane Light Type to Named or Manual Param"
                )
            # To understand why this all works, see the massive comment in xplane_lights_txt_parser.py
            elif is_omni and light_data.type == "SPOT":
                layout.row().label(
                    text=f"'{light_data.xplane.name}' is omnidirectional and must use a Point Light"
                )
            elif not is_omni and omni_conclusively_known and light_data.type == "POINT":
                layout.row().label(
                    text=f"'{light_data.xplane.name}' is directional and must use a Spot Light"
                )
            elif parsed_light.light_param_def:
                for param, prop_name in {
                    "INDEX": "param_index",
                    "FREQ": "param_freq",
                    "PHASE": "param_phase",
                    "SIZE": "param_size",
                }.items():
                    if param in parsed_light.light_param_def:
                        layout.row().prop(light_data.xplane, prop_name)

                has_width = "WIDTH" in parsed_light.light_param_def
                has_dir_mag = "DIR_MAG" in parsed_light.light_param_def
                if has_width or has_dir_mag:
                    debug_box = layout.box()
                    debug_box.label(text="Calculated Values")
                # debug_box = layout.box()
                # debug_box.row().label(text=f"{len(parsed_light.light_param_def)} {' '.join(parsed_light.light_param_def)}")
                # debug_box.row().label(text=f"{parsed_light.overloads[0]['DREF'] if 'DREF' in parsed_light.overloads[0] else ''}")
                # if light_data.xplane.params:
                # debug_box.row().label(text=f"Former Params: '{light_data.xplane.params}'")
                # if {"R","G","B"} <= set(parsed_light.light_param_def):
                # debug_box.row().label(text=f"R, G, B: {', '.join(map(lambda c: str(round(c, 3)), light_data.color))}")

                # def try_param(prop:str, param:str, text:str, n=5)->None:
                # if param in parsed_light.light_param_def:
                # debug_box.row().label(text=f"{text}: {round(light_data.xplane.get(prop), n)}")

                # try_param("param_size", "Size", 3)
                # --- WIDTH -----------------------------------------------
                if has_width or has_dir_mag:
                    # Covers DIR_MAG case as well,
                    # though, ideally we'd stick with only using is_omni
                    if light_data.type == "POINT":
                        WIDTH_val = "Omni"
                    elif is_omni and not omni_conclusively_known:
                        assert False, "is_omni can't be True and not conclusively known"
                    elif not is_omni:
                        if has_width:
                            if (
                                "BILLBOARD"
                                in parsed_light.best_overload().overload_type
                            ):
                                WIDTH_val = round(
                                    xplane_types.XPlaneLight.WIDTH_for_billboard(
                                        light_data.spot_size
                                    ),
                                    5,
                                )
                            elif "SPILL" in parsed_light.best_overload().overload_type:
                                WIDTH_val = round(
                                    xplane_types.XPlaneLight.WIDTH_for_spill(
                                        light_data.spot_size
                                    ),
                                    5,
                                )
                        elif has_dir_mag:
                            WIDTH_val = round(
                                xplane_types.XPlaneLight.DIR_MAG_for_billboard(
                                    light_data.spot_size
                                ),
                                5,
                            )
                    debug_box.row().label(text=f"Width: {WIDTH_val}")
                # ---------------------------------------------------------
                # try_param("param_index", "INDEX", "Dataref Index", n=0)
                # try_param("param_freq", "FREQ", "Freq")
                # try_param("param_phase", "PHASE", "Phase")

        draw_automatic_ui()
    elif light_data.xplane.type == LIGHT_SPILL_CUSTOM and light_data.type not in {
        "POINT",
        "SPOT",
    }:
        layout.row().label(
            text="Custom Spill lights must use Point or Spot Blender Lights"
        )
    elif light_data.xplane.type == LIGHT_SPILL_CUSTOM and light_data.type in {
        "POINT",
        "SPOT",
    }:
        layout.row().prop(light_data.xplane, "size")
        row = layout.row()
        row.prop(light_data.xplane, "dataref")
        draw_dataref_search_window(row, layout)
        debug_box = layout.box()
        debug_box.label(text="Calculated Values")
        if light_data.type == "POINT":
            WIDTH_val = "Omni"
        elif light_data.type == "SPOT":
            WIDTH_val = round(
                xplane_types.XPlaneLight.WIDTH_for_spill(light_data.spot_size), 5
            )
        debug_box.row().label(text=f"Width: {WIDTH_val}")
    elif light_data.xplane.type == LIGHT_NAMED:
        layout.row().prop(light_data.xplane, "name")
    elif light_data.xplane.type == LIGHT_PARAM:
        layout.row().prop(light_data.xplane, "name")
        layout.row().prop(light_data.xplane, "params")
    elif light_data.xplane.type == LIGHT_CUSTOM:
        layout.row().prop(light_data.xplane, "size")
        layout.row().label(text="Texture Coordinates:")
        layout.row().prop(light_data.xplane, "uv", text="")
        row = layout.row()
        row.prop(light_data.xplane, "dataref", text="Dataref")
        draw_dataref_search_window(row, layout)

        layout.row().prop(light_data.xplane, "enable_rgb_override")
        if light_data.xplane.enable_rgb_override:
            layout.row().prop(light_data.xplane, "rgb_override_values")
    layout.row().operator("scene.dev_create_lights_txt_summary")


# Function: material_layout
# Draws the UI layout for materials.
#
# Parameters:
#   UILayout layout - Instance of current UILayout.
#   Material active_material - The active_material of a mesh
def material_layout(layout: UILayout, active_material: bpy.types.Material) -> None:
    version = int(bpy.context.scene.xplane.version)
    draw_box = layout.box()
    draw_box.label(text="Draw Settings")
    draw_box_column = draw_box.column()
    draw_box_column.prop(active_material.xplane, "draw")

    if active_material.xplane.draw:
        draw_box_column.prop(active_material.xplane, "draped")

        # v1000 blend / v9000 blend
        if version >= 1000:
            draw_box_column.prop(active_material.xplane, "blend_v1000")

        if version >= 1010:
            draw_box_column.prop(active_material.xplane, "shadow_local")

        if version >= 1000:
            blend_prop_enum = active_material.xplane.blend_v1000
        else:
            blend_prop_enum = None

        if active_material.xplane.blend == True and version < 1000:
            draw_box_column.prop(active_material.xplane, "blendRatio", slider=True)
        elif blend_prop_enum == BLEND_OFF and version >= 1000:
            draw_box_column.prop(active_material.xplane, "blendRatio", slider=True)
        elif blend_prop_enum == BLEND_SHADOW and version >= 1000:
            draw_box_column.prop(
                active_material.xplane,
                "blendRatio",
                text="Shadow Blend Ratio",
                slider=True,
            )

    surface_behavior_box = layout.box()
    surface_behavior_box.label(text="Surface Behavior")
    surface_behavior_box_column = surface_behavior_box.column()
    surface_behavior_box_column.prop(active_material.xplane, "surfaceType")

    if active_material.xplane.surfaceType != "none":
        surface_behavior_box_column.prop(
            active_material.xplane, "deck", text="Only Slightly Thick"
        )

    surface_behavior_box_column.prop(active_material.xplane, "solid_camera")
    ll_box = layout.box()
    ll_box.label(text="Light Levels")
    ll_box_column = ll_box.column()
    ll_box_column.prop(active_material.xplane, "lightLevel")

    if active_material.xplane.lightLevel:
        box = ll_box_column.box()
        box.prop(active_material.xplane, "lightLevel_v1")
        row = box.row()
        row.prop(active_material.xplane, "lightLevel_v2")
        row = box.row()
        row.prop(active_material.xplane, "lightLevel_dataref")

        scene = bpy.context.scene
        expanded = (
            scene.xplane.dataref_search_window_state.dataref_prop_dest
            == "bpy.context.active_object.data.materials[0].xplane.lightLevel_dataref"
        )
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = row.operator(
            "xplane.dataref_search_toggle", text="", emboss=False, icon=our_icon
        )
        dataref_search_toggle_op.paired_dataref_prop = (
            "bpy.context.active_object.data.materials[0].xplane.lightLevel_dataref"
        )

        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(box)

    ll_box_column.row()

    # instancing effects
    layout.row().prop(active_material.xplane, "poly_os")


def custom_layout(
    layout: bpy.types.UILayout,
    has_custom_props: [
        bpy.types.Armature,
        bpy.types.Light,
        bpy.types.Material,
        bpy.types.Object,
    ],
):
    if isinstance(has_custom_props, bpy.types.Material):
        op_type = "material"
    elif has_custom_props.type == "LIGHT":
        op_type = "light"
    elif has_custom_props.type in {"ARMATURE", "MESH"}:
        op_type = "object"
    else:
        assert False, has_custom_props.name + " does not have custom_props"

    layout.separator()

    # regular attributes
    row = layout.row()
    row.label(text="Custom Properties")
    row.operator("object.add_xplane_" + op_type + "_attribute")
    box = layout.box()
    for i, attr in enumerate(has_custom_props.xplane.customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "name")
        subrow.operator(
            "object.remove_xplane_" + op_type + "_attribute",
            text="",
            emboss=False,
            icon="X",
        ).index = i
        subrow = subbox.row()
        subrow.prop(attr, "value")
        subrow = subbox.row()
        subrow.prop(attr, "reset")
        subrow = subbox.row()
        subrow.prop(attr, "weight")

    # animation attributes
    if op_type != "material":
        row = layout.row()
        row.label(text="Custom Animation Properties")
        row.operator("object.add_xplane_object_anim_attribute")
        box = layout.box()
        for i, attr in enumerate(has_custom_props.xplane.customAnimAttributes):
            subbox = box.box()
            subrow = subbox.row()
            subrow.prop(attr, "name")
            subrow.operator(
                "object.remove_xplane_object_anim_attribute",
                text="",
                emboss=False,
                icon="X",
            ).index = i
            subrow = subbox.row()
            subrow.prop(attr, "value")
            subrow = subbox.row()
            subrow.prop(attr, "weight")


# Function: animation_layout
def animation_layout(
    layout: bpy.types.UILayout, obj: bpy.types.Object, is_bone: bool = False
):
    """
    Draws UI Layout for animations, including datarefs
    and the datarefs search window
    """
    layout.separator()
    row = layout.row()
    row.label(text="Datarefs")
    if is_bone:
        row.operator("bone.add_xplane_dataref", text="Add Dataref")
        current_dataref_prop_template = (
            "bpy.context.active_bone.xplane.datarefs[{index}].path"
        )
    else:
        row.operator("object.add_xplane_dataref", text="Add Dataref")
        current_dataref_prop_template = (
            "bpy.context.active_object.xplane.datarefs[{index}].path"
        )

    box = layout.box()
    for i, attr in enumerate(obj.xplane.datarefs):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "path")

        # Next to path: magnifying glass icon for dataref search - icon toggles based on
        # disclosure, so compute that up front.
        scene = bpy.context.scene
        expanded = (
            scene.xplane.dataref_search_window_state.dataref_prop_dest
            == current_dataref_prop_template.format(index=i)
        )
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = subrow.operator(
            "xplane.dataref_search_toggle", text="", emboss=False, icon=our_icon
        )
        paired_prop = current_dataref_prop_template.format(index=i)

        dataref_search_toggle_op.paired_dataref_prop = paired_prop
        # Next: "X" box to nuke the dataref - further to the right to keep from separating search from its field.
        if is_bone:
            subrow.operator(
                "bone.remove_xplane_dataref", text="", emboss=False, icon="X"
            ).index = i
        else:
            subrow.operator(
                "object.remove_xplane_dataref", text="", emboss=False, icon="X"
            ).index = i

        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(subbox)

        subrow = subbox.row()
        subrow.prop(attr, "anim_type")
        subrow = subbox.row()

        if attr.anim_type in ("transform", "translate", "rotate"):
            if bpy.context.object.animation_data:
                if is_bone:
                    subrow.operator(
                        "bone.add_xplane_dataref_keyframe", text="", icon="KEY_HLT"
                    ).index = i
                    subrow.operator(
                        "bone.remove_xplane_dataref_keyframe", text="", icon="KEY_DEHLT"
                    ).index = i
                else:
                    subrow.operator(
                        "object.add_xplane_dataref_keyframe", text="", icon="KEY_HLT"
                    ).index = i
                    subrow.operator(
                        "object.remove_xplane_dataref_keyframe",
                        text="",
                        icon="KEY_DEHLT",
                    ).index = i
                subrow.prop(attr, "value")
                subrow = subbox.row()
                subrow.prop(attr, "loop")
            else:
                subrow.label(text="Object not animated")
        elif attr.anim_type in ("show", "hide"):
            subrow.prop(attr, "show_hide_v1")
            subrow = subbox.row()
            subrow.prop(attr, "show_hide_v2")


def cockpit_layout(
    layout: bpy.types.UILayout, active_material: bpy.types.Material
) -> None:
    """Draws UI for cockpit and panel regions"""
    cockpit_box = layout.box()
    cockpit_box.label(text="Cockpit Features")
    cockpit_box_column = cockpit_box.column()
    cockpit_box_column.prop(active_material.xplane, "cockpit_feature")

    if active_material.xplane.cockpit_feature == COCKPIT_FEATURE_NONE:
        pass
    elif active_material.xplane.cockpit_feature == COCKPIT_FEATURE_PANEL:
        cockpit_box_column.prop(active_material.xplane, "cockpit_region")
    elif active_material.xplane.cockpit_feature == COCKPIT_FEATURE_DEVICE:
        device_box = cockpit_box_column.box()
        device_box.label(text="Cockpit Device")
        device_box.prop(active_material.xplane, "device_name")
        if not any(
            getattr(active_material.xplane, f"device_bus_{bus}") for bus in range(6)
        ):
            device_box.label(text="Select at least one bus", icon="ERROR")
        column = device_box.column_flow(columns=2, align=True)
        for bus in range(6):
            column.prop(active_material.xplane, f"device_bus_{bus}")
        device_box.prop(active_material.xplane, "device_lighting_channel")
        device_box.prop(active_material.xplane, "device_auto_adjust")


def axis_detent_ranges_layout(
    layout: bpy.types.UILayout, manip: xplane_props.XPlaneManipulatorSettings
) -> None:
    layout.separator()
    row = layout.row()
    row.label(text="Axis Detent Range")

    row.operator("object.add_xplane_axis_detent_range")

    box = layout.box()

    for i, attr in enumerate(manip.axis_detent_ranges):
        row = box.row()
        row.prop(attr, "start")
        row.prop(attr, "end")
        if manip.type == MANIP_DRAG_AXIS_DETENT:
            row.prop(attr, "height", text="Length")
        else:
            row.prop(attr, "height")

        row.operator(
            "object.remove_xplane_axis_detent_range", text="", emboss=False, icon="X"
        ).index = i


def manipulator_layout(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    row = layout.row()
    row.prop(obj.xplane.manip, "enabled")

    if obj.xplane.manip.enabled:
        box = layout.box()

        xplane_version = int(bpy.context.scene.xplane.version)
        box.prop(obj.xplane.manip, "type", text="Type")

        manipType = obj.xplane.manip.type

        box.prop(obj.xplane.manip, "cursor", text="Cursor")
        box.prop(obj.xplane.manip, "tooltip", text="Tooltip")

        def show_command_search_window_pairing(
            box, command_prop_name: str, prop_text: Optional[str] = None
        ) -> None:
            row = box.row()
            if prop_text:
                row.prop(obj.xplane.manip, command_prop_name, prop_text)
            else:
                row.prop(obj.xplane.manip, command_prop_name)

            scene = bpy.context.scene
            expanded = (
                scene.xplane.command_search_window_state.command_prop_dest
                == "bpy.context.active_object.xplane.manip." + command_prop_name
            )
            if expanded:
                our_icon = "ZOOM_OUT"
            else:
                our_icon = "ZOOM_IN"
            command_search_toggle_op = row.operator(
                "xplane.command_search_toggle", text="", emboss=False, icon=our_icon
            )
            command_search_toggle_op.paired_command_prop = (
                "bpy.context.active_object.xplane.manip." + command_prop_name
            )
            # Finally, in the next row, if we are expanded, build the entire search list.
            if expanded:
                command_search_window_layout(box)

        def show_dataref_search_window_pairing(
            box, dataref_prop_name: str, prop_text: Optional[str] = None
        ) -> None:
            row = box.row()
            if prop_text:
                row.prop(obj.xplane.manip, dataref_prop_name, text=prop_text)
            else:
                row.prop(obj.xplane.manip, dataref_prop_name)

            scene = bpy.context.scene
            expanded = (
                scene.xplane.dataref_search_window_state.dataref_prop_dest
                == "bpy.context.active_object.xplane.manip." + dataref_prop_name
            )
            if expanded:
                our_icon = "ZOOM_OUT"
            else:
                our_icon = "ZOOM_IN"
            dataref_search_toggle_op = row.operator(
                "xplane.dataref_search_toggle", text="", emboss=False, icon=our_icon
            )
            dataref_search_toggle_op.paired_dataref_prop = (
                "bpy.context.active_object.xplane.manip." + dataref_prop_name
            )
            # Finally, in the next row, if we are expanded, build the entire search list.
            if expanded:
                dataref_search_window_layout(box)

        MANIPULATORS_AXIS = {
            MANIP_DRAG_XY,
            MANIP_DRAG_AXIS,
            MANIP_COMMAND_AXIS,
            MANIP_DRAG_AXIS_PIX,
        }

        # EXPLICIT as in "Needs explict opt in permision"
        MANIPULATORS_AUTODETECT_EXPLICIT = {MANIP_DRAG_AXIS}
        MANIPULATORS_AUTODETECT_IMPLICIT = {
            MANIP_DRAG_AXIS_DETENT,
            MANIP_DRAG_ROTATE,
            MANIP_DRAG_ROTATE_DETENT,
        }

        MANIPULATORS_AUTODETECT_DATAREFS = {
            MANIP_DRAG_AXIS,
            MANIP_DRAG_AXIS_DETENT,
            MANIP_DRAG_ROTATE,
            MANIP_DRAG_ROTATE_DETENT,
        }

        MANIPULATORS_COMMAND_CLASSIC = {
            MANIP_COMMAND,
            MANIP_COMMAND_AXIS,
            MANIP_COMMAND_KNOB,
            MANIP_COMMAND_SWITCH_LEFT_RIGHT,
            MANIP_COMMAND_SWITCH_UP_DOWN,
        }

        MANIPULATORS_COMMAND_1110 = {
            MANIP_COMMAND_KNOB2,
            MANIP_COMMAND_SWITCH_LEFT_RIGHT2,
            MANIP_COMMAND_SWITCH_UP_DOWN2,
        }

        MANIPULATORS_COMMAND = MANIPULATORS_COMMAND_1110 | MANIPULATORS_COMMAND_CLASSIC

        MANIPULATORS_DETENT = {MANIP_DRAG_AXIS_DETENT, MANIP_DRAG_ROTATE_DETENT}

        """
        UI Spec for showing Autodetect and Dataref properties

        # Dataref Text Boxes and Search Button (Window)
        - Dataref text boxes only appear for relevant types
        - When a dataref text box is shown, the dataref search button
          (or window) is shown
        - The dataref search button appears after all dataref textboxs
        - Dataref text boxes and search button appear regardless of Autodetect Settings Opt In (for classic types)

        # Autodetect Datarefs checkbox
        - The checkbox only appears for relevant manip types
        - Dataref text boxes will only be hidden when checked
        - Checkbox only appears when Autodetect Settings is true
          (for Opt In types) or always for new types

        # Autodetect Settings Opt In
        - The checkbox only appears for relevant manip types
        """

        def should_show_autodetect_dataref(manip_type: str) -> bool:
            if (
                manip_type in MANIPULATORS_AUTODETECT_DATAREFS
                and xplane_version >= 1110
            ):
                if manip_type in MANIPULATORS_AUTODETECT_EXPLICIT:
                    return obj.xplane.manip.autodetect_settings_opt_in
                else:
                    return True
            else:
                return False

        def should_show_dataref(manip_type: str) -> bool:
            if (
                manip_type in MANIPULATORS_AUTODETECT_EXPLICIT
                and obj.xplane.manip.autodetect_settings_opt_in
                and obj.xplane.manip.autodetect_datarefs
            ):
                return False
            elif (
                manip_type in MANIPULATORS_AUTODETECT_IMPLICIT
                and obj.xplane.manip.autodetect_datarefs
            ):
                return False

            return True

        def get_dataref_title(manip_type: str, dataref_number: int) -> str:
            assert dataref_number == 1 or dataref_number == 2
            if manip_type == MANIP_DRAG_AXIS or manip_type == MANIP_DRAG_AXIS_DETENT:
                if dataref_number == 1:
                    return "Drag Axis Dataref"

            if (
                manip_type == MANIP_DRAG_ROTATE
                or manip_type == MANIP_DRAG_ROTATE_DETENT
            ):
                if dataref_number == 1:
                    return "Rotation Axis Dataref"

            if (
                manip_type == MANIP_DRAG_AXIS_DETENT
                or manip_type == MANIP_DRAG_ROTATE_DETENT
            ):
                if dataref_number == 2:
                    return "Detent Axis Dataref"

            return None

        # Each value contains two predicates: 1st, to decide to use it or not, 2nd, what title to use
        # fmt: off
        props =  collections.OrderedDict() # type: Dict[str,Tuple[Callable[[str],bool],Optional[Callable[[str],bool]]]]
        props['autodetect_datarefs'] = (lambda manip_type: should_show_autodetect_dataref(manip_type), None)
        props['dataref1'] = (lambda manip_type: manip_type in MANIPULATORS_ALL - MANIPULATORS_COMMAND and\
                should_show_dataref(manip_type), lambda manip_type: get_dataref_title(manip_type,1))
        props['dataref2'] =\
            lambda manip_type: manip_type in {MANIP_DRAG_XY} | {MANIP_DRAG_AXIS_DETENT, MANIP_DRAG_ROTATE_DETENT} and should_show_dataref(manip_type),\
            lambda manip_type: get_dataref_title(manip_type,2)

        props['dx'] = (lambda manip_type: manip_type in MANIPULATORS_AXIS, None)
        props['dy'] = (lambda manip_type: manip_type in MANIPULATORS_AXIS - {MANIP_DRAG_AXIS_PIX}, None)
        props['dz'] = (lambda manip_type: manip_type in MANIPULATORS_AXIS - {MANIP_DRAG_XY, MANIP_DRAG_AXIS_PIX}, None)

        props['step'] = (lambda manip_type: manip_type in {MANIP_DRAG_AXIS_PIX}, None)
        props['exp' ] = (lambda manip_type: manip_type in {MANIP_DRAG_AXIS_PIX}, None)

        props['v1_min'] = (lambda manip_type: manip_type in {MANIP_DRAG_XY,MANIP_DELTA,MANIP_WRAP}, None)
        props['v1_max'] = (lambda manip_type: manip_type in {MANIP_DRAG_XY,MANIP_DELTA,MANIP_WRAP}, None)
        props['v2_min'] = (lambda manip_type: manip_type in {MANIP_DRAG_XY}, None)
        props['v2_max'] = (lambda manip_type: manip_type in {MANIP_DRAG_XY}, None)

        props['v1'] = (lambda manip_type: manip_type in {MANIP_DRAG_AXIS, MANIP_DRAG_AXIS_PIX, MANIP_AXIS_KNOB, MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT}, None)
        props['v2'] = (lambda manip_type: manip_type in {MANIP_DRAG_AXIS, MANIP_DRAG_AXIS_PIX, MANIP_AXIS_KNOB, MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT}, None)

        props['command'] = (lambda manip_type: manip_type in MANIPULATORS_COMMAND_1110 | {MANIP_COMMAND}, None)
        props['positive_command'] = (lambda manip_type: manip_type in MANIPULATORS_COMMAND_CLASSIC - {MANIP_COMMAND}, None)
        props['negative_command'] = (lambda manip_type: manip_type in MANIPULATORS_COMMAND_CLASSIC - {MANIP_COMMAND}, None)

        props['v_down'] = (lambda manip_type: manip_type in {MANIP_PUSH,MANIP_RADIO,MANIP_DELTA,MANIP_WRAP}, None)
        props['v_up'  ] = (lambda manip_type: manip_type in {MANIP_PUSH}, None)

        props['v_on']   = (lambda manip_type: manip_type in {MANIP_TOGGLE}, None)
        props['v_off']  = (lambda manip_type: manip_type in {MANIP_TOGGLE}, None)
        props['v_hold'] = (lambda manip_type: manip_type in {MANIP_DELTA,MANIP_WRAP}, None)

        props['click_step']  = (lambda manip_type: manip_type in {MANIP_AXIS_KNOB, MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT}, None)
        props['hold_step']   = (lambda manip_type: manip_type in {MANIP_AXIS_KNOB, MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT}, None)
        props['wheel_delta'] = (lambda manip_type: manip_type in MANIPULATORS_MOUSE_WHEEL and xplane_version >= 1050, None)
        # fmt: on

        if manipType in MANIPULATORS_OPT_IN and xplane_version >= 1110:
            box.prop(obj.xplane.manip, "autodetect_settings_opt_in")

        for prop, predicates in props.items():
            if (
                manipType in MANIPULATORS_OPT_IN
                and obj.xplane.manip.autodetect_settings_opt_in
            ):
                disabled = lambda manip_type: False
                if manipType == MANIP_DRAG_AXIS:
                    props["dx"] = (disabled, None)
                    props["dy"] = (disabled, None)
                    props["dz"] = (disabled, None)
                    props["v1"] = (disabled, None)
                    props["v2"] = (disabled, None)

            if predicates[0](manipType):
                if predicates[1]:
                    text = predicates[1](manipType)
                    if prop == "dataref1" or prop == "dataref2":
                        show_dataref_search_window_pairing(box, prop, text)
                    else:
                        if text:
                            box.prop(obj.xplane.manip, prop, text=text)
                        else:
                            box.prop(obj.xplane.manip, prop)
                else:
                    if prop in {"command", "positive_command", "negative_command"}:
                        show_command_search_window_pairing(box, prop)
                    else:
                        box.prop(obj.xplane.manip, prop)

        if manipType == MANIP_DRAG_AXIS_DETENT or manipType == MANIP_DRAG_ROTATE_DETENT:
            axis_detent_ranges_layout(box, obj.xplane.manip)


def conditions_layout(
    layout: bpy.types.UILayout,
    could_have_conditions: Union[bpy.types.Material, bpy.types.Object],
) -> None:
    assert isinstance(could_have_conditions, bpy.types.Material) or isinstance(
        could_have_conditions, bpy.types.Object
    )
    op_type = (
        "material"
        if isinstance(could_have_conditions, bpy.types.Material)
        else "object"
    )

    # regular attributes
    row = layout.row()
    row.label(text="Conditions")
    row.operator("object.add_xplane_" + op_type + "_condition", text="Add Condition")
    box = layout.box()
    for i, attr in enumerate(could_have_conditions.xplane.conditions):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "variable")
        subrow.operator(
            "object.remove_xplane_" + op_type + "_condition",
            text="",
            emboss=False,
            icon="X",
        ).index = i
        subrow = subbox.row()
        subrow.prop(attr, "value")


def lod_layout(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    row = layout.row()
    row.prop(obj.xplane, "override_lods")
    if obj.xplane.override_lods:
        box = layout.box()
        box.row().prop(obj.xplane, "lod", text="LOD")


def weight_layout(layout: bpy.types.UILayout, obj: bpy.types.Object) -> None:
    row = layout.row()
    row.prop(obj.xplane, "override_weight")
    if obj.xplane.override_weight:
        row.prop(obj.xplane, "weight")


class XPLANE_UL_CommandSearchList(bpy.types.UIList):
    import io_xplane2blender.xplane_utils.xplane_commands_txt_parser

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
        flt_flag,
    ):

        # Ben says: this is a total hack.  By just BASHING the filter, we open it always, rather than making the user open it.
        # Sadly there's no sane way to open the filter programmatically because Blender - the UI never gets access to the UIList
        # derivative, and we don't know its constructor syntax to override it.
        self.use_filter_show = True
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # This code makes labels - highlighting the label acts like a click via trickery
            layout.alignment = "EXPAND"
            row = layout.row(align=True)
            row.alignment = "LEFT"
            row.label(text=item.command, icon="NONE")
            row.label(text="|")
            row.label(text=item.command_description, icon="NONE")
            return

        elif self.layout_type in {"GRID"}:
            pass

    def draw_filter(self, context, layout):
        row = layout.row()
        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")

    # Called once to filter/reorder items.
    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        filter_name = self.filter_name
        if filter_name == "":
            return flt_flags, flt_neworder

        # Search info:
        # A set of one or more unique searches (split on |) composed of one or more unique search terms (split by ' ')
        # A command must match at least one search in all searches, and must partially match each search term
        search_info = []
        for search in filter_name.upper().split("|"):
            search_info.append(frozenset(search.split(" ")))
        search_info = set(search_info)

        def check_command(command_path: str, search_info: List[str]) -> bool:
            upper_command = command_path.upper()
            for search in search_info:
                for search_term in search:
                    if not search_term in upper_command:
                        break
                else:
                    return True
            return False

        for (
            command_info
        ) in bpy.context.scene.xplane.command_search_window_state.command_search_list:
            if check_command(command_info.command, search_info):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0 << 0)

        return flt_flags, flt_neworder


class XPLANE_UL_DatarefSearchList(bpy.types.UIList):
    import io_xplane2blender.xplane_utils.xplane_datarefs_txt_parser

    def draw_item(
        self,
        context,
        layout,
        data,
        item,
        icon,
        active_data,
        active_propname,
        index,
        flt_flag,
    ):

        # Ben says: this is a total hack.  By just BASHING the filter, we open it always, rather than making the user open it.
        # Sadly there's no sane way to open the filter programmatically because Blender - the UI never gets access to the UIList
        # derivative, and we don't know its constructor syntax to override it.
        self.use_filter_show = True
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            # This code makes labels - highlighting the label acts like a click via trickery
            layout.alignment = "EXPAND"
            row = layout.row(align=True)
            row.alignment = "LEFT"
            row.label(text=item.dataref_path, icon="NONE")
            row.label(text="|")
            row.label(text=item.dataref_type, icon="NONE")
            row.label(text="|")
            row.label(text=item.dataref_is_writable, icon="NONE")
            row.label(text="|")
            row.label(text=item.dataref_units, icon="NONE")
            return

        elif self.layout_type in {"GRID"}:
            pass

    def draw_filter(self, context, layout):
        row = layout.row()
        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")

    # Called once to filter/reorder items.
    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        filter_name = self.filter_name
        if filter_name == "":
            return flt_flags, flt_neworder

        # Search info:
        # A set of one or more unique searches (split on |) composed of one or more unique search terms (split by ' ')
        # A dataref must match at least one search in all searches, and must partially match each search term
        search_info = []
        for search in filter_name.upper().split("|"):
            search_info.append(frozenset(search.split(" ")))
        search_info = set(search_info)

        def check_dref(dataref_path: str, search_info: List[str]) -> bool:
            upper_dref = dataref_path.upper()
            for search in search_info:
                for search_term in search:
                    if not search_term in upper_dref:
                        break
                else:
                    return True
            return False

        for (
            dref
        ) in bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list:
            if check_dref(dref.dataref_path, search_info):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0 << 0)

        return flt_flags, flt_neworder


class XPLANE_OT_XPlaneMessage(bpy.types.Operator):
    bl_idname = "xplane.msg"
    bl_label = "XPlane2Blender message"
    msg_type: bpy.props.StringProperty(default="INFO")
    msg_text: bpy.props.StringProperty(default="")

    def execute(self, context):
        self.report(self.msg_type, self.msg_text)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.msg_type + ": " + self.msg_text)


class XPLANE_OT_XPlaneError(bpy.types.Operator):
    bl_idname = "xplane.error"
    bl_label = "XPlane2Blender Error"
    msg_type: bpy.props.StringProperty(default="ERROR")
    msg_text: bpy.props.StringProperty(default="")
    report_text: bpy.props.StringProperty(default="")

    def execute(self, context):
        self.report({self.msg_type}, self.report_text)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.msg_text, icon="ERROR")


_XPlaneUITypes = (
    BONE_PT_xplane,
    DATA_PT_xplane,
    MATERIAL_PT_xplane,
    OBJECT_PT_xplane,
    SCENE_PT_xplane,
    XPLANE_UL_CommandSearchList,
    XPLANE_UL_DatarefSearchList,
    XPLANE_OT_XPlaneError,
    XPLANE_OT_XPlaneMessage,
)

register, unregister = bpy.utils.register_classes_factory(_XPlaneUITypes)
