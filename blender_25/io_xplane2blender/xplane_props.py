import bpy
from io_xplane2blender.xplane_config import *

class XPlaneSceneSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLayerSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLayer(bpy.types.IDPropertyGroup):
    pass

class XPlaneObjectSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneBoneSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneMaterialSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLampSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneCustomAttribute(bpy.types.IDPropertyGroup):
    pass

class XPlaneDataref(bpy.types.IDPropertyGroup):
    pass

class XPlaneDatarefSearch(bpy.types.IDPropertyGroup):
    pass

def addXPlaneRNA():
    bpy.types.Scene.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneSceneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Object.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Bone.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneBoneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Scene.xplane_datarefs = bpy.props.CollectionProperty(attr="xplane_datarefs",
                                                                    name="XPlane Datarefs",
                                                                    description="XPlane Datarefs",
                                                                    type=XPlaneDatarefSearch)

    XPlaneDatarefSearch.name = bpy.props.StringProperty(attr="path",
                                                name="Dataref path",
                                                description="XPlane Dataref path",
                                                default = "")

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

    # Datarefs
    XPlaneDataref.path = bpy.props.StringProperty(attr="path",
                                        name="Path",
                                        description="Dataref Path",
                                        default="")

    XPlaneDataref.value = bpy.props.FloatProperty(attr="value",
                                        name="Value",
                                        description="Value",
                                        default=0)

    XPlaneDataref.loop = bpy.props.IntProperty(attr="loop",
                                                name="Loop Amount",
                                                description="Loop amount of animation, usefull for ever increasing Datarefs. A value of 0 will ignore this setting.",
                                                min=0)

    # Scene settings
    XPlaneSceneSettings.layers = bpy.props.CollectionProperty(attr="layers",
                                    name="Layers",
                                    description="Export settings for the Blender layers",
                                    type=XPlaneLayer)

#    XPlaneLayerSettings.exportChildren = bpy.props.BoolProperty(attr="exportChildren",
#                                name="Export Children",
#                                description="Export children of this to X-Plane.",
#                                default = False)

    XPlaneLayer.index = bpy.props.IntProperty(attr="index",
                                    name="Index",
                                    description="The blender layer index.",
                                    default=-1)

    XPlaneLayer.expanded = bpy.props.BoolProperty(attr="expanded",
                                    name="Expanded",
                                    description="Toggles the layer settings visibility.",
                                    default=False)

    XPlaneLayer.name = bpy.props.StringProperty(attr="name",
                                    name="Name",
                                    description="This name will be used as a filename hint for OBJ file(s).",
                                    default="")
                                    
    XPlaneLayer.cockpit = bpy.props.BoolProperty(attr="cockpit",
                                    name="Cockpit",
                                    description="If checked the exported object will be interpreted as a cockpit.",
                                    default=False)

    XPlaneLayer.slungLoadWeight = bpy.props.FloatProperty(attr="slungLoadWeight",
                                    name="Slung Load weight",
                                    description="Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter.",
                                    default=0.0,
                                    step=1,
                                    precision=3)

    XPlaneLayer.customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane header attributes",
                                      description="User defined header attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

    #Object settings
    XPlaneObjectSettings.datarefs = bpy.props.CollectionProperty(attr="datarefs",
                                        name="X-Plane Datarefs",
                                        description="X-Plane Datarefs",
                                        type=XPlaneDataref)

    XPlaneObjectSettings.depth = bpy.props.BoolProperty(attr="depth",
                                      name="Use depth culling",
                                      description="If unchecked the renderer will perform no depth check on this object.",
                                      default=True)

    XPlaneObjectSettings.customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane attributes",
                                      description="User defined attributes for the Object.",
                                      type=XPlaneCustomAttribute)

    #Bone settings
    XPlaneBoneSettings.datarefs = bpy.props.CollectionProperty(attr="datarefs",
                                        name="X-Plane Datarefs",
                                        description="X-Plane Datarefs",
                                        type=XPlaneDataref)

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

    XPlaneLampSettings.customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane light attributes",
                                      description="User defined light attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

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

    XPlaneMaterialSettings.customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane material attributes",
                                      description="User defined material attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)


def removeXPlaneRNA():
    del bpy.types.Object.xplane
    del bpy.types.Material.xplane
    del bpy.types.Lamp.xplane