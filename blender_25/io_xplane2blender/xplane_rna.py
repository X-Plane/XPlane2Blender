import bpy

class XPlaneObjectSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneMaterialSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLampSettings(bpy.types.IDPropertyGroup):
    pass

#class XPlaneCustomAttributeWrapper(bpy.types.IDPropertyGroup):
#    pass
#
#class XPlaneCustomAttribute(bpy.types.IDPropertyGroup):
#    pass

class OBJECT_OP_addXPlaneHeaderAttribute(bpy.types.Operator):
    bl_label = 'Add Header Attribute'
    bl_idname = 'object.add_xplane_header_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane header Property'

    def execute(self,context):
        obj = context.object
        #obj.xplane.customHeaderAttributes.collection.append(XPlaneCustomAttribute())
        #obj.xplane.customAttributes.items().append({"name":"","value":""})
        return {'FINISHED'}

def addXPlaneRNA():
    #bpy.ops.register(OBJECT_OP_addXPlaneHeaderAttribute)
    bpy.types.Object.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")
    #bpy.types.register(XPlaneCustomAttribute)
    
    # custom Attribute
#    bpy.types.Object.PointerProperty(attr="xplane_custom",type=XPlaneCustomAttribute, name="Custom XPlane Attribute", description="Custom XPlane Attribute")
#
#    XPlaneCustomAttribute.StringProperty(attr="name",
#                                        name="Name",
#                                        description="Name",
#                                        default="")
#
#    XPlaneCustomAttribute.StringProperty(attr="value",
#                                        name="Value",
#                                        description="Value",
#                                        default="")

    # Empty settings
    XPlaneObjectSettings.BoolProperty(attr="exportChildren",
                                name="Export Children",
                                description="Export children of this to X-Plane.",
                                default = False)

    XPlaneObjectSettings.FloatProperty(attr="slungLoadWeight",
                                name="Slung Load weight",
                                description="Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter.",
                                default=0.0,
                                step=1,
                                precision=3)

#    XPlaneObjectSettings.CollectionProperty(attr="customAttributes",
#                                      name="Custom X-Plane header attributes",
#                                      description="User defined header attributes for the X-Plane file.",
#                                      type=XPlaneCustomAttributeWrapper)

    XPlaneObjectSettings.StringProperty(attr="dataref",
                                        name="X-Plane Dataref",
                                        description="X-Plane Dataref",
                                        default="")

    XPlaneObjectSettings.BoolProperty(attr="depth",
                                      name="Use depth culling",
                                      description="If unchecked the renderer will perform no depth check on this object.",
                                      default=True)
    

    # Lamp settings
    XPlaneLampSettings.EnumProperty(attr="lightType",
                                name="Light type",
                                description="Defines the type of the light in X-Plane.",
                                default = "default",
                                items=[("default","default","default"),
                                        ("flashing","flashing","flashing"),
                                        ("pulsing","pulsing","pulsing"),
                                        ("strobe","strobe","strobe"),
                                        ("traffic","traffic","traffic")])

    
    # Material settings
    XPlaneMaterialSettings.EnumProperty(attr='surfaceType',
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

    XPlaneMaterialSettings.BoolProperty(attr="blend",
                                        name="Use Alpha cutoff",
                                        description="If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio.",
                                        default=False)

    XPlaneMaterialSettings.FloatProperty(attr="blendRatio",
                                        name="Alpha cutoff ratio",
                                        description="Alpha levels in the texture below this level are rendered as fully transparent and alpha levels above this level are fully opaque.",
                                        default=0.5,
                                        step=0.1,
                                        precision=2,
                                        max=1.0,
                                        min=0.0)


def removeXPlaneRNA():
    #bpy.types.unregister(XPlaneCustomAttribute)
    #bpy.ops.unregister(OBJECT_OP_addXPlaneHeaderAttribute)
    bpy.types.Object.RemoveProperty("xplane")
    bpy.types.Material.RemoveProperty("xplane")
    bpy.types.Lamp.RemoveProperty("xplane")