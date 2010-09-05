import bpy

class OBJECT_PT_xplane(bpy.types.Panel):
    '''XPlane Object Panel'''
    bl_label = "XPlane"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        obj = context.object
		#load_xplane_properties(obj)
        
        if(obj.type == "EMPTY"):
            empty_layout(self, obj)
            
#			if(obj.xplane_use):
#				export_layout(self, obj)
    
        elif(obj.type == "MESH"):
            pass
            #default_layout(self, obj)

    #			if(obj.xplane_use):
    #				dataref_layout(self, obj)

        elif(obj.type == "LAMP"):
            lamp_layout(self, obj)

        elif(obj.type == "BONE"):
            pass
            #default_layout(self, obj)

#			if(obj.xplane_use):
#				dataref_layout(self, obj)


def empty_layout(self, obj):
    if obj.xplane.exportChildren:
        checkboxIcon = "CHECKBOX_HLT"
    else:
        checkboxIcon = "CHECKBOX_DEHLT"

    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "exportChildren", text="Export Children", icon=checkboxIcon, toggle=True)

def lamp_layout(self, obj):
    layout = self.layout
    row = layout.row()
    row.prop(obj.xplane, "lightType", text="Light type")

#def dataref_layout(self, obj):
#	layout = self.layout
#	row = layout.row()
#	row.prop(obj, "xplane_dataref",text="Dataref")
#
#
#def export_layout(self, obj):
#	if(obj.xplane_export==False):
#		checkboxIcon = "CHECKBOX_DEHLT"
#	elif(obj.xplane_export==True):
#		checkboxIcon = "CHECKBOX_HLT"
#
#	layout = self.layout
#	row = layout.row()
#	row.prop(obj, "xplane_export",text="Export all children into single file",icon=checkboxIcon,toggle=True)
#
#	if(obj.xplane_export):
#		# set default file name to object name
#		if(obj.xplane_export_file==''):
#			obj.xplane_export_file = bpy.context.active_object.name+'.obj'
#
#		# check if filename ends with .obj, if not append it
#		if (obj.xplane_export_file[-4:len(obj.xplane_export_file)]!='.obj'):
#			obj.xplane_export_file+='.obj'
#
#		row = layout.row()
#		row.prop(obj, "xplane_export_file",icon="FILE_BLANK")
