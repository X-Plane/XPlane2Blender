import bpy

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
    

class MATERIAL_PT_xplane(bpy.types.Panel):
    '''XPlane Material Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    def draw(self,context):
        obj = context.object

        if(obj.type == "MESH"):
            material_layout(self,obj.active_material)
            custom_layout(self,obj.active_material,"MATERIAL")
    

class OBJECT_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(self,context):
        obj = context.object

        if(obj.type in ("EMPTY","MESH")):
            return True
        else:
            return False

    def draw(self, context):
        obj = context.object
        
        if(obj.type == "EMPTY"):
            empty_layout(self, obj)
            custom_layout(self,obj,obj.type)
        else:
            if obj.type == "MESH":
                mesh_layout(self,obj)
                custom_layout(self,obj,obj.type)
            if obj.type in ("MESH","BONE","LAMP"):
                animation_layout(self,obj)
        

def empty_layout(self, obj):
    if obj.xplane.exportChildren:
        checkboxIcon = "CHECKBOX_HLT"
    else:
        checkboxIcon = "CHECKBOX_DEHLT"

    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "exportChildren", text="Export Children", icon=checkboxIcon, toggle=True)

    row = layout.row()
    row.prop(obj.xplane, "slungLoadWeight", text="Slung Load weight")

def mesh_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "depth", text="Use depth culling")

def lamp_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "lightType", text="Light type")

def material_layout(self, obj):
    layout = self.layout

    row = layout.row()
    row.prop(obj.xplane, "surfaceType", text="Surface type")

    row = layout.row()
    row.prop(obj.xplane, "blend", text="Use alpha cutoff")

    if(obj.xplane.blend==True):
        row = layout.row()
        row.prop(obj.xplane, "blendRatio", text="Alpha cutoff ratio")


def custom_layout(self,obj,type):
    if type in ("EMPTY","MESH"):
        oType = 'object'
    elif type=="MATERIAL":
        oType = 'material'
    elif type=='LAMP':
        oType = 'lamp'

    layout = self.layout
    layout.separator()
    row = layout.row()
    row.label("Custom Properties")
    row.operator("object.add_xplane_"+oType+"_attribute", text="Add Property")
    box = layout.box()
    for i, attr in enumerate(obj.xplane.customAttributes):
        subbox = box.box()
        subrow = subbox.row()
        subrow.prop(attr,"name")
        subrow.prop(attr,"value")
        subrow.operator("object.remove_xplane_"+oType+"_attribute",text="",emboss=False,icon="X").index = i
        if type in ("MATERIAL","MESH"):
            subrow = subbox.row()
            subrow.prop(attr,"reset")    
    

def animation_layout(self,obj):
    layout = self.layout

    row = layout.row()
    row.label("Animation")
    box = row.box()
#    subrow = box.row()
#    subrow.prop(obj.xplane, "dataref", text="Dataref")

def addXPlaneUI():
    pass
#    bpy.types.register(OBJECT_PT_xplane)
#    bpy.types.register(MATERIAL_PT_xplane)
#    bpy.types.register(LAMP_PT_xplane)

def removeXPlaneUI():
    pass
#    bpy.types.unregister(OBJECT_PT_xplane)
#    bpy.types.unregister(MATERIAL_PT_xplane)
#    bpy.types.unregister(LAMP_PT_xplane)