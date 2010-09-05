import bpy

class XPlaneSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneCustomAttribute(bpy.types.IDPropertyGroup):
    pass

def addXPlaneRNA():
    bpy.types.Object.PointerProperty(attr="xplane", type=XPlaneSettings, name="XPlane", description="XPlane Export Settings")
    #bpy.types.register(XPlaneCustomAttribute)

    XPlaneCustomAttribute.StringProperty(attr="customAttribute",
                                        name="Custom X-Plane Attribute",
                                        description="User defined attributes for the X-Plane file.",
                                        default="")

    XPlaneSettings.BoolProperty( attr="exportChildren",
                                name="Export Children",
                                description="Export children of this to X-Plane.",
                                default = False)

    XPlaneSettings.EnumProperty( attr="lightType",
                                name="Light type",
                                description="Defines the type of the light in X-Plane.",
                                default = "default",
                                items=[("default","default","default"),
                                        ("flashing","flashing","flashing"),
                                        ("pulsing","pulsing","pulsing"),
                                        ("strobe","strobe","strobe"),
                                        ("traffic","traffic","traffic")])

    XPlaneSettings.FloatProperty( attr="slungLoadWeight",
                                name="Slung Load weight",
                                description="Weight of the object in pounds, for use in the X-Plane physics engine if the object is being carried by a plane or helicopter.",
                                default=0.0,
                                step=1,
                                precision=3)


    XPlaneSettings.CollectionProperty( attr="customHeaderAttributes",
                                        name="Custom X-Plane header attributes",
                                        description="User defined header attributes for the X-Plane file.",
                                        type=XPlaneCustomAttribute)
                                


def removeXPlaneRNA():
    #bpy.types.unregister(XPlaneCustomAttribute)
    bpy.types.Object.RemoveProperty("xplane")