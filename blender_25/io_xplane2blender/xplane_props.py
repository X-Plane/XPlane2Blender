import bpy
from io_xplane2blender.xplane_config import *

class XPlaneCustomAttribute(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(attr="name",
                                    name="Name",
                                    description="Name",
                                    default="")

    value = bpy.props.StringProperty(attr="value",
                                    name="Value",
                                    description="Value",
                                    default="")

    reset = bpy.props.StringProperty(attr="reset",
                                    name="Reset",
                                    description="Reset",
                                    default="")

class XPlaneDataref(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(attr="path",
                                    name="Path",
                                    description="Dataref Path",
                                    default="")

    value = bpy.props.FloatProperty(attr="value",
                                    name="Value",
                                    description="Value",
                                    default=0)

    loop = bpy.props.IntProperty(attr="loop",
                                name="Loop Amount",
                                description="Loop amount of animation, usefull for ever increasing Datarefs. A value of 0 will ignore this setting.",
                                min=0)

class XPlaneDatarefSearch(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(attr="path",
                                    name="Dataref path",
                                    description="XPlane Dataref path",
                                    default = "")

class XPlaneManipulator(bpy.types.PropertyGroup):
    enabled = bpy.props.BoolProperty(attr="enabled",
                                    name="Manipulator",
                                    description="If checked this object will be treated as a manipulator.",
                                    default=False)

    type = bpy.props.EnumProperty(attr="type",
                                name="Manipulator type",
                                description="The type of the manipulator.",
                                default='drag_xy',
                                items=[("drag_xy","drag_xy","drag_xy"),
                                ("drag_axis","drag_axis","drag_axis"),
                                ("command","command","command"),
                                ("command_axis","command_axis","command_axis"),
                                ("push","push","push"),
                                ("radio","radio","radio"),
                                ("toggle","toggle","toggle"),
                                ("delta","delta","delta"),
                                ("wrap","wrap","wrap"),
                                ("toggle","toggle","toggle"),
                                ("noop","noop","noop")])

    tooltip = bpy.props.StringProperty(attr="tooltip",
                                    name="Manipulator Tooltip",
                                    description="The tooltip will be displayed when hovering over the object.",
                                    default="")

    cursor = bpy.props.EnumProperty(attr="cursor",
                                name="Manipulator Cursor",
                                description="The mouse cursor type when hovering over the object.",
                                default="hand",
                                items=[("four_arrows","four_arrows","four_arrows"),
                                        ("hand","hand","hand"),
                                        ("button","button","button"),
                                        ("rotate_small","rotate_small","rotate_small"),
                                        ("rotate_small_left","rotate_small_left","rotate_small_left"),
                                        ("rotate_small_right","rotate_small_right","rotate_small_right"),
                                        ("rotate_medium","rotate_medium","rotate_medium"),
                                        ("rotate_medium_left","rotate_medium_left","rotate_medium_left"),
                                        ("rotate_medium_right","rotate_medium_right","rotate_medium_right"),
                                        ("rotate_large","rotate_large","rotate_large"),
                                        ("rotate_large_left","rotate_large_left","rotate_large_left"),
                                        ("rotate_large_right","rotate_large_right","rotate_large_right"),
                                        ("up_down","up_down","up_down"),
                                        ("down","down","down"),
                                        ("up","up","up"),
                                        ("left_right","left_right","left_right"),
                                        ("left","left","left"),
                                        ("right","right","right"),
                                        ("arrow","arrow","arrow")])

    dx = bpy.props.IntProperty(attr="dx",
                            name="dx",
                            description="X-Drag axis length",
                            default=0,
                            min=0)

    dy = bpy.props.IntProperty(attr="dy",
                            name="dy",
                            description="Y-Drag axis length",
                            default=0,
                            min=0)

    dz = bpy.props.IntProperty(attr="dz",
                            name="dz",
                            description="Z-Drag axis length",
                            default=0,
                            min=0)

    v1 = bpy.props.FloatProperty(attr="v1",
                            name="v1",
                            description="Value 1",
                            default=0)

    v2 = bpy.props.FloatProperty(attr="v2",
                            name="v2",
                            description="Value 2",
                            default=0)

    v1_min = bpy.props.FloatProperty(attr="v1_min",
                            name="v1 min",
                            description="Value 1 min.",
                            default=0)

    v1_max = bpy.props.FloatProperty(attr="v1_max",
                            name="v1 min",
                            description="Value 1 max.",
                            default=0)

    v2_min = bpy.props.FloatProperty(attr="v2_min",
                            name="v2 min",
                            description="Value 2 min.",
                            default=0)

    v2_max = bpy.props.FloatProperty(attr="v2_max",
                            name="v2 min",
                            description="Value 2 max.",
                            default=0)

    v_down = bpy.props.FloatProperty(attr="v_down",
                                name="v down",
                                description="Value on mouse down",
                                default=0)

    v_up = bpy.props.FloatProperty(attr="v_up",
                                name="v up",
                                description="Value on mouse up",
                                default=0)

    v_hold = bpy.props.FloatProperty(attr="v_hold",
                                name="v hold",
                                description="Value on mouse hold",
                                default=0)

    v_on = bpy.props.FloatProperty(attr="v_on",
                                name="v on",
                                description="On value",
                                default=0)

    v_off = bpy.props.FloatProperty(attr="v_off",
                                name="v off",
                                description="Off value",
                                default=0)

    command = bpy.props.StringProperty(attr="command",
                                name="Command",
                                description="Command",
                                default="")

    positive_command = bpy.props.StringProperty(attr="positive_command",
                                name="Positive command",
                                description="Positive command",
                                default="")

    negative_command = bpy.props.StringProperty(attr="negative_command",
                                name="Negative command",
                                description="Negative command",
                                default="")

    dataref1 = bpy.props.StringProperty(attr="dataref1",
                                name="Dataref 1",
                                description="Dataref 1",
                                default="")

    dataref2 = bpy.props.StringProperty(attr="dataref2",
                                name="Dataref 2",
                                description="Dataref 2",
                                default="")

class XPlaneLayerSettings(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(attr="index",
                                    name="Index",
                                    description="The blender layer index.",
                                    default=-1)

    expanded = bpy.props.BoolProperty(attr="expanded",
                                    name="Expanded",
                                    description="Toggles the layer settings visibility.",
                                    default=False)

    name = bpy.props.StringProperty(attr="name",
                                    name="Name",
                                    description="This name will be used as a filename hint for OBJ file(s).",
                                    default="")

    cockpit = bpy.props.BoolProperty(attr="cockpit",
                                    name="Cockpit",
                                    description="If checked the exported object will be interpreted as a cockpit.",
                                    default=False)

    slungLoadWeight = bpy.props.FloatProperty(attr="slungLoadWeight",
                                    name="Slung Load weight",
                                    description="Weight of the object in pounds, for use in the physics engine if the object is being carried by a plane or helicopter.",
                                    default=0.0,
                                    step=1,
                                    precision=3)

    texture = bpy.props.StringProperty(attr="texture",
                                    name="Texture",
                                    description="Texture to use for objects on this layer.",
                                    default="")

    texture_lit = bpy.props.StringProperty(attr="texture_lit",
                                    name="Night Texture",
                                    description="Night Texture to use for objects on this layer.",
                                    default="")

    texture_normal = bpy.props.StringProperty(attr="texture_normal",
                                    name="Normal/Specular Texture",
                                    description="Normal/Specular Texture to use for objects on this layer.",
                                    default="")
                                    
    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane header attributes",
                                      description="User defined header attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

class XPlaneLayer(bpy.types.PropertyGroup):
    pass

class XPlaneSceneSettings(bpy.types.PropertyGroup):
    layers = bpy.props.CollectionProperty(attr="layers",
                                            name="Layers",
                                            description="Export settings for the Blender layers",
                                            type=XPlaneLayer)

class XPlaneObjectSettings(bpy.types.PropertyGroup):
    datarefs = bpy.props.CollectionProperty(attr="datarefs",
                                        name="X-Plane Datarefs",
                                        description="X-Plane Datarefs",
                                        type=XPlaneDataref)

    depth = bpy.props.BoolProperty(attr="depth",
                                      name="Use depth culling",
                                      description="If unchecked the renderer will perform no depth check on this object.",
                                      default=True)

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane attributes",
                                      description="User defined attributes for the Object.",
                                      type=XPlaneCustomAttribute)

    panel = bpy.props.BoolProperty(attr="panel",
                                        name="Part of cockpit panel",
                                        description="If checked this object will use the panel texture and will be clickable.",
                                        default=False)

    manip = bpy.props.PointerProperty(attr="manip",
                                        name="Manipulator",
                                        description="XPlane Manipulator Settings.",
                                        type=XPlaneManipulator)

    lightLevel = bpy.props.BoolProperty(attr="lightLevel",
                                        name="Light Level",
                                        description="If checked values will change the brightness of the _LIT texture for the object. This overrides the sim's decision about object lighting.",
                                        default=False)

    lightLevel_v1 = bpy.props.FloatProperty(attr="lightLevel_v1",
                                        name="Light Level v1",
                                        description="Value 1",
                                        default=0.0,
                                        min=0.0,
                                        max=1.0)

    lightLevel_v2 = bpy.props.FloatProperty(attr="lightLevel_v2",
                                        name="Light Level v2",
                                        description="Value 2",
                                        default=1.0,
                                        min=0.0,
                                        max=1.0)

    lightLevel_dataref = bpy.props.StringProperty(attr="lightLevel_dataref",
                                        name="Light Level Dataref",
                                        description="The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped.",
                                        default="")

class XPlaneBoneSettings(bpy.types.PropertyGroup):
    datarefs = bpy.props.CollectionProperty(attr="datarefs",
                                        name="X-Plane Datarefs",
                                        description="X-Plane Datarefs",
                                        type=XPlaneDataref)

class XPlaneMaterialSettings(bpy.types.PropertyGroup):
    surfaceType = bpy.props.EnumProperty(attr='surfaceType',
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

    blend = bpy.props.BoolProperty(attr="blend",
                                        name="Use Alpha cutoff",
                                        description="If turned on the textures alpha channel will be used to cutoff areas above the Alpha cutoff ratio.",
                                        default=False)

    blendRatio = bpy.props.FloatProperty(attr="blendRatio",
                                        name="Alpha cutoff ratio",
                                        description="Alpha levels in the texture below this level are rendered as fully transparent and alpha levels above this level are fully opaque.",
                                        default=0.5,
                                        step=0.1,
                                        precision=2,
                                        max=1.0,
                                        min=0.0)

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane material attributes",
                                      description="User defined material attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

class XPlaneLampSettings(bpy.types.PropertyGroup):
    type = bpy.props.EnumProperty(attr="type",
                                name="Type",
                                description="Defines the type of the light in X-Plane.",
                                default = "default",
                                items=[("default","default","default"),
                                        ("flashing","flashing","flashing"),
                                        ("pulsing","pulsing","pulsing"),
                                        ("strobe","strobe","strobe"),
                                        ("traffic","traffic","traffic"),
                                        ("named","named","named"),
                                        ("custom","custom","custom"),
                                        ("param","param","param")])

    name = bpy.props.StringProperty(attr="name",
                                    name='Name',
                                    description="Named lights allow a light to be created based on pre-existing types.",
                                    default="")

    params = bpy.props.StringProperty(attr="params",
                                    name='Parameters',
                                    description="The additional parameters vary in number and definition based on the particular parameterized light selected.",
                                    default="")

    size = bpy.props.FloatProperty(attr="size",
                                    name='Size',
                                    description="The size of the light - this is not in a particular unit (like meters), but larger numbers produce bigger brighter lights.",
                                    default=1.0,
                                    min=0.0)

    dataref = bpy.props.StringProperty(attr="dataref",
                                    name='Dataref',
                                    description="A X-Plane Dataref.",
                                    default="")

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane light attributes",
                                      description="User defined light attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

def addXPlaneRNA():
    # basic classes
    bpy.utils.register_class(XPlaneCustomAttribute)
    bpy.utils.register_class(XPlaneDataref)
    bpy.utils.register_class(XPlaneDatarefSearch)
    bpy.utils.register_class(XPlaneManipulator)
    bpy.utils.register_class(XPlaneLayer)

    # complex classes, depending on basic classes
    bpy.utils.register_class(XPlaneObjectSettings)
    bpy.utils.register_class(XPlaneBoneSettings)
    bpy.utils.register_class(XPlaneMaterialSettings)
    bpy.utils.register_class(XPlaneLampSettings)
    bpy.utils.register_class(XPlaneLayerSettings)
    bpy.utils.register_class(XPlaneSceneSettings)    

    bpy.types.Scene.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneSceneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Object.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.PoseBone.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneBoneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Scene.xplane_datarefs = bpy.props.CollectionProperty(attr="xplane_datarefs",
                                                                    name="XPlane Datarefs",
                                                                    description="XPlane Datarefs",
                                                                    type=XPlaneDatarefSearch)
                                                                    

#    XPlaneLayerSettings.exportChildren = bpy.props.BoolProperty(attr="exportChildren",
#                                name="Export Children",
#                                description="Export children of this to X-Plane.",
#                                default = False)

    # TODO: cockpit region

    


def removeXPlaneRNA():
    # complex classes, depending on basic classes
    bpy.utils.unregister_class(XPlaneObjectSettings)
    bpy.utils.unregister_class(XPlaneBoneSettings)
    bpy.utils.unregister_class(XPlaneMaterialSettings)
    bpy.utils.unregister_class(XPlaneLampSettings)
    bpy.utils.unregister_class(XPlaneLayerSettings)
    bpy.utils.unregister_class(XPlaneSceneSettings)

    # basic classes
    bpy.utils.unregister_class(XPlaneCustomAttribute)
    bpy.utils.unregister_class(XPlaneDataref)
    bpy.utils.unregister_class(XPlaneDatarefSearch)
    bpy.utils.unregister_class(XPlaneManipulator)
    bpy.utils.unregister_class(XPlaneLayer)