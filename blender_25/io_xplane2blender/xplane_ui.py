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
    

class OBJECT_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        obj = context.object
        
        if(obj.type == "EMPTY"):
            empty_layout(self, obj)
        else:
            if obj.type == "MESH":
                mesh_layout(self,obj)
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

    row = layout.row()
    row.label("Custom Header Properties")
    row = layout.row()
    box = row.box()
    for attr in obj.xplane.customHeaderAttributes:
        subrow = box.row()
        subrow.prop(attr,"customAttribute")
    #row.prop(obj.xplane, "customHeaderAttributes", text="Custom Header Attributes")

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


def animation_layout(self,obj):
    layout = self.layout

    row = layout.row()
    row.label("Animation")
    box = row.box()
    subrow = box.row()
    subrow.prop(obj.xplane, "dataref", text="Dataref")

def addXPlaneUI():
    print("adding xplane ui")
#    bpy.types.register(OBJECT_PT_xplane)
#    bpy.types.register(MATERIAL_PT_xplane)
#    bpy.types.register(LAMP_PT_xplane)

def removeXPlaneUI():
    print("removing xplane ui")
#    bpy.types.unregister(OBJECT_PT_xplane)
#    bpy.types.unregister(MATERIAL_PT_xplane)
#    bpy.types.unregister(LAMP_PT_xplane)