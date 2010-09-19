import bpy

class XPlaneObjectSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneMaterialSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLampSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneCustomAttribute(bpy.types.IDPropertyGroup):
    pass

class OBJECT_OT_add_xplane_header_attribute(bpy.types.Operator):
    bl_label = 'Add Header Attribute'
    bl_idname = 'object.add_xplane_header_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane header Property'

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_header_attribute(bpy.types.Operator):
    bl_label = 'Remove Header Attribute'
    bl_idname = 'object.remove_xplane_header_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane header Property'
    
    index = bpy.props.IntProperty()
    
    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

def addXPlaneRNA():
    bpy.types.Object.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")

    # custom Attributes
    XPlaneCustomAttribute.name = bpy.props.StringProperty(attr="name",
                                        name="Name",
                                        description="Name",
                                        default="")

    XPlaneCustomAttribute.value = bpy.props.StringProperty(attr="value",
                                        name="Value",
                                        description="Value",
                                        default="")

    XPlaneCustomAttribute.reset = bpy.props.StringProperty(attr="reset",
                                        name="Reset",
                                        description="Reset",
                                        default="")

    # Empty settings
    XPlaneObjectSettings.exportChildren = bpy.props.BoolProperty(attr="exportChildren",
                                name="Export Children",
                                description="Export children of this to X-Plane.",
                                default = False)

    XPlaneObjectSettings.slungLoadWeight = bpy.props.FloatProperty(attr="slungLoadWeight",
                                name="Slung Load weight",
                                description="Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter.",
                                default=0.0,
                                step=1,
                                precision=3)

    XPlaneObjectSettings.customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane header attributes",
                                      description="User defined header attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

#    XPlaneObjectSettings.dataref = bpy.props.StringProperty(attr="dataref",
#                                        name="X-Plane Dataref",
#                                        description="X-Plane Dataref",
#                                        default="")

    XPlaneObjectSettings.depth = bpy.props.BoolProperty(attr="depth",
                                      name="Use depth culling",
                                      description="If unchecked the renderer will perform no depth check on this object.",
                                      default=True)
    

    # Lamp settings
    XPlaneLampSettings.lightType = bpy.props.EnumProperty(attr="lightType",
                                name="Light type",
                                description="Defines the type of the light in X-Plane.",
                                default = "default",
                                items=[("default","default","default"),
                                        ("flashing","flashing","flashing"),
                                        ("pulsing","pulsing","pulsing"),
                                        ("strobe","strobe","strobe"),
                                        ("traffic","traffic","traffic")])

    
    # Material settings
    XPlaneMaterialSettings.surfaceType = bpy.props.EnumProperty(attr='surfaceType',
                                        name='Surface type',
                                        description='Controls the bumpiness of material in X-Plane.',
                                        default='none',
                                        items=[('none','none','none'),
                                                ('water','water','water'),
                                                ('concrete','concrete','concrete'),
                                                ('asphalt','asphalt','asphalt'),
                                                ('grass','grass','grass'),
                                                ('dirt','dirt','dirt'),
                                                ('gravel','gravel','gravel'),
                                                ('lakebed','lakebed','lakebed'),
                                                ('snow','snow','snow'),
                                                ('shoulder','shoulder','shoulder'),
                                                ('blastpad','blastpad','blastpad')])

    XPlaneMaterialSettings.blend = bpy.props.BoolProperty(attr="blend",
                                        name="Use Alpha cutoff",
                                        description="If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio.",
                                        default=False)

    XPlaneMaterialSettings.blendRatio = bpy.props.FloatProperty(attr="blendRatio",
                                        name="Alpha cutoff ratio",
                                        description="Alpha levels in the texture below this level are rendered as fully transparent and alpha levels above this level are fully opaque.",
                                        default=0.5,
                                        step=0.1,
                                        precision=2,
                                        max=1.0,
                                        min=0.0)


def removeXPlaneRNA():
    bpy.types.Object.RemoveProperty("xplane")
    bpy.types.Material.RemoveProperty("xplane")
    bpy.types.Lamp.RemoveProperty("xplane")