import bpy

class XPlaneSettings(bpy.types.IDPropertyGroup):
    pass

def addXPlaneRNA():
    bpy.types.Object.PointerProperty(attr="xplane", type=XPlaneSettings, name="XPlane", description="XPlane Export Settings")

    XPlaneSettings.BoolProperty( attr="exportChildren",
                                name="Export Children",
                                description="Export children of this to XPlane",
                                default = False)

    XPlaneSettings.EnumProperty( attr="lightType",
                                name="Light type",
                                description="Defines the type of the light in XPlane",
                                default = "default",
                                items=[("default","default","default"),
                                        ("flashing","flashing","flashing"),
                                        ("pulsing","pulsing","pulsing"),
                                        ("strobe","strobe","strobe"),
                                        ("traffic","traffic","traffic")])
                                


def removeXPlaneRNA():
    bpy.types.Object.RemoveProperty("xplane")