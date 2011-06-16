# File: xplane_ui.py
# Creates the User Interface for all X-Plane settings.

import bpy
from io_xplane2blender.xplane_ops import *
from io_xplane2blender.xplane_config import *

# Class: LAMP_PT_xplane
# Adds X-Plane lamp settings to the lamp tab. Uses <lamp_layout> and <custom_layout>.
class LAMP_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self,context):
        obj = context.object

        if(obj.type == "LAMP"):
            lamp_layout(self,obj.data)
            custom_layout(self,obj.data,"LAMP")
    
# Class: MATERIAL_PT_xplane
# Adds X-Plane Material settings to the material tab. Uses <material_layout> and <custom_layout>.
class MATERIAL_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(self,context):
        if context.material:
            return True

    def draw(self,context):
        obj = context.object

        if(obj.type == "MESH"):
            material_layout(self,obj.active_material)
            custom_layout(self,obj.active_material,"MATERIAL")

# Class: SCENE_PT_xplane
# Adds X-Plane Layer settings to the scene tab. Uses <scene_layout>.
class SCENE_PT_xplane(bpy.types.Panel):
    '''XPlane Scene Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(self,context):
        return True

    def draw(self,context):
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
    def poll(self,context):
        obj = context.object

        if obj.type in ("MESH","EMPTY","ARMATURE","LAMP"):
            return True
        else:
            return False

    def draw(self, context):
        obj = context.object
        
        if obj.type in ("MESH","EMPTY","ARMATURE","LAMP"):
            animation_layout(self,obj)
            if obj.type == "MESH":
                mesh_layout(self,obj)
                cockpit_layout(self,obj)
                manipulator_layout(self,obj)
            type = obj.type
            if type=="LAMP":
                type = "OBJECT"
            lod_layout(self,obj)
            weight_layout(self,obj)
            custom_layout(self,obj,type)
            

# Class: BONE_PT_xplane
# Adds X-Plane settings to the bone tab. Uses <animation_layout>.
class BONE_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"

    @classmethod
    def poll(self,context):
        bone = context.bone
        
        if bone:
            return True
        else:
            return False

    def draw(self, context):
        bone = context.bone
        obj = context.object
        animation_layout(self,bone,True)

# Class: OBJECT_MT_xplane_datarefs
# Adds the X-Plane datarefs search menu. This is not implemented yet.
class OBJECT_MT_xplane_datarefs(bpy.types.Menu):
    '''XPlane Datarefs Search Menu'''
    bl_label = "XPlane Datarefs"

    def draw(self,context):
        self.search_menu(xplane_datarefs,"text.open")

# Function: scene_layout
# Draws the UI layout for scene tabs. Uses <layer_layout>.
#
# Parameters:
#   self - Instance of current panel class.
#   scene - Blender scene.
def scene_layout(self, scene):
    layout = self.layout
    row = layout.row()
    row.prop(scene.xplane,"optimize",text="Optimize")

    row = layout.row()
    row.prop(scene.xplane,"debug",text="Debug")

    if scene.xplane.debug:
        box = layout.box()
        box.prop(scene.xplane,"profile",text="Profiling")
        box.prop(scene.xplane,"log",text="Log")

    row = layout.row()

    if len(scene.xplane.layers)!=0:
        for i in range(0,len(scene.layers)):
            row = layout.row()
            layer_layout(self, scene, row, i)
    else:
        row.operator('scene.add_xplane_layers')
        
# Function: layer_layout
# Draws the UI layout for <XPlaneLayers>. Uses <custom_layer_layout>.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   scene - Blender scene
#   UILayout layout - Instance of sublayout to use.
#   int layer - <XPlaneLayer> index.
def layer_layout(self, scene, layout, layer):
    box = layout.box()
    li = str(layer+1)

    if scene.xplane.layers[layer].expanded:
        expandIcon = "TRIA_DOWN"
        expanded = True
    else:
        expandIcon = "TRIA_RIGHT"
        expanded = False
        
    box.prop(scene.xplane.layers[layer],"expanded", text="Layer "+li, expand=True, emboss=False, icon=expandIcon)

    if expanded:
        column = box.column()
        column.prop(scene.xplane.layers[layer],"export", text="Export")
        column.prop(scene.xplane.layers[layer],"name", text="Name")
        
        if scene.xplane.layers[layer].cockpit:
            checkboxIcon = "CHECKBOX_HLT"
        else:
            checkboxIcon = "CHECKBOX_DEHLT"

        column.label('Textures')
        tex_box = column.box()
        tex_box.prop(scene.xplane.layers[layer], "texture", text="Default")
        tex_box.prop(scene.xplane.layers[layer], "texture_lit", text="Night")
        tex_box.prop(scene.xplane.layers[layer], "texture_normal", text="Normal / Specular")
        column.prop(scene.xplane.layers[layer], "cockpit", text="Cockpit",icon=checkboxIcon, toggle=True)

        # cockpit regions
        if scene.xplane.layers[layer].cockpit:
            cockpit_box = column.box()
            #cockpit_box.prop(scene.xplane.layers[layer],"panel_texture", text="Panel Texture")
            cockpit_box.prop(scene.xplane.layers[layer],"cockpit_regions", text="Cockpit regions")
            num_regions = int(scene.xplane.layers[layer].cockpit_regions)
            if num_regions>0:
                for i in range(0,num_regions):
                    # get cockpit region or create it if not present
                    if len(scene.xplane.layers[layer].cockpit_region)>i:
                        cockpit_region = scene.xplane.layers[layer].cockpit_region[i]
                    else:
                        cockpit_region = scene.xplane.layers[layer].cockpit_region.add()

                    if cockpit_region.expanded:
                        expandIcon = "TRIA_DOWN"
                    else:
                        expandIcon = "TRIA_RIGHT"

                    region_box = cockpit_box.box()
                    region_box.prop(cockpit_region,"expanded",text="Cockpit region %i" % (i+1), expand=True, emboss=False, icon=expandIcon)

                    if cockpit_region.expanded:
                        region_box.prop(cockpit_region,"left")
                        region_box.prop(cockpit_region,"top")
                        region_split = region_box.split(percentage=0.5)
                        region_split.prop(cockpit_region,"width")
                        region_split.label("= %d" % (2 ** cockpit_region.width))
                        region_split = region_box.split(percentage=0.5)
                        region_split.prop(cockpit_region,"height")
                        region_split.label("= %d" % (2 ** cockpit_region.height))

        # LODs
        if scene.xplane.layers[layer].cockpit==False:
            lods_box = column.box()
            lods_box.prop(scene.xplane.layers[layer],"lods", text="Levels of detail")
            num_lods = int(scene.xplane.layers[layer].lods)
            if num_lods>0:
                for i in range(0,num_lods):
                    # get lod or create it if not present
                    if len(scene.xplane.layers[layer].lod)>i:
                        lod = scene.xplane.layers[layer].lod[i]
                    else:
                        lod = scene.xplane.layers[layer].lod.add()

                    if lod.expanded:
                        expandIcon = "TRIA_DOWN"
                    else:
                        expandIcon = "TRIA_RIGHT"

                    lod_box = lods_box.box()
                    lod_box.prop(lod,"expanded",text="Level of detail %i" % (i+1), expand=True, emboss=False, icon=expandIcon)

                    if lod.expanded:
                        lod_box.prop(lod,"near")
                        lod_box.prop(lod,"far")

        column.separator()
        column.prop(scene.xplane.layers[layer], "slungLoadWeight", text="Slung Load weight")
        
        custom_layer_layout(self, box, scene, layer)

# Function: custom_layer_layout
# Draws the UI layout for the custom attributes of a <XPlaneLayer>.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   UILayout layout - Instance of sublayout to use.
#   scene - Blender scene
#   int layer - <XPlaneLayer> index.
def custom_layer_layout(self,layout, scene, layer):
    layout.separator()
    row = layout.row()
    row.label("Custom Properties")
    row.operator("scene.add_xplane_layer_attribute", text="Add Property").index = layer
    box = layout.box()
    for i, attr in enumerate(scene.xplane.layers[layer].customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr,"name")
        subrow.prop(attr,"value")
        subrow.operator("scene.remove_xplane_layer_attribute",text="",emboss=False,icon="X").index = (layer,i)
        if type in ("MATERIAL","MESH"):
            subrow = subbox.row()
            subrow.prop(attr,"reset")
    
# Function: mesh_layout
# Draws the additional UI layout for Mesh-Objects. This includes light-level and depth-culling.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def mesh_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "depth", text="Use depth culling")
    row = layout.row()
    row.prop(obj.xplane, "poly_os", text="Polygon offset")
    row = layout.row()

    row.prop(obj.xplane,"lightLevel", text="Override light level")

    if obj.xplane.lightLevel:
        box = layout.box()
        box.prop(obj.xplane,"lightLevel_v1",text="Value 1")
        row = box.row()
        row.prop(obj.xplane,"lightLevel_v2",text="Value 2")
        row = box.row()
        row.prop(obj.xplane,"lightLevel_dataref",text="Dataref")
        row = box.row()
        row.operator('xplane.dataref_search',text="Search dataref",emboss=True,icon="VIEWZOOM")

# Function: lamp_layout
# Draws the UI layout for lamps.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def lamp_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "type", text="Type")

    if obj.xplane.type in ("named","param"):
        row = layout.row()
        row.prop(obj.xplane,"name",text="Name")
        if obj.xplane.type=="param":
            row = layout.row()
            row.prop(obj.xplane,"params",text="Parameters")
    elif obj.xplane.type=="custom":
        row = layout.row()
        row.prop(obj.xplane,"size",text="Size")
        row = layout.row()
        row.label("Texture coordinates:")
        row = layout.row()
        row.prop(obj.xplane,"uv",text="")
        row = layout.row()
        row.prop(obj.xplane,"dataref",text="Dataref")
        row = layout.row()
        row.operator('xplane.dataref_search',text="Search dataref",emboss=True,icon="VIEWZOOM")

# Function: material_layout
# Draws the UI layout for materials.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def material_layout(self, obj):
    layout = self.layout

    row = layout.row()
    row.prop(obj.xplane, "draw", text="Draw")

    if (obj.xplane.draw):
        row = layout.row()
        row.prop(obj.xplane, "overrideSpecularity", text="Override specularity")

        if obj.xplane.overrideSpecularity:
            row = layout.row()
            row.prop(obj.xplane, "shinyRatio", text="Shiny ratio")

        row = layout.row()
        row.prop(obj.xplane, "blend", text="Use alpha cutoff")

        if(obj.xplane.blend==True):
            row = layout.row()
            row.prop(obj.xplane, "blendRatio", text="Alpha cutoff ratio")

    row = layout.row()
    row.prop(obj.xplane, "surfaceType", text="Surface type")

    if obj.xplane.surfaceType!='none':
        row = layout.row()
        row.prop(obj.xplane,"deck",text="Deck")

    row = layout.row()
    row.prop(obj.xplane,"solid_camera",text="Camera collision")

# Function: custom_layout
# Draws the additional UI layout for custom attributes.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   string type - Type of object. ("MESH","MATERIAL","LAMP")
def custom_layout(self,obj,type):
    if type in ("MESH","ARMATURE","OBJECT"):
        oType = 'object'
    elif type=="MATERIAL":
        oType = 'material'
    elif type=='LAMP':
        oType = 'lamp'

    layout = self.layout
    layout.separator()

    # regular attributes
    row = layout.row()
    row.label("Custom Properties")
    row.operator("object.add_xplane_"+oType+"_attribute", text="Add Property")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr,"name")
        subrow.operator("object.remove_xplane_"+oType+"_attribute",text="",emboss=False,icon="X").index = i
        subrow = subbox.row()
        subrow.prop(attr,"value")
        if type in ("MATERIAL","MESH","LAMP","ARMATURE"):
            subrow = subbox.row()
            subrow.prop(attr,"reset")
            subrow = subbox.row()
            subrow.prop(attr,"weight")

    # animation attributes
    if type in ("MESH","ARMATURE","OBJECT"):
        row = layout.row()
        row.label("Custom Animation Properties")
        row.operator("object.add_xplane_object_anim_attribute", text="Add Property")
        box = layout.box()
        for i, attr in enumerate(obj.xplane.customAnimAttributes):
            subbox = box.box()
            subrow = subbox.row()
            subrow.prop(attr,"name")
            subrow.operator("object.remove_xplane_object_anim_attribute",text="",emboss=False,icon="X").index = i
            subrow = subbox.row()
            subrow.prop(attr,"value")
            subrow = subbox.row()
            subrow.prop(attr,"weight")
    
# Function: animation_layout
# Draws the UI layout for animations. This includes Datarefs.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
#   bool bone - True if the object is a bone.
def animation_layout(self,obj,bone = False):
    layout = self.layout
    layout.separator()
    row = layout.row()
    row.label("Datarefs")
    if bone:
        row.operator("bone.add_xplane_dataref", text="Add Dataref")
    else:
        row.operator("object.add_xplane_dataref", text="Add Dataref")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.datarefs):
        subbox = box.box()
        subrow = subbox.row()
        # TODO: search is causing memory leak!
#        if len(bpy.data.scenes[0].xplane_datarefs)>0:
#            subrow.prop_search(attr,"path",bpy.data.scenes[0],"xplane_datarefs",text="",icon="VIEWZOOM")
#        else:
#            subrow.prop(attr,"path")
        subrow.prop(attr,"path")
        if bone:
            subrow.operator("bone.remove_xplane_dataref",text="",emboss=False,icon="X").index = i
        else:
            subrow.operator("object.remove_xplane_dataref",text="",emboss=False,icon="X").index = i
        subrow = subbox.row()
        subrow.operator('xplane.dataref_search',text="Search dataref",emboss=True,icon="VIEWZOOM")
        subrow = subbox.row()
        subrow.prop(attr,"anim_type",text="Animation")
        subrow = subbox.row()

        if attr.anim_type=='transform':
            if bone:
                subrow.operator("bone.add_xplane_dataref_keyframe",text="",icon="KEY_HLT").index = i
                subrow.operator("bone.remove_xplane_dataref_keyframe",text="",icon="KEY_DEHLT").index = i
            else:
                subrow.operator("object.add_xplane_dataref_keyframe",text="",icon="KEY_HLT").index = i
                subrow.operator("object.remove_xplane_dataref_keyframe",text="",icon="KEY_DEHLT").index = i
            subrow.prop(attr,"value")
            subrow = subbox.row()
            subrow.prop(attr,"loop",text="Loops")
        elif attr.anim_type in ("show","hide"):
            subrow.prop(attr,"show_hide_v1")
            subrow = subbox.row()
            subrow.prop(attr,"show_hide_v2")

# Function: cockpit_layout
# Draws the UI layout for cockpit parameters. This includes panel.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def cockpit_layout(self,obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane,'panel',text='Part of Cockpit panel')

    if obj.xplane.panel:
        row = layout.row()
        row.prop(obj.xplane,'cockpit_region',text="Cockpit region")

# Function: manipulator_layout
# Draws the UI layout for manipulator settings.
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def manipulator_layout(self,obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane.manip,'enabled',text='Manipulator')

    if obj.xplane.manip.enabled:
        box = layout.box()
        box.prop(obj.xplane.manip,'type',text="Type")

        type = obj.xplane.manip.type
        
        box.prop(obj.xplane.manip,'cursor',text="Cursor")
        box.prop(obj.xplane.manip,'tooltip',text="Tooltip")

        if type!='drag_xy':
            box.prop(obj.xplane.manip,'dataref1',text="Dataref")
            box.operator('xplane.dataref_search',text="Search dataref",emboss=True,icon="VIEWZOOM")
        else:
            box.prop(obj.xplane.manip,'dataref1',text="Dataref 1")
            box.prop(obj.xplane.manip,'dataref2',text="Dataref 2")
            box.operator('xplane.dataref_search',text="Search dataref",emboss=True,icon="VIEWZOOM")

        # drag axis lenghts
        if type in ('drag_xy','drag_axis','command_axis'):
            box.prop(obj.xplane.manip,'dx',text="dx")
            box.prop(obj.xplane.manip,'dy',text="dy")
            if type in('drag_axis','command_axis'):
                box.prop(obj.xplane.manip,'dz',text="dz")

        # values
        if type=='drag_xy':
            box.prop(obj.xplane.manip,'v1_min',text="v1 min")
            box.prop(obj.xplane.manip,'v1_max',text="v1 max")
            box.prop(obj.xplane.manip,'v2_min',text="v2 min")
            box.prop(obj.xplane.manip,'v2_max',text="v2 max")
        elif type=='drag_axis':
            box.prop(obj.xplane.manip,'v1',text="v1")
            box.prop(obj.xplane.manip,'v2',text="v2")
        elif type=='command':
            box.prop(obj.xplane.manip,'command',text="Command")
        elif type=='command_axis':
            box.prop(obj.xplane.manip,'positive_command',text="Pos. command")
            box.prop(obj.xplane.manip,'negative_command',text="Neg. command")
        elif type=='push':
            box.prop(obj.xplane.manip,'v_down',text="v down")
            box.prop(obj.xplane.manip,'v_up',text="v up")
        elif type=='radio':
            box.prop(obj.xplane.manip,'v_down',text="v down")
        elif type=='toggle':
            box.prop(obj.xplane.manip,'v_on',text="v On")
            box.prop(obj.xplane.manip,'v_off',text="v Off")
        elif type in ('delta','wrap'):
            box.prop(obj.xplane.manip,'v_down',text="v down")
            box.prop(obj.xplane.manip,'v_hold',text="v hold")
            box.prop(obj.xplane.manip,'v1_min',text="v min")
            box.prop(obj.xplane.manip,'v1_max',text="v max")

# Function: lod_layout
# Draws the UI for Levels of detail
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def lod_layout(self,obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane,"lod",text="LOD")

# Function: weight_layout
# Draws the UI for Object weight
#
# Parameters:
#   UILayout self - Instance of current UILayout.
#   obj - Blender object.
def weight_layout(self,obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane,'override_weight')
    if obj.xplane.override_weight:
        row.prop(obj.xplane,'weight')

# Function: parseDatarefs
# Parses the DataRefs.txt file which is located within the io_xplane2blender addon directory and stores results in a list.
# This list should later be used to help search for datarefs with an autocomplete field.
#def parseDatarefs():
#    import os
#    search_data = []
#    filePath = os.path.dirname(__file__)+'/DataRefs.txt'
#    if os.path.exists(filePath):
#        try:
#            file = open(filePath,'r')
#            i = 0
#            for line in file:
#                if i>1:
#                    parts = line.split('\t')
#                    if (len(parts)>1 and parts[1] in ('float','int')):
#                        search_data.append(parts[0])
#                i+=1
#        except IOError:
#            print(IOError)
#        finally:
#            file.close()
#    return search_data


# Function: showError
# Draws a window displaying an error message.
#
# Parameters:
#   string message - The message to display.
#
# Todos:
#   - Not working at all.
def showError(message):
    bpy.ops.xplane.error(
        'INVOKE_DEFAULT',
        msg_text=message
    )
    setErrors(True)

# Function: showProgress
# Draws a progress bar together with a message.
#
# Parameters:
#   float progress - value between 0 and 1 indicating the current progress.
#   string message - An aditional message to display.
#
# Todos:
#   - Not working at all.
def showProgress(progress,message):
    bpy.ops.xplane.msg(
        'INVOKE_DEFAULT',
        msg_text='%s - %s' % (str(round(progress*100))+'%',message)
    )

class XPlaneMessage(bpy.types.Operator):
    bl_idname = 'xplane.msg'
    bl_label = 'XPlane2Blender message'
    msg_type = bpy.props.StringProperty(default='INFO')
    msg_text = bpy.props.StringProperty(default='')
    def execute(self, context):
        self.report(self.msg_type, self.msg_text)
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.msg_type+': '+self.msg_text)


class XPlaneError(bpy.types.Operator):
    bl_idname = 'xplane.error'
    bl_label = 'XPlane2Blender error'
    msg_type = bpy.props.StringProperty(default='ERROR')
    msg_text = bpy.props.StringProperty(default='')

    def execute(self, context):
        self.report(self.msg_type, self.msg_text)
        return {'FINISHED'}

    def invoke(self,context,event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.msg_type+': '+self.msg_text)


class XPlaneDatarefSearch(bpy.types.Operator):
    bl_label = 'XPlane dataref search'
    bl_description = 'Search for XPlane dataref'
    bl_idname = 'xplane.dataref_search'

    #datarefs = parseDatarefs()

    def execute(self,context):
        import webbrowser
        webbrowser.open('http://www.anzui.de/xplane/dataref-search/dataref-search.php')
        return {'FINISHED'}

#    def invoke(self,context,event):
#        wm = context.window_manager
#        return wm.invoke_popup(operator=self)
#
#    def draw(self,context):
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