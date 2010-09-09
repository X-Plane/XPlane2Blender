import bpy

class XPlaneObjectSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneMaterialSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLampSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneCustomAttribute(bpy.types.IDPropertyGroup):
    pass

def addXPlaneRNA():
    print("adding xplane rna")
    bpy.types.Object.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")
    #bpy.types.register(XPlaneCustomAttribute)

    # custom Attribute
    XPlaneCustomAttribute.StringProperty(attr="customAttribute",
                                        name="Custom X-Plane Attribute",
                                        description="User defined attributes for the X-Plane file.",
                                        default="")

    # Empty settings
    XPlaneObjectSettings.BoolProperty(attr="exportChildren",
                                name="Export Children",
                                description="Export children of this to X-Plane.",
                                default = False)

    XPlaneObjectSettings.FloatProperty(attr="slungLoadWeight",
                                name="Slung Load weight",
                                description="Weight of the object in pounds, for use in the X-Plane physics engine if the object is being carried by a plane or helicopter.",
                                default=0.0,
                                step=1,
                                precision=3)

    XPlaneObjectSettings.CollectionProperty(attr="customHeaderAttributes",
                                      name="Custom X-Plane header attributes",
                                      description="User defined header attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

    XPlaneObjectSettings.StringProperty(attr="dataref",
                                        name="X-Plane Dataref",
                                        description="X-Plane Dataref",
                                        default="")
    

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


def removeXPlaneRNA():
    print("removing xplane rna")
    #bpy.types.unregister(XPlaneCustomAttribute)
    bpy.types.Object.RemoveProperty("xplane")
    bpy.types.Material.RemoveProperty("xplane")
    bpy.types.Lamp.RemoveProperty("xplane")