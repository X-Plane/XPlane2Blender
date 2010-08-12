import bpy

def add_xplane_properties(obj):
	obj.BoolProperty(attr="xplane_use",description="If set, this object will be used in the X-Plane export.",default=False,options={'HIDDEN'})
	obj.BoolProperty(attr="xplane_export",description="If set, the children of this object will be exported into a single X-Plane obj-file.",default=False,options={'HIDDEN'})
	obj.StringProperty(attr="xplane_export_file",description="Path to the X-Plane obj-file to be exported.",default="",options={'HIDDEN'},subtype="FILE_PATH")
	obj.StringProperty(attr="xplane_dataref",description="A X-Plane Dataref",default="",options={'HIDDEN'})

class OBJECT_PT_xplane(bpy.types.Panel):
	'''XPlane Object Panel'''
	bl_label = "XPlane"
	bl_space_type = "PROPERTIES"
	bl_region_type = "WINDOW"
	bl_context = "object"

	def draw(self, context):
		obj = context.object

		add_xplane_properties(obj)
		#load_xplane_properties(obj)

		if(obj.type=="EMPTY"):
			default_layout(self, obj)

			if(obj.xplane_use):
				export_layout(self, obj)
			
		elif(obj.type=="MESH"):
			default_layout(self, obj)

			if(obj.xplane_use):
				dataref_layout(self, obj)

		elif(obj.type=="LAMP"):
			default_layout(self, obj)

			if(obj.xplane_use):
				dataref_layout(self, obj)
			
		elif(obj.type=="BONE"):
			default_layout(self, obj)

			if(obj.xplane_use):
				dataref_layout(self, obj)


def default_layout(self, obj):
	if(obj.xplane_use==False):
		checkboxIcon = "CHECKBOX_DEHLT"
	elif(obj.xplane_use==True):
		checkboxIcon = "CHECKBOX_HLT"

	layout = self.layout
	row = layout.row()
	row.prop(obj, "xplane_use",text="Use for X-Plane Export",icon=checkboxIcon,toggle=True)

	row = layout.row()
	row.separator()


def dataref_layout(self, obj):
	layout = self.layout
	row = layout.row()
	row.prop(obj, "xplane_dataref",text="Dataref")


def export_layout(self, obj):
	if(obj.xplane_export==False):
		checkboxIcon = "CHECKBOX_DEHLT"
	elif(obj.xplane_export==True):
		checkboxIcon = "CHECKBOX_HLT"

	layout = self.layout
	row = layout.row()
	row.prop(obj, "xplane_export",text="Export all children into single file",icon=checkboxIcon,toggle=True)

	if(obj.xplane_export):
		# set default file name to object name
		if(obj.xplane_export_file==''):
			obj.xplane_export_file = bpy.context.active_object.name+'.obj'
		
		# check if filename ends with .obj, if not append it
		if (obj.xplane_export_file[-4:len(obj.xplane_export_file)]!='.obj'):
			obj.xplane_export_file+='.obj'
			
		row = layout.row()
		row.prop(obj, "xplane_export_file",icon="FILE_BLANK")
