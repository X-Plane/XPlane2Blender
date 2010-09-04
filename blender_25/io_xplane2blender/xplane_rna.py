import bpy

class XPlaneSettings(bpy.types.IDPropertyGroup):
    pass

def addXPlaneRNA():
    bpy.types.Object.PointerProperty(attr="xplane", type=XPlaneSettings, name="XPlane", description="XPlane Export Settings")

    XPlaneSettings.BoolProperty( attr="exportChildren",
                    name="Export Children",
                    description="Export children of this to XPlane",
                    default = False)


def removeXPlaneRNA():
    bpy.types.Object.RemoveProperty("xplane")