# File: xplane_ui.py
# Creates the User Interface for all X-Plane settings.

import collections
from typing import Optional 

import bpy
from io_xplane2blender import xplane_constants
from bpy.types import Object, UILayout
from io_xplane2blender.xplane_constants import MANIPULATORS_OPT_IN
from typing import Optional

from .xplane_config import *
from .xplane_constants import *
from .xplane_helpers import getColorAndLitTextureSlots
from .xplane_ops import *
from .xplane_props import *


# Class: DATA_PT_xplane
# Adds X-Plane lamp settings to the lamp tab. Uses <lamp_layout> and <custom_layout>.
class DATA_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        obj = context.object
        version = int(bpy.context.scene.xplane.version)

        if obj.type == "LAMP":
            lamp_layout(self, obj.data)
            custom_layout(self, obj.data, "LAMP")
        if obj.type == "EMPTY" and version >= 1130:
            empty_layout(self, obj)


# Class: MATERIAL_PT_xplane
# Adds X-Plane Material settings to the material tab. Uses <material_layout> and <custom_layout>.
class MATERIAL_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
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

        if(obj.type == "MESH"):
            material_layout(self.layout, obj.active_material)
            self.layout.separator()
            cockpit_layout(self, obj.active_material)
            custom_layout(self, obj.active_material, "MATERIAL")

            if version >= 1000:
                conditions_layout(self, obj.active_material, "MATERIAL")


# Class: SCENE_PT_xplane
# Adds X-Plane Layer settings to the scene tab. Uses <scene_layout>.
class SCENE_PT_xplane(bpy.types.Panel):
    '''XPlane Scene Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene = context.scene
        scene_layout(self, scene)

# Class: OBJECT_PT_xplane
# Adds X-Plane settings to the object tab. Uses <mesh_layout>, <cockpit_layout>, <manipulator_layout> and <custom_layout>.
class OBJECT_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(self, context):
        obj = context.object

        if obj.type in ("MESH", "EMPTY", "ARMATURE", "LAMP"):
            return True
        else:
            return False

    def draw(self, context):
        obj = context.object
        version = int(context.scene.xplane.version)

        if obj.type in ("MESH", "EMPTY", "ARMATURE", "LAMP"):
            object_layer_layout(self, obj)

            animation_layout(self, obj)
            if obj.type == "MESH":
                mesh_layout(self, obj)
                manipulator_layout(self, obj)
            objType = obj.type
            if objType == "LAMP":
                objType = "OBJECT"
            lod_layout(self, obj)
            weight_layout(self, obj)
            custom_layout(self, obj, objType)

            # v1000
            if version >= 1000:
                conditions_layout(self, obj, "OBJECT")


# Class: BONE_PT_xplane
# Adds X-Plane settings to the bone tab. Uses <animation_layout>.
class BONE_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
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
        weight_layout(self, bone)
        animation_layout(self, bone, True)

def empty_layout(self:bpy.types.UILayout, empty_obj:bpy.types.Object):
    assert empty_obj.type == 'EMPTY'

    # Note: Even though this is being displayed on the Empty > Data
    # tab in the properties Window, the propery still comes
    # from bpy.types.Object.xplane because there is no bpy.types.Empty
    emp = empty_obj.xplane.special_empty_props

    layout = self.layout
    layout.row().prop(empty_obj.xplane.special_empty_props,'special_type')

    if emp.special_type == EMPTY_USAGE_EMITTER_PARTICLE or\
       emp.special_type == EMPTY_USAGE_EMITTER_SOUND:
        box = layout.box()
        box.label("Emitter Settings")
        row = box.row()
        row.prop(emp.emitter_props,"name",text="Name")
        # Adapted from properties_texture.py, factor_but
        sub = row.row()
        sub.prop(emp.emitter_props, "index_enabled", text="")
        sub.active = getattr(emp.emitter_props, "index_enabled")
        sub.prop(emp.emitter_props, "index", text="Index")

# Function: scene_layout
# Draws the UI layout for scene tabs. Uses <layer_layout>.
#
# Parameters:
#   self - Instance of current panel class.
#   scene - Blender scene.
def scene_layout(self, scene):
    layout = self.layout
    layout.row().operator("scene.export_to_relative_dir", icon="EXPORT")
    layout.row().prop(scene.xplane, "version")
    layout.row().prop(scene.xplane, "exportMode")
    layout.row().prop(scene.xplane, "compositeTextures")

    xp2b_ver = xplane_helpers.VerStruct.current()
    if xp2b_ver.build_type == xplane_constants.BUILD_TYPE_RC and xp2b_ver.build_number != xplane_constants.BUILD_NUMBER_NONE:
        layout.row().label("XPlane2Blender Version: " + str(xp2b_ver), icon="FILE_TICK")
    else:
        layout.row().label("XPlane2Blender Version: " + str(xp2b_ver), icon="NONE")

    needs_warning = False
    if xp2b_ver.build_type == xplane_constants.BUILD_TYPE_ALPHA or\
        xp2b_ver.build_type == xplane_constants.BUILD_TYPE_BETA:
        layout.row().label("BEWARE: " + xp2b_ver.build_type.capitalize() + " versions can damage files!", icon="ERROR")
        needs_warning = True
    elif xp2b_ver.build_type == xplane_constants.BUILD_TYPE_DEV:
        layout.row().label("Developer versions are DANGEROUS and UNSTABLE!", icon="RADIO")
        needs_warning = True

    if xp2b_ver.build_number == xplane_constants.BUILD_NUMBER_NONE:
        layout.row().label("No build number: addon may be EXTRA UNSTABLE.", icon="CANCEL")
        needs_warning = True

    if needs_warning is True:
        layout.row().label("     Make backups or switch to a more stable release!")

    if scene.xplane.exportMode == 'layers':
        if len(scene.xplane.layers) != 0:
            for i in range(0, len(scene.layers)):
                row = layout.row()
                scene_layer_layout(self, scene, row, i)
        else:
            layout.row().operator('scene.add_xplane_layers')

    advanced_box = layout.box()
    advanced_box.label("Advanced Settings")
    advanced_column = advanced_box.column()
    advanced_column.prop(scene.xplane, "optimize")
    advanced_column.prop(scene.xplane, "debug")

    if scene.xplane.debug:
        debug_box = advanced_column.box()
        #TODO: Remove profiler entirely?
        #debug_box.prop(scene.xplane, "profile")
        debug_box.prop(scene.xplane, "log")
    
    scene_dev_layout(self,scene,layout)

def scene_dev_layout(self,scene,layout):
    dev_box = layout.box()
    dev_box_row = dev_box.column_flow(2,True)
    dev_box_row.prop(scene.xplane, "plugin_development")
    dev_box_row.label(text="", icon="ERROR")
    if scene.xplane.plugin_development:
        dev_box_column = dev_box.column()
        dev_box_column.prop(scene.xplane, "dev_enable_breakpoints")
        dev_box_column.prop(scene.xplane, "dev_continue_export_on_error")
        dev_box_column.prop(scene.xplane, "dev_export_as_dry_run")
        #Exact same operator, more convient place 
        dev_box_column.operator("scene.export_to_relative_dir", icon="EXPORT")
        dev_box_column.operator("scene.dev_layer_names_from_objects")
        updater_row = dev_box_column.row()
        updater_row.prop(scene.xplane,"dev_fake_xplane2blender_version")
        updater_row.operator("scene.dev_rerun_updater")
        updater_row = dev_box_column.row()
        updater_row.operator("scene.dev_create_lights_txt_summary")
        
        history_box = dev_box_column.box()
        history_box.label("XPlane2Blender Version History")
        history_list = list(scene.xplane.xplane2blender_ver_history)
        history_list.reverse()
        for entry in history_list:
            icon_str = "NONE"
            if entry.build_type == xplane_constants.BUILD_TYPE_LEGACY:
                icon_str = "GHOST_ENABLED"
            if entry.build_type == xplane_constants.BUILD_TYPE_DEV:
                icon_str = "RADIO"
            elif entry.build_type == xplane_constants.BUILD_TYPE_ALPHA or\
                entry.build_type == xplane_constants.BUILD_TYPE_BETA:
                icon_str="ERROR"
            elif entry.build_type == xplane_constants.BUILD_TYPE_RC and entry.build_number != BUILD_NUMBER_NONE:
                icon_str="FILE_TICK"
            
            history_box.label(text=str(entry), icon=icon_str)

def scene_layer_layout(self, scene, layout, layer):
    version = int(scene.xplane.version)
    li = str(layer + 1)
    layerObj = scene.xplane.layers[layer]
    box = layout.box()
    li = str(layer + 1)

    if layerObj.expanded:
        expandIcon = "TRIA_DOWN"
        expanded = True
    else:
        expandIcon = "TRIA_RIGHT"
        expanded = False

    box.prop(layerObj, "expanded", text = "Layer " + li, expand = True, emboss = False, icon = expandIcon)

    if expanded:
        layer_layout(self, box, layerObj, version)
        export_path_dir_layer_layout(self, box, layerObj, version)
        custom_layer_layout(self, box, layerObj, version)

def object_layer_layout(self, obj):
    if bpy.context.scene.xplane.exportMode == 'root_objects':
        version = int(bpy.context.scene.xplane.version)
        layerObj = obj.xplane.layer
        row = self.layout.row()

        row.prop(obj.xplane, 'isExportableRoot')

        if obj.xplane.isExportableRoot:
            row = self.layout.row()
            box = row.box()

            if layerObj.expanded:
                expandIcon = "TRIA_DOWN"
                expanded = True
            else:
                expandIcon = "TRIA_RIGHT"
                expanded = False

            box.prop(layerObj, "expanded", text = "Root Object", expand = True, emboss = False, icon = expandIcon)

            if expanded:
                layer_layout(self, box, layerObj, version, 'object')
                export_path_dir_layer_layout(self, box, layerObj, version, 'object')
                custom_layer_layout(self, box, layerObj, version, 'object')

# Function: layer_layout
# Draws the UI layout for <XPlaneLayers>. Uses <custom_layer_layout>.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   scene - Blender scene
#   UILayout layout - Instance of sublayout to use.
#   int layer - <XPlaneLayer> index.
def layer_layout(self, layout, layerObj, version, context = 'scene'):
    canHaveDraped = version >= 1000 and layerObj.export_type not in ['aircraft', 'cockpit']
    isInstanced   = version >= 1000 and layerObj.export_type == 'instanced_scenery'

    #column = layout.column()
    layout.prop(layerObj, "name")
    layout.prop(layerObj, "export_type")

    tex_box = layout.box()
    tex_box.label('Textures')

    tex_box.prop(layerObj, "autodetectTextures")

    if not layerObj.autodetectTextures:
        tex_box.prop(layerObj, "texture", text = "Default")
        tex_box.prop(layerObj, "texture_lit", text = "Night")
        tex_box.prop(layerObj, "texture_normal", text = "Normal / Specular")

        if canHaveDraped:
            tex_box.prop(layerObj, "texture_draped", text = "Draped")
            tex_box.prop(layerObj, "texture_draped_normal", text = "Draped Normal / Specular")

    # cockpit regions
    if layerObj.export_type == 'cockpit':
        cockpit_box = layout.box()
        cockpit_box.label('Cockpits')
        #cockpit_box.prop(layerObj, "panel_texture")
        cockpit_box.prop(layerObj, "cockpit_regions", text= "Regions")
        num_regions = int(layerObj.cockpit_regions)

        if num_regions > 0:
            if len(layerObj.cockpit_region) < num_regions:
                region_box = cockpit_box.box()

                if context == 'scene':
                    region_box.operator("scene.add_xplane_layer_cockpit_regions").index = layerObj.index
                elif context == 'object':
                    region_box.operator("object.add_xplane_layer_cockpit_regions")
            else:
                for i in range(0, num_regions):
                    # get cockpit region or create it if not present
                    if len(layerObj.cockpit_region)>i:
                        cockpit_region = layerObj.cockpit_region[i]

                        if cockpit_region.expanded:
                            expandIcon = "TRIA_DOWN"
                        else:
                            expandIcon = "TRIA_RIGHT"

                        region_box = cockpit_box.box()
                        region_box.prop(cockpit_region, "expanded", text = "Cockpit region %i" % (i+1), expand = True, emboss = False, icon = expandIcon)

                        if cockpit_region.expanded:
                            region_box.prop(cockpit_region, "left")
                            region_box.prop(cockpit_region, "top")
                            region_split = region_box.split(percentage = 0.5)
                            region_split.prop(cockpit_region, "width")
                            region_split.label("= %d" % (2 ** cockpit_region.width))
                            region_split = region_box.split(percentage = 0.5)
                            region_split.prop(cockpit_region, "height")
                            region_split.label("= %d" % (2 ** cockpit_region.height))

        # v1010
        if version < 1100:
            # cockpit_lit
            cockpit_lit_box = cockpit_box.row()
            cockpit_lit_box.prop(layerObj, "cockpit_lit")
    # LODs
    else:
        lods_box = layout.box()
        lods_box.label('Levels of Detail')
        lods_box.prop(layerObj, "lods", text="LODs")
        num_lods = int(layerObj.lods)

        if num_lods > 0:
            if len(layerObj.lod) < num_lods:
                lod_box = lods_box.box()

                if context == 'scene':
                    lod_box.operator("scene.add_xplane_layer_lods").index = layerObj.index
                elif context == 'object':
                    lod_box.operator("object.add_xplane_layer_lods")

            else:
                for i in range(0, num_lods):
                    if len(layerObj.lod)>i:
                        lod = layerObj.lod[i]

                        if lod.expanded:
                            expandIcon = "TRIA_DOWN"
                        else:
                            expandIcon = "TRIA_RIGHT"

                        lod_box = lods_box.box()
                        lod_box.prop(lod, "expanded", text = "Level of detail %i" % (i+1), expand = True, emboss = False, icon = expandIcon)

                        if lod.expanded:
                            lod_box.prop(lod, "near")
                            lod_box.prop(lod, "far")

        if canHaveDraped:
            lods_box.prop(layerObj, "lod_draped")

    #Scenery Properties Group
    scenery_props_group_box = layout.box()
    scenery_props_group_box.label("Scenery Properties")

    layer_group_box = scenery_props_group_box.box()
    layer_group_box.label("Layer Grouping")
    layer_group_box.prop(layerObj, "layer_group")
    layer_group_box.prop(layerObj, "layer_group_offset")

    if canHaveDraped:
        layer_group_box.prop(layerObj, "layer_group_draped")
        layer_group_box.prop(layerObj, "layer_group_draped_offset")

    # v1010
    if version >= 1010 and (layerObj.export_type == EXPORT_TYPE_SCENERY or
                            layerObj.export_type == EXPORT_TYPE_INSTANCED_SCENERY):
        
        #TODO: Shouldn't these be material properties instead?
        # shadow
        shadow_box = scenery_props_group_box.box()
        shadow_box.prop(layerObj, "shadow", "Cast shadows")
        
    # v1000
    if version >= 1000:
        # slope_limit
        slope_box = scenery_props_group_box.box()
        slope_box.label("Slope Properties")
        slope_box.prop(layerObj, "slope_limit")

        if layerObj.slope_limit == True:
            slope_box.row().prop(layerObj, "slope_limit_min_pitch")
            slope_box.row().prop(layerObj, "slope_limit_max_pitch")
            slope_box.row().prop(layerObj, "slope_limit_min_roll")
            slope_box.row().prop(layerObj, "slope_limit_max_roll")

        # tilted
        slope_box.prop(layerObj, "tilted")

        # require surface
        require_box = scenery_props_group_box.row()
        require_box.prop(layerObj, "require_surface", "Require surface")

    # Other Options
    #layout.separator()
    advanced_box = layout.box()
    advanced_box.label("Advanced Options")
    if version >= 1130:
        advanced_box.prop(layerObj, "particle_system_file", text="Particle System File")
    advanced_box.prop(layerObj, "slungLoadWeight")

    advanced_box.prop(layerObj, "export")
    advanced_box.prop(layerObj, "debug")

# Function: custom_layer_layout
# Draws the UI layout for the custom attributes of a <XPlaneLayer>.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   UILayout layout - Instance of sublayout to use.
#   layerObj - <XPlaneLayer> .
def custom_layer_layout(self, layout, layerObj, version, context = 'scene'):
    layout.separator()
    row = layout.row()
    row.label("Custom Properties")

    if context == 'scene':
        row.operator("scene.add_xplane_layer_attribute").index = layerObj.index
    elif context == 'object':
        row.operator("object.add_xplane_layer_attribute")

    box = layout.box()

    for i, attr in enumerate(layerObj.customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "name")
        subrow.prop(attr, "value")

        if context == 'scene':
            subrow.operator("scene.remove_xplane_layer_attribute", text = "", emboss = False, icon = "X").index = (layerObj.index, i)
        elif context == 'object':
            subrow.operator("object.remove_xplane_layer_attribute", text = "", emboss = False, icon = "X").index = i

        if type in ("MATERIAL", "MESH"):
            subrow = subbox.row()
            subrow.prop(attr, "reset")

def command_search_window_layout(layout):
    scene = bpy.context.scene
    row = layout.row()
    row.template_list("UL_CommandSearchList", "", scene.xplane.command_search_window_state, "command_search_list", scene.xplane.command_search_window_state, "command_search_list_idx")

def dataref_search_window_layout(layout):
    scene = bpy.context.scene
    row = layout.row()
    row.template_list("UL_DatarefSearchList", "", scene.xplane.dataref_search_window_state, "dataref_search_list", scene.xplane.dataref_search_window_state, "dataref_search_list_idx")

def export_path_dir_layer_layout(self, layout, layerObj, version, context = 'scene'):
    layout.separator()
    row = layout.row()
    row.label("Export Path Directives")
    
    if context == 'scene':
        row.operator("scene.add_xplane_export_path_directive").index = layerObj.index
    elif context == 'object':
        row.operator("object.add_xplane_export_path_directive")
        
    box = layout.box()
    
    for i, attr in enumerate(layerObj.export_path_directives):
        row = box.row() 
        row.prop(attr,"export_path", text= "Export Path " + str(i))
        
        if context == 'scene':
            row.operator("scene.remove_xplane_export_path_directive", text="", emboss=False, icon="X").index = (layerObj.index, i)
        elif context == 'object':
            row.operator("object.remove_xplane_export_path_directive", text="", emboss=False, icon="X").index = i

# Function: mesh_layout
# Draws the additional UI layout for Mesh-Objects. This includes light-level and depth-culling.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def mesh_layout(self, obj):
    layout = self.layout

    if bpy.context.scene.xplane.exportMode == 'layers':
        row = layout.row()
        row.prop(obj.xplane, "export_mesh", text = "Export Animation In Layers")

    row = layout.row()

# Function: lamp_layout
# Draws the UI layout for lamps.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender data object, the lamp itself
def lamp_layout(self:bpy.types.UILayout, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "type", text = "Type")

    # TODO: deprecate named lights in v3.4
    if obj.xplane.type in ("named", "param"):
        row = layout.row()
        row.prop(obj.xplane, "name")
        if obj.xplane.type == "param":
            row = layout.row()
            row.prop(obj.xplane, "params", text = "Parameters")
    elif obj.xplane.type == "custom":
        row = layout.row()
        row.prop(obj.xplane, "size")
        row = layout.row()
        row.label("Texture Coordinates:")
        row = layout.row()
        row.prop(obj.xplane, "uv", text = "")
        row = layout.row()
        row.prop(obj.xplane, "dataref", text = "Dataref")
        scene = bpy.context.scene
        expanded = scene.xplane.dataref_search_window_state.dataref_prop_dest == "bpy.context.active_object.data.xplane.dataref"
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = row.operator('xplane.dataref_search_toggle', text = "", emboss = False, icon = our_icon)
        dataref_search_toggle_op.paired_dataref_prop = "bpy.context.active_object.data.xplane.dataref"
        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(layout)

        row = layout.row()
        row.prop(obj.xplane, "enable_rgb_override")
        if obj.xplane.enable_rgb_override:
            row = layout.row()
            row.prop(obj.xplane, "rgb_override_values")

# Function: material_layout
# Draws the UI layout for materials.
#
# Parameters:
#   UILayout layout - Instance of current UILayout.
#   Material active_material - The active_material of a mesh
def material_layout(layout:UILayout,
                    active_material:bpy.types.Material):
    version = int(bpy.context.scene.xplane.version)
    draw_box = layout.box()
    draw_box.label("Draw Settings")
    draw_box_column = draw_box.column()
    draw_box_column.prop(active_material.xplane, "draw")

    if (active_material.xplane.draw):
        draw_box_column.prop(active_material.xplane, "draped")

        if version >= 1100 and not active_material.xplane.panel:
            draw_box_column.prop(active_material.xplane, "normal_metalness")

        # v1000 blend / v9000 blend
        if version >= 1000:
            draw_box_column.prop(active_material.xplane, "blend_v1000")
        else:
            draw_box_column.prop(active_material.xplane, "blend")

        if version >= 1100:
            draw_box_column.prop(active_material.xplane, "blend_glass")
        if version >= 1000:
            blend_prop_enum = active_material.xplane.blend_v1000
        else:
            blend_prop_enum = None

        if active_material.xplane.blend == True and version < 1000:
            draw_box_column.prop(active_material.xplane, "blendRatio")
        elif blend_prop_enum == BLEND_OFF and version >= 1000:
            draw_box_column.prop(active_material.xplane, "blendRatio")

    surface_behavior_box = layout.box()
    surface_behavior_box.label("Surface Behavior")
    surface_behavior_box_column = surface_behavior_box.column()
    surface_behavior_box_column.prop(active_material.xplane, "surfaceType")

    if active_material.xplane.surfaceType != 'none':
        surface_behavior_box_column.prop(active_material.xplane, "deck")

    surface_behavior_box_column.prop(active_material.xplane, "solid_camera")
    ll_box = layout.box()
    ll_box.label("Light Levels")
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
        expanded = scene.xplane.dataref_search_window_state.dataref_prop_dest == "bpy.context.active_object.data.materials[0].xplane.lightLevel_dataref"
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = row.operator('xplane.dataref_search_toggle', text = "", emboss = False, icon = our_icon)
        dataref_search_toggle_op.paired_dataref_prop = "bpy.context.active_object.data.materials[0].xplane.lightLevel_dataref"

        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(box)

    ll_box_column.row()
    if not canPreviewEmit(active_material):
        ll_box_column.label("To enable the Day-Night Preview feature, add an albedo texture (uses Diffuse->Color) and a night texture (uses Shading->Emit)", icon = "INFO")
    else:
        ll_box_column.prop(active_material.xplane, "litFactor", slider = True)


    # instancing effects
    instanced_box = layout.box()
    instanced_box.label("Instancing Effects")
    instanced_box_column = instanced_box.column()
    instanced_box_column.prop(active_material.xplane, 'tint')

    if active_material.xplane.tint:
        instanced_box_column.prop(active_material.xplane, 'tint_albedo')
        instanced_box_column.prop(active_material.xplane, 'tint_emissive')

    layout.row().prop(active_material.xplane, "poly_os")


def canPreviewEmit(mat):
    texture, textureLit = getColorAndLitTextureSlots(mat)

    return (texture != None and textureLit != None)

# Function: custom_layout
# Draws the additional UI layout for custom attributes.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   string type - Type of object. ("MESH", "MATERIAL", "LAMP")
def custom_layout(self, obj:bpy.types.Object, object_type:str):
    if object_type in ("MESH", "ARMATURE", "OBJECT"):
        oType = 'object'
    elif object_type == "MATERIAL":
        oType = 'material'
    elif object_type == 'LAMP':
        oType = 'lamp'
    else:
        oType = None

    layout = self.layout
    layout.separator()

    if oType:
        # regular attributes
        row = layout.row()
        row.label("Custom Properties")
        row.operator("object.add_xplane_"+oType+"_attribute")
        box = layout.box()
        for i, attr in enumerate(obj.xplane.customAttributes):
            subbox = box.box()
            subrow = subbox.row()
            subrow.prop(attr, "name")
            subrow.operator("object.remove_xplane_"+oType+"_attribute", text = "", emboss = False, icon = "X").index = i
            subrow = subbox.row()
            subrow.prop(attr, "value")
            if object_type in ("MATERIAL", "MESH", "LAMP", "ARMATURE"):
                subrow = subbox.row()
                subrow.prop(attr, "reset")
                subrow = subbox.row()
                subrow.prop(attr, "weight")

        # animation attributes
        if object_type in ("MESH", "ARMATURE", "OBJECT"):
            row = layout.row()
            row.label("Custom Animation Properties")
            row.operator("object.add_xplane_object_anim_attribute")
            box = layout.box()
            for i, attr in enumerate(obj.xplane.customAnimAttributes):
                subbox = box.box()
                subrow = subbox.row()
                subrow.prop(attr, "name")
                subrow.operator("object.remove_xplane_object_anim_attribute", text = "", emboss = False, icon = "X").index = i
                subrow = subbox.row()
                subrow.prop(attr, "value")
                subrow = subbox.row()
                subrow.prop(attr, "weight")

# Function: animation_layout
# Draws the UI layout for animations. This includes Datarefs.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   bool bone - True if the object is a bone.
def animation_layout(self, obj, bone = False):
    layout = self.layout
    layout.separator()
    row = layout.row()
    row.label("Datarefs")
    if bone:
        row.operator("bone.add_xplane_dataref", text = "Add Dataref")
        current_dataref_prop_template = "bpy.context.active_bone.xplane.datarefs[{index}].path"
    else:
        row.operator("object.add_xplane_dataref", text = "Add Dataref")
        current_dataref_prop_template = "bpy.context.active_object.xplane.datarefs[{index}].path"

    box = layout.box()
    for i, attr in enumerate(obj.xplane.datarefs):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "path")

        # Next to path: magnifying glass icon for dataref search - icon toggles based on
        # disclosure, so compute that up front.
        scene = bpy.context.scene
        expanded = scene.xplane.dataref_search_window_state.dataref_prop_dest == current_dataref_prop_template.format(index=i)
        if expanded:
            our_icon = "ZOOM_OUT"
        else:
            our_icon = "ZOOM_IN"
        dataref_search_toggle_op = subrow.operator('xplane.dataref_search_toggle', text = "", emboss = False, icon = our_icon)
        dataref_search_toggle_op.paired_dataref_prop = current_dataref_prop_template.format(index=i)

        # Next: "X" box to nuke the dataref - further to the right to keep from separating search from its field.
        if bone:
            subrow.operator("bone.remove_xplane_dataref", text = "", emboss = False, icon = "X").index = i
        else:
            subrow.operator("object.remove_xplane_dataref", text = "", emboss = False, icon = "X").index = i

        # Finally, in the next row, if we are expanded, build the entire search list.
        if expanded:
            dataref_search_window_layout(subbox)

        subrow = subbox.row()
        subrow.prop(attr, "anim_type")
        subrow = subbox.row()

        if attr.anim_type in ('transform', 'translate', 'rotate'):
            if bpy.context.object.animation_data:
                if bone:
                    subrow.operator("bone.add_xplane_dataref_keyframe", text = "", icon = "KEY_HLT").index = i
                    subrow.operator("bone.remove_xplane_dataref_keyframe", text = "", icon = "KEY_DEHLT").index = i
                else:
                    subrow.operator("object.add_xplane_dataref_keyframe", text = "", icon = "KEY_HLT").index = i
                    subrow.operator("object.remove_xplane_dataref_keyframe", text = "", icon = "KEY_DEHLT").index = i
                subrow.prop(attr, "value")
                subrow = subbox.row()
                subrow.prop(attr, "loop")
            else:
                subrow.label('Object not animated')
        elif attr.anim_type in ("show", "hide"):
            subrow.prop(attr, "show_hide_v1")
            subrow = subbox.row()
            subrow.prop(attr, "show_hide_v2")

# Function: cockpit_layout
# Draws the UI layout for cockpit parameters. This includes panel.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def cockpit_layout(self, active_material:bpy.types.Material):
    layout = self.layout
    cockpit_box = layout.box()
    cockpit_box.label("Cockpit Panel")
    cockpit_box_column = cockpit_box.column()
    cockpit_box_column.prop(active_material.xplane, 'panel')

    if active_material.xplane.panel:
        cockpit_box_column.prop(active_material.xplane, 'cockpit_region')

def axis_detent_ranges_layout(self, layout, manip):
    layout.separator()
    row = layout.row()
    row.label("Axis Detent Range")
    
    row.operator("object.add_xplane_axis_detent_range")
        
    box = layout.box()

    for i, attr in enumerate(manip.axis_detent_ranges):
        row = box.row() 
        row.prop(attr,"start")
        row.prop(attr,"end")
        if manip.type == MANIP_DRAG_AXIS_DETENT:
            row.prop(attr,"height", text="Length")
        else:
            row.prop(attr,"height")
        
        row.operator("object.remove_xplane_axis_detent_range", text="", emboss=False, icon="X").index = i

# Function: manipulator_layout
# Draws the UI layout for manipulator settings.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def manipulator_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane.manip, 'enabled')

    if obj.xplane.manip.enabled:
        box = layout.box()

        xplane_version = int(bpy.context.scene.xplane.version)
        box.prop(obj.xplane.manip, 'type', text="Type")

        manipType = obj.xplane.manip.type

        box.prop(obj.xplane.manip, 'cursor', text="Cursor")
        box.prop(obj.xplane.manip, 'tooltip', text="Tooltip")

        def show_command_search_window_pairing(box, command_prop_name:str, prop_text:Optional[str]=None)->None:
            row = box.row()
            if prop_text:
                row.prop(obj.xplane.manip, command_prop_name, prop_text)
            else:
                row.prop(obj.xplane.manip, command_prop_name)

            scene = bpy.context.scene
            expanded = scene.xplane.command_search_window_state.command_prop_dest == "bpy.context.active_object.xplane.manip." + command_prop_name
            if expanded:
                our_icon = "ZOOM_OUT"
            else:
                our_icon = "ZOOM_IN"
            command_search_toggle_op = row.operator('xplane.command_search_toggle', text = "", emboss = False, icon = our_icon)
            command_search_toggle_op.paired_command_prop = "bpy.context.active_object.xplane.manip." + command_prop_name
            # Finally, in the next row, if we are expanded, build the entire search list.
            if expanded:
                command_search_window_layout(box)

        def show_dataref_search_window_pairing(box, dataref_prop_name:str, prop_text:Optional[str]=None)->None:
            row = box.row()
            if prop_text:
                row.prop(obj.xplane.manip, dataref_prop_name, prop_text)
            else:
                row.prop(obj.xplane.manip, dataref_prop_name)

            scene = bpy.context.scene
            expanded = scene.xplane.dataref_search_window_state.dataref_prop_dest == "bpy.context.active_object.xplane.manip." + dataref_prop_name
            if expanded:
                our_icon = "ZOOM_OUT"
            else:
                our_icon = "ZOOM_IN"
            dataref_search_toggle_op = row.operator('xplane.dataref_search_toggle', text = "", emboss = False, icon = our_icon)
            dataref_search_toggle_op.paired_dataref_prop = "bpy.context.active_object.xplane.manip." + dataref_prop_name
            # Finally, in the next row, if we are expanded, build the entire search list.
            if expanded:
                dataref_search_window_layout(box)

        MANIPULATORS_AXIS = { MANIP_DRAG_XY,
                              MANIP_DRAG_AXIS,
                              MANIP_COMMAND_AXIS,
                              MANIP_DRAG_AXIS_PIX}

        # EXPLICIT as in "Needs explict opt in permision"
        MANIPULATORS_AUTODETECT_EXPLICIT = { MANIP_DRAG_AXIS }
        MANIPULATORS_AUTODETECT_IMPLICIT = { MANIP_DRAG_AXIS_DETENT,
                                  MANIP_DRAG_ROTATE,
                                  MANIP_DRAG_ROTATE_DETENT}

        MANIPULATORS_AUTODETECT_DATAREFS = { MANIP_DRAG_AXIS,
                                             MANIP_DRAG_AXIS_DETENT,
                                             MANIP_DRAG_ROTATE,
                                             MANIP_DRAG_ROTATE_DETENT}

        MANIPULATORS_COMMAND_CLASSIC = { MANIP_COMMAND,
                                         MANIP_COMMAND_AXIS,
                                         MANIP_COMMAND_KNOB,
                                         MANIP_COMMAND_SWITCH_LEFT_RIGHT,
                                         MANIP_COMMAND_SWITCH_UP_DOWN}

        MANIPULATORS_COMMAND_1110 = { MANIP_COMMAND_KNOB2,
                                      MANIP_COMMAND_SWITCH_LEFT_RIGHT2,
                                      MANIP_COMMAND_SWITCH_UP_DOWN2}

        MANIPULATORS_COMMAND = MANIPULATORS_COMMAND_1110 | MANIPULATORS_COMMAND_CLASSIC

        MANIPULATORS_DETENT = { MANIP_DRAG_AXIS_DETENT,
                                MANIP_DRAG_ROTATE_DETENT}


        '''
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
        '''
        def should_show_autodetect_dataref(manip_type:str) -> bool:
            if manip_type in MANIPULATORS_AUTODETECT_DATAREFS and xplane_version >= 1110:
                if manip_type in MANIPULATORS_AUTODETECT_EXPLICIT:
                    return obj.xplane.manip.autodetect_settings_opt_in
                else:
                    return True
            else:
                return False

        def should_show_dataref(manip_type:str) -> bool:
            if manip_type in MANIPULATORS_AUTODETECT_EXPLICIT and\
               obj.xplane.manip.autodetect_settings_opt_in  and obj.xplane.manip.autodetect_datarefs:
                return False
            elif manip_type in MANIPULATORS_AUTODETECT_IMPLICIT and\
                 obj.xplane.manip.autodetect_datarefs:
               return False

            return True

        def get_dataref_title(manip_type:str, dataref_number:int)->str:
            assert dataref_number == 1 or dataref_number == 2
            if manip_type == MANIP_DRAG_AXIS or\
               manip_type == MANIP_DRAG_AXIS_DETENT:
                if dataref_number == 1:
                    return "Drag Axis Dataref"

            if manip_type == MANIP_DRAG_ROTATE or\
               manip_type == MANIP_DRAG_ROTATE_DETENT:
                if dataref_number == 1:
                   return "Rotation Axis Dataref"

            if manip_type == MANIP_DRAG_AXIS_DETENT or\
                manip_type == MANIP_DRAG_ROTATE_DETENT:
                if dataref_number == 2:
                    return "Detent Axis Dataref"

            return None

        # Each value contains two predicates: 1st, to decide to use it or not, 2nd, what title to use
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

        if manipType in MANIPULATORS_OPT_IN and xplane_version >= 1110: 
            box.prop(obj.xplane.manip, 'autodetect_settings_opt_in')

        for prop,predicates in props.items():
            if manipType in MANIPULATORS_OPT_IN and obj.xplane.manip.autodetect_settings_opt_in:
                disabled = lambda manip_type: False
                if manipType == MANIP_DRAG_AXIS:
                    props['dx'] = (disabled, None)
                    props['dy'] = (disabled, None)
                    props['dz'] = (disabled, None)
                    props['v1'] = (disabled, None)
                    props['v2'] = (disabled, None)

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

        if  manipType == MANIP_DRAG_AXIS_DETENT or\
            manipType == MANIP_DRAG_ROTATE_DETENT:
            axis_detent_ranges_layout(self, box, obj.xplane.manip)

# Function: conditions_layout
# Draws the UI layout for conditions.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   obgType - object type
def conditions_layout(self, obj, obgType):
    layout = self.layout

    obgType = obgType.lower()

    # regular attributes
    row = layout.row()
    row.label("Conditions")
    row.operator('object.add_xplane_' + obgType + '_condition', text = "Add Condition")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.conditions):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "variable")
        subrow.operator('object.remove_xplane_' + obgType + '_condition', text = "", emboss = False, icon = "X").index = i
        subrow = subbox.row()
        subrow.prop(attr, "value")

# Function: lod_layout
# Draws the UI for Levels of detail
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def lod_layout(self, obj):
    if bpy.context.scene.xplane.exportMode == 'layers':
        layout = self.layout
        row = layout.row()
        row.prop(obj.xplane, "lod", text = "LOD")

# Function: weight_layout
# Draws the UI for Object weight
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def weight_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, 'override_weight')
    if obj.xplane.override_weight:
        row.prop(obj.xplane, 'weight')

class UL_CommandSearchList(bpy.types.UIList):
    import io_xplane2blender.xplane_utils.xplane_commands_txt_parser

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        # Ben says: this is a total hack.  By just BASHING the filter, we open it always, rather than making the user open it.
        # Sadly there's no sane way to open the filter programmatically because Blender - the UI never gets access to the UIList
        # derivative, and we don't know its constructor syntax to override it.
        self.use_filter_show=True
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # This code makes labels - highlighting the label acts like a click via trickery
            layout.alignment = "EXPAND"
            row = layout.row(align=True)
            row.alignment = "LEFT"
            row.label(item.command, icon="NONE")
            row.label("|")
            row.label(item.command_description, icon="NONE")
            return

        elif self.layout_type in {'GRID'}:
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
            return flt_flags,flt_neworder
        
        #Search info:
        # A set of one or more unique searches (split on |) composed of one or more unique search terms (split by ' ')
        # A command must match at least one search in all searches, and must partially match each search term        
        search_info = []
        for search in filter_name.upper().split('|'):
            search_info.append(frozenset(search.split(' ')))
        search_info = set(search_info)

        def check_command(command_path:str, search_info:List[str])->bool:
            upper_command = command_path.upper()
            for search in search_info:
                for search_term in search:
                    if not search_term in upper_command:
                        break
                else:
                    return True
            return False

        for command_info in bpy.context.scene.xplane.command_search_window_state.command_search_list:
            if check_command(command_info.command, search_info):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0 << 0)

        return flt_flags, flt_neworder

class UL_DatarefSearchList(bpy.types.UIList):
    import io_xplane2blender.xplane_utils.xplane_datarefs_txt_parser

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):

        # Ben says: this is a total hack.  By just BASHING the filter, we open it always, rather than making the user open it.
        # Sadly there's no sane way to open the filter programmatically because Blender - the UI never gets access to the UIList
        # derivative, and we don't know its constructor syntax to override it.
        self.use_filter_show=True
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # This code makes labels - highlighting the label acts like a click via trickery
            layout.alignment = "EXPAND"
            row = layout.row(align=True)
            row.alignment = "LEFT"
            row.label(item.dataref_path, icon="NONE")
            row.label("|")
            row.label(item.dataref_type, icon="NONE")
            row.label("|")
            row.label(item.dataref_is_writable, icon="NONE")
            row.label("|")
            row.label(item.dataref_units, icon="NONE")
            return

        elif self.layout_type in {'GRID'}:
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
            return flt_flags,flt_neworder
        
        #Search info:
        # A set of one or more unique searches (split on |) composed of one or more unique search terms (split by ' ')
        # A dataref must match at least one search in all searches, and must partially match each search term        
        search_info = []
        for search in filter_name.upper().split('|'):
            search_info.append(frozenset(search.split(' ')))
        search_info = set(search_info)

        def check_dref(dataref_path:str, search_info:List[str])->bool:
            upper_dref = dataref_path.upper()
            for search in search_info:
                for search_term in search:
                    if not search_term in upper_dref:
                        break
                else:
                    return True
            return False

        for dref in bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list:
            if check_dref(dref.dataref_path, search_info):
                flt_flags.append(self.bitflag_filter_item)
            else:
                flt_flags.append(0 << 0)

        return flt_flags, flt_neworder

class XPlaneMessage(bpy.types.Operator):
    bl_idname = 'xplane.msg'
    bl_label = 'XPlane2Blender message'
    msg_type = bpy.props.StringProperty(default = 'INFO')
    msg_text = bpy.props.StringProperty(default = '')
    def execute(self, context):
        self.report(self.msg_type, self.msg_text)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text = self.msg_type+': '+self.msg_text)


class XPlaneError(bpy.types.Operator):
    bl_idname = 'xplane.error'
    bl_label = 'XPlane2Blender Error'
    msg_type = bpy.props.StringProperty(default = 'ERROR')
    msg_text = bpy.props.StringProperty(default = '')
    report_text = bpy.props.StringProperty(default = '')

    def execute(self, context):
        self.report({self.msg_type}, self.report_text)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self,width=400)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.msg_text,icon="ERROR")

_XPlaneUITypes = [
    BONE_PT_xplane,
    DATA_PT_xplane,
    MATERIAL_PT_xplane,
    OBJECT_PT_xplane,
    SCENE_PT_xplane,

    UL_CommandSearchList,
    UL_DatarefSearchList,
    XPlaneError,
    XPlaneMessage
] 

# Function: addXPlaneUI
# Registers all UI Panels.
def addXPlaneUI():
    for t in _XPlaneUITypes:
        bpy.utils.register_class(t)

# Function: removeXPlaneUI
# Unregisters all UI Panels.
def removeXPlaneUI():
    for t in _XPlaneUITypes:
        bpy.utils.unregister_class(t)
