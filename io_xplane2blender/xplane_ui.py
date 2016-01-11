# File: xplane_ui.py
# Creates the User Interface for all X-Plane settings.

import bpy
from .xplane_ops import *
from .xplane_config import *
from .xplane_constants import *
from .xplane_helpers import getColorAndLitTextureSlots

# Class: LAMP_PT_xplane
# Adds X-Plane lamp settings to the lamp tab. Uses <lamp_layout> and <custom_layout>.
class LAMP_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        obj = context.object

        if(obj.type == "LAMP"):
            lamp_layout(self, obj.data)
            custom_layout(self, obj.data, "LAMP")

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
            material_layout(self, obj.active_material)
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

# Class: OBJECT_MT_xplane_datarefs
# Adds the X-Plane datarefs search menu. This is not implemented yet.
class OBJECT_MT_xplane_datarefs(bpy.types.Menu):
    '''XPlane Datarefs Search Menu'''
    bl_label = "XPlane Datarefs"

    def draw(self, context):
        self.search_menu(xplane_datarefs, "text.open")

# Function: scene_layout
# Draws the UI layout for scene tabs. Uses <layer_layout>.
#
# Parameters:
#   self - Instance of current panel class.
#   scene - Blender scene.
def scene_layout(self, scene):
    layout = self.layout
    row = layout.row()
    row.prop(scene.xplane, "version", text = "X-Plane Version")

    row = layout.row()
    row.prop(scene.xplane, "optimize", text = "Optimize")

    row = layout.row()
    row.prop(scene.xplane, "debug", text = "Debug")

    if scene.xplane.debug:
        box = layout.box()
        box.prop(scene.xplane, "profile", text = "Profiling")
        box.prop(scene.xplane, "log", text = "Log")

    row = layout.row()
    row.prop(scene.xplane, "exportMode", text = "Export Mode")

    row = layout.row()

    if scene.xplane.exportMode == 'layers':
        if len(scene.xplane.layers) != 0:
            for i in range(0, len(scene.layers)):
                row = layout.row()
                scene_layer_layout(self, scene, row, i)
        else:
            row.operator('scene.add_xplane_layers')

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
        custom_layer_layout(self, box, layerObj, version)

def object_layer_layout(self, obj):
    if bpy.context.scene.xplane.exportMode == 'root_objects':
        version = int(bpy.context.scene.xplane.version)
        layerObj = obj.xplane.layer
        row = self.layout.row()

        row.prop(obj.xplane, 'isExportableRoot', text = 'Root Object')

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
    isInstanced = version >= 1000 and layerObj.export_type == 'instanced_scenery'

    column = layout.column()
    column.prop(layerObj, "export", text = "Export")
    column.prop(layerObj, "debug", text = "Debug")
    column.prop(layerObj, "name", text = "Name")
    column.prop(layerObj, "export_type", text = "Type")

    column.label('Textures')
    tex_box = column.box()

    tex_box.prop(layerObj, "autodetectTextures", text = "Autodetect Textures")

    if not layerObj.autodetectTextures:
        tex_box.prop(layerObj, "texture", text = "Default")
        tex_box.prop(layerObj, "texture_lit", text = "Night")
        tex_box.prop(layerObj, "texture_normal", text = "Normal / Specular")

        if canHaveDraped:
            tex_box.prop(layerObj, "texture_draped", text = "Draped")
            tex_box.prop(layerObj, "texture_draped_normal", text = "Draped Normal / Specular")

    # cockpit regions
    if layerObj.export_type == 'cockpit':
        cockpit_box = column.box()
        #cockpit_box.prop(layerObj, "panel_texture", text = "Panel Texture")
        cockpit_box.prop(layerObj, "cockpit_regions", text = "Cockpit regions")
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
        # cockpit_lit
        cockpit_lit_box = column.row()
        cockpit_lit_box.prop(layerObj, "cockpit_lit", "3D-Cockpit lighting")

    # LODs
    else:
        lods_box = column.box()
        lods_box.prop(layerObj, "lods", text = "Levels of detail")
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

    column.separator()
    column.prop(layerObj, "slungLoadWeight", text = "Slung Load weight")

    # v1000
    if version >= 1000:
        # slope_limit
        slope_box = column.box()
        slope_box.prop(layerObj, "slope_limit", text = "Slope limit")

        if (layerObj.slope_limit == True):
            row = slope_box.row()
            row.prop(layerObj, "slope_limit_min_pitch", text = "Min. pitch")
            row = slope_box.row()
            row.prop(layerObj, "slope_limit_max_pitch", text = "Max. pitch")
            row = slope_box.row()
            row.prop(layerObj, "slope_limit_min_roll", text = "Min. roll")
            row = slope_box.row()
            row.prop(layerObj, "slope_limit_max_roll", text = "Max. roll")

        # tilted
        tilted_box = column.row()
        tilted_box.prop(layerObj, "tilted", text = "Tilted")

        # require surface
        require_box = column.row()
        require_box.prop(layerObj, "require_surface", "Require surface")

    # v1010
    if version >= 1010:
        # shadow
        shadow_box = column.box()
        shadow_box.prop(layerObj, "shadow", "Cast shadows")
        row = shadow_box.row()
        row.prop(layerObj, "shadow_blend", "Shadow cutoff")

        if layerObj.shadow_blend:
            row = shadow_box.row()
            row.prop(layerObj, "shadow_blend_ratio", "Cutoff Ratio")

    layer_group_box = column.box()
    layer_group_box.prop(layerObj, "layer_group")
    layer_group_box.prop(layerObj, "layer_group_offset")

    if canHaveDraped:
        layer_group_box.prop(layerObj, "layer_group_draped")
        layer_group_box.prop(layerObj, "layer_group_draped_offset")

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
        row.operator("scene.add_xplane_layer_attribute", text = "Add Property").index = layerObj.index
    elif context == 'object':
        row.operator("object.add_xplane_layer_attribute", text = "Add Property")

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

# Function: mesh_layout
# Draws the additional UI layout for Mesh-Objects. This includes light-level and depth-culling.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def mesh_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "depth", text = "Use depth culling")

    if bpy.context.scene.xplane.exportMode == 'layers':
        row = layout.row()
        row.prop(obj.xplane, "export_mesh", text = "Export mesh in layers")

    row = layout.row()

# Function: lamp_layout
# Draws the UI layout for lamps.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def lamp_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "type", text = "Type")

    # TODO: deprecate named lights in v3.4
    if obj.xplane.type in ("named", "param"):
        row = layout.row()
        row.prop(obj.xplane, "name", text = "Name")
        if obj.xplane.type == "param":
            row = layout.row()
            row.prop(obj.xplane, "params", text = "Parameters")
    elif obj.xplane.type == "custom":
        row = layout.row()
        row.prop(obj.xplane, "size", text = "Size")
        row = layout.row()
        row.label("Texture coordinates:")
        row = layout.row()
        row.prop(obj.xplane, "uv", text = "")
        row = layout.row()
        row.prop(obj.xplane, "dataref", text = "Dataref")
        row = layout.row()
        row.operator('xplane.dataref_search', text = "Search dataref", emboss = True, icon = "VIEWZOOM")

# Function: material_layout
# Draws the UI layout for materials.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def material_layout(self, obj):
    # TODO: hide stuff for draped materials
    isDraped = obj.xplane.draped
    version = int(bpy.context.scene.xplane.version)
    layout = self.layout

    row = layout.row()
    row.prop(obj.xplane, "draw", text = "Draw")

    if (obj.xplane.draw):
        row = layout.row()
        row.prop(obj.xplane, "draped")

        row = layout.row()

        # v1000 blend / v9000 blend
        if version >= 1000:
            row.prop(obj.xplane, "blend_v1000", text = "Blend")
        else:
            row.prop(obj.xplane, "blend", text = "Use alpha cutoff")

        if obj.xplane.blend == True or obj.xplane.blend_v1000 == 'off':
            row = layout.row()
            row.prop(obj.xplane, "blendRatio", text = "Alpha cutoff ratio")

    row = layout.row()
    row.prop(obj.xplane, "surfaceType", text = "Surface type")

    if obj.xplane.surfaceType != 'none':
        row = layout.row()
        row.prop(obj.xplane, "deck", text = "Deck")

    row = layout.row()
    row.prop(obj.xplane, "solid_camera", text = "Camera collision")

    row = layout.row()
    row.prop(obj.xplane, "poly_os", text = "Polygon offset")
    row = layout.row()

    row.prop(obj.xplane, "lightLevel", text = "Override light level")

    if obj.xplane.lightLevel:
        box = layout.box()
        box.prop(obj.xplane, "lightLevel_v1", text = "Value 1")
        row = box.row()
        row.prop(obj.xplane, "lightLevel_v2", text = "Value 2")
        row = box.row()
        row.prop(obj.xplane, "lightLevel_dataref", text = "Dataref")
        row = box.row()
        row.operator('xplane.dataref_search', text = "Search dataref", emboss = True, icon = "VIEWZOOM")

    row = layout.row()
    box = row.box()
    box.prop(obj.xplane, "litFactor", text = "Night texture preview", slider = True)
    row = box.row()

    if not canPreviewEmit(obj):
        row.label("Add one texture affecting color and one affecting ambient and emit.", icon = "INFO")

    # instancing effects
    instanced_box = layout.box()
    instanced_box.prop(obj.xplane, 'tint', 'Tint (Instanced Scenery only)')

    if obj.xplane.tint:
        instanced_box.prop(obj.xplane, 'tint_albedo')
        instanced_box.prop(obj.xplane, 'tint_emissive')

def canPreviewEmit(mat):
    hasTexture = False
    hasTextureLit = False
    texture, textureLit = getColorAndLitTextureSlots(mat)

    return (texture != None and textureLit != None)

# Function: custom_layout
# Draws the additional UI layout for custom attributes.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   string type - Type of object. ("MESH", "MATERIAL", "LAMP")
def custom_layout(self, obj, type):
    if type in ("MESH", "ARMATURE", "OBJECT"):
        oType = 'object'
    elif type == "MATERIAL":
        oType = 'material'
    elif type == 'LAMP':
        oType = 'lamp'
    else:
        oType = None

    layout = self.layout
    layout.separator()

    if oType:
        # regular attributes
        row = layout.row()
        row.label("Custom Properties")
        row.operator("object.add_xplane_"+oType+"_attribute", text = "Add Property")
        box = layout.box()
        for i, attr in enumerate(obj.xplane.customAttributes):
            subbox = box.box()
            subrow = subbox.row()
            subrow.prop(attr, "name")
            subrow.operator("object.remove_xplane_"+oType+"_attribute", text = "", emboss = False, icon = "X").index = i
            subrow = subbox.row()
            subrow.prop(attr, "value")
            if type in ("MATERIAL", "MESH", "LAMP", "ARMATURE"):
                subrow = subbox.row()
                subrow.prop(attr, "reset")
                subrow = subbox.row()
                subrow.prop(attr, "weight")

        # animation attributes
        if type in ("MESH", "ARMATURE", "OBJECT"):
            row = layout.row()
            row.label("Custom Animation Properties")
            row.operator("object.add_xplane_object_anim_attribute", text = "Add Property")
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
    else:
        row.operator("object.add_xplane_dataref", text = "Add Dataref")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.datarefs):
        subbox = box.box()
        subrow = subbox.row()
        # TODO: search is causing memory leak!
#        if len(bpy.data.scenes[0].xplane_datarefs)>0:
#            subrow.prop_search(attr, "path", bpy.data.scenes[0], "xplane_datarefs", text = "", icon = "VIEWZOOM")
#        else:
#            subrow.prop(attr, "path")
        subrow.prop(attr, "path")
        if bone:
            subrow.operator("bone.remove_xplane_dataref", text = "", emboss = False, icon = "X").index = i
        else:
            subrow.operator("object.remove_xplane_dataref", text = "", emboss = False, icon = "X").index = i
        subrow = subbox.row()
        subrow.operator('xplane.dataref_search', text = "Search dataref", emboss = True, icon = "VIEWZOOM")
        subrow = subbox.row()
        subrow.prop(attr, "anim_type", text = "Animation")
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
                subrow.prop(attr, "loop", text = "Loops")
            else:
                subrow.label('Object not animated.')
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
def cockpit_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, 'panel', text = 'Part of Cockpit panel')

    if obj.xplane.panel:
        row = layout.row()
        row.prop(obj.xplane, 'cockpit_region', text = "Cockpit region")

# Function: manipulator_layout
# Draws the UI layout for manipulator settings.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def manipulator_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane.manip, 'enabled', text = 'Manipulator')

    if obj.xplane.manip.enabled:
        box = layout.box()
        box.prop(obj.xplane.manip, 'type', text = "Type")

        type = obj.xplane.manip.type

        box.prop(obj.xplane.manip, 'cursor', text = "Cursor")
        box.prop(obj.xplane.manip, 'tooltip', text = "Tooltip")

        if type not in (MANIP_COMMAND, MANIP_COMMAND_AXIS, MANIP_COMMAND_KNOB, MANIP_COMMAND_SWITCH_UP_DOWN, MANIP_COMMAND_SWITCH_LEFT_RIGHT):
            if type != MANIP_DRAG_XY:
                box.prop(obj.xplane.manip, 'dataref1', text = "Dataref")
                box.operator('xplane.dataref_search', text = "Search dataref", emboss = True, icon = "VIEWZOOM")
            else:
                box.prop(obj.xplane.manip, 'dataref1', text = "Dataref 1")
                box.prop(obj.xplane.manip, 'dataref2', text = "Dataref 2")
                box.operator('xplane.dataref_search', text = "Search dataref", emboss = True, icon = "VIEWZOOM")

        # drag axis lenghts
        if type in (MANIP_DRAG_XY, MANIP_DRAG_AXIS, MANIP_COMMAND_AXIS):
            box.prop(obj.xplane.manip, 'dx', text = "dx")
            box.prop(obj.xplane.manip, 'dy', text = "dy")

            if type in(MANIP_DRAG_AXIS, MANIP_COMMAND_AXIS):
                box.prop(obj.xplane.manip, 'dz', text = "dz")

        elif type == MANIP_DRAG_AXIS_PIX:
             box.prop(obj.xplane.manip, 'dx', text = "dx")
             box.prop(obj.xplane.manip, 'step', text = "Step")
             box.prop(obj.xplane.manip, 'exp', text = "Exp")

        # values
        if type == MANIP_DRAG_XY:
            box.prop(obj.xplane.manip, 'v1_min', text = "v1 min")
            box.prop(obj.xplane.manip, 'v1_max', text = "v1 max")
            box.prop(obj.xplane.manip, 'v2_min', text = "v2 min")
            box.prop(obj.xplane.manip, 'v2_max', text = "v2 max")
        elif type in (MANIP_DRAG_AXIS, MANIP_DRAG_AXIS_PIX, MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT):
            box.prop(obj.xplane.manip, 'v1', text = "v1")
            box.prop(obj.xplane.manip, 'v2', text = "v2")
        elif type == MANIP_COMMAND:
            box.prop(obj.xplane.manip, MANIP_COMMAND, text = "Command")
        elif type in (MANIP_COMMAND_AXIS, MANIP_COMMAND_KNOB, MANIP_COMMAND_SWITCH_UP_DOWN, MANIP_COMMAND_SWITCH_LEFT_RIGHT):
            box.prop(obj.xplane.manip, 'positive_command', text = "Pos. command")
            box.prop(obj.xplane.manip, 'negative_command', text = "Neg. command")
        elif type == MANIP_PUSH:
            box.prop(obj.xplane.manip, 'v_down', text = "v down")
            box.prop(obj.xplane.manip, 'v_up', text = "v up")
        elif type == MANIP_RADIO:
            box.prop(obj.xplane.manip, 'v_down', text = "v down")
        elif type == MANIP_TOGGLE:
            box.prop(obj.xplane.manip, 'v_on', text = "v On")
            box.prop(obj.xplane.manip, 'v_off', text = "v Off")
        elif type in (MANIP_DELTA, MANIP_WRAP):
            box.prop(obj.xplane.manip, 'v_down', text = "v down")
            box.prop(obj.xplane.manip, 'v_hold', text = "v hold")
            box.prop(obj.xplane.manip, 'v1_min', text = "v min")
            box.prop(obj.xplane.manip, 'v1_max', text = "v max")

        if type in (MANIP_AXIS_SWITCH_UP_DOWN, MANIP_AXIS_SWITCH_LEFT_RIGHT):
            box.prop(obj.xplane.manip, 'click_step')
            box.prop(obj.xplane.manip, 'hold_step')

        # v1050: mouse wheel support
        if type in MOUSE_WHEEL_MANIPULATORS:
            box.prop(obj.xplane.manip, 'wheel_delta')

# Function: conditions_layout
# Draws the UI layout for conditions.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   type - object type
def conditions_layout(self, obj, type):
    layout = self.layout

    type = type.lower()

    # regular attributes
    row = layout.row()
    row.label("Conditions")
    row.operator('object.add_xplane_' + type + '_condition', text = "Add Condition")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.conditions):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr, "variable")
        subrow.operator('object.remove_xplane_' + type + '_condition', text = "", emboss = False, icon = "X").index = i
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

# Function: parseDatarefs
# Parses the DataRefs.txt file which is located within the io_xplane2blender addon directory and stores results in a list.
# This list should later be used to help search for datarefs with an autocomplete field.
#def parseDatarefs():
#    import os
#    search_data = []
#    filePath = os.path.dirname(__file__)+'/DataRefs.txt'
#    if os.path.exists(filePath):
#        try:
#            file = open(filePath, 'r')
#            i = 0
#            for line in file:
#                if i>1:
#                    parts = line.split('\t')
#                    if (len(parts)>1 and parts[1] in ('float', 'int')):
#                        search_data.append(parts[0])
#                i+ = 1
#        except IOError:
#            print(IOError)
#        finally:
#            file.close()
#    return search_data

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
    bl_label = 'XPlane2Blender error'
    msg_type = bpy.props.StringProperty(default = 'ERROR')
    msg_text = bpy.props.StringProperty(default = '')

    def execute(self, context):
        # self.report({self.msg_type}, self.msg_text)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text = self.msg_type+': '+self.msg_text)


class XPlaneDatarefSearch(bpy.types.Operator):
    bl_label = 'XPlane dataref search'
    bl_description = 'Search for XPlane dataref'
    bl_idname = 'xplane.dataref_search'

    #datarefs = parseDatarefs()

    def execute(self, context):
        import webbrowser
        webbrowser.open('http://xplane.anzui.de/dataref-search/')
        return {'FINISHED'}

#    def invoke(self, context, event):
#        wm = context.window_manager
#        return wm.invoke_popup(operator = self)
#
#    def draw(self, context):
#        layout = self.layout
#        row = layout.row()
#        row.label('Search Datarefs')
#        layout.separator()
#        box = layout.box()
#        datarefs = parseDatarefs()
#        for dataref in datarefs:
#            #subrow = box.row()
#            subrow.label(dataref)
#
##        return {'FINISHED'}

# Function: addXPlaneUI
# Registers all UI Panels.
def addXPlaneUI():
#    datarefs = parseDatarefs()
#
#    for dataref in datarefs:
#        prop = bpy.data.scenes[0].xplane_datarefs.add()
#        prop.name = dataref

    bpy.utils.register_class(BONE_PT_xplane)
    bpy.utils.register_class(LAMP_PT_xplane)
    bpy.utils.register_class(MATERIAL_PT_xplane)
    bpy.utils.register_class(OBJECT_PT_xplane)
    bpy.utils.register_class(SCENE_PT_xplane)
    bpy.utils.register_class(XPlaneMessage)
    bpy.utils.register_class(XPlaneError)
    bpy.utils.register_class(XPlaneDatarefSearch)

# Function: removeXPlaneUI
# Unregisters all UI Panels.
def removeXPlaneUI():
    bpy.utils.unregister_class(BONE_PT_xplane)
    bpy.utils.unregister_class(LAMP_PT_xplane)
    bpy.utils.unregister_class(MATERIAL_PT_xplane)
    bpy.utils.unregister_class(OBJECT_PT_xplane)
    bpy.utils.unregister_class(SCENE_PT_xplane)
    bpy.utils.unregister_class(XPlaneMessage)
    bpy.utils.unregister_class(XPlaneError)
    bpy.utils.unregister_class(XPlaneDatarefSearch)
