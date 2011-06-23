# File: xplane_props.py
# Defines X-Plane Properties attached to regular Blender data types.

import bpy
from io_xplane2blender.xplane_config import *

# Class: XPlaneCustomAttribute
# A custom attribute.
#
# Properties:
#   string name - Name of the attribute
#   string value - Value of the attribute
#   string reset - Reseter of the attribute
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

    weight = bpy.props.IntProperty(name="Weight",
                                    description="The more weight an attribute has the later it gets written in the OBJ.",
                                    default=0,
                                    min=0)

# Class: XPlaneDataref
# A X-Plane Dataref
#
# Properties:
#   string path - Dataref path
#   float value - Dataref value (can be keyframed)
#   int loop - Loop amount of dataref animation.
class XPlaneDataref(bpy.types.PropertyGroup):
    path = bpy.props.StringProperty(attr="path",
                                    name="Path",
                                    description="Dataref Path",
                                    default="")

    value = bpy.props.FloatProperty(attr="value",
                                    name="Value",
                                    description="Value",
                                    default=0.0,
                                    precision=6)

    loop = bpy.props.FloatProperty(attr="loop",
                                name="Loop Amount",
                                description="Loop amount of animation, usefull for ever increasing Datarefs. A value of 0 will ignore this setting.",
                                min=0.0,
                                precision=3)

    anim_type = bpy.props.EnumProperty(attr="anim_type",
                                        name="Animation Type",
                                        description="Type of animation this Dataref will use.",
                                        default="transform",
                                        items=[("transform","LocRot","Location/Rotation"),("show","Show","Show"),("hide","Hide","Hide")])

    show_hide_v1 = bpy.props.FloatProperty(attr="show_hide_v1",
                                            name="Value 1",
                                            description="Show/Hide value 1",
                                            default=0.0)

    show_hide_v2 = bpy.props.FloatProperty(attr="show_hide_v2",
                                            name="Value 2",
                                            description="Show/Hide value 2",
                                            default=0.0)

# Class: XPlaneDatarefSearch
# Not used right now. Might be used to search for dataref paths.
#class XPlaneDatarefSearch(bpy.types.PropertyGroup):
#    path = bpy.props.StringProperty(attr="path",
#                                    name="Dataref path",
#                                    description="XPlane Dataref path",
#                                    default = "")

# Class: XPlaneManipulator
# A X-Plane manipulator settings
#
# Properties:
#   bool enabled - True if object is a manipulator
#   enum type - Manipulator types as defined in OBJ specs.
#   string tooltip - Manipulator Tooltip
#   enum cursor - Manipulator cursors as defined in OBJ specs.
#   int dx - X-Drag axis length
#   int dy - Y-Drag axis length
#   int dz - Z-Drag axis length
#   float v1 - Value 1
#   float v2 - Value 2
#   float v1_min - Value 1 min.
#   float v1_max - Value 1 max.
#   float v2_min - Value 2 min.
#   float v2_max - Value 2 max.
#   float v_down - Value on mouse down
#   float v_up - Value on mouse up
#   float v_hold - Value on mouse hold
#   float v_on - On value
#   float v_off - Off value
#   string command - Command
#   string positive_command - Positive command
#   string negative_command - Negative command
#   string dataref1 - Dataref 1
#   string dataref2 - Dataref 2
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

    dx = bpy.props.FloatProperty(attr="dx",
                            name="dx",
                            description="X-Drag axis length",
                            default=0.0)

    dy = bpy.props.FloatProperty(attr="dy",
                            name="dy",
                            description="Y-Drag axis length",
                            default=0.0)

    dz = bpy.props.FloatProperty(attr="dz",
                            name="dz",
                            description="Z-Drag axis length",
                            default=0.0)

    v1 = bpy.props.FloatProperty(attr="v1",
                            name="v1",
                            description="Value 1",
                            default=0.0)

    v2 = bpy.props.FloatProperty(attr="v2",
                            name="v2",
                            description="Value 2",
                            default=0.0)

    v1_min = bpy.props.FloatProperty(attr="v1_min",
                            name="v1 min",
                            description="Value 1 min.",
                            default=0.0)

    v1_max = bpy.props.FloatProperty(attr="v1_max",
                            name="v1 min",
                            description="Value 1 max.",
                            default=0.0)

    v2_min = bpy.props.FloatProperty(attr="v2_min",
                            name="v2 min",
                            description="Value 2 min.",
                            default=0.0)

    v2_max = bpy.props.FloatProperty(attr="v2_max",
                            name="v2 min",
                            description="Value 2 max.",
                            default=0.0)

    v_down = bpy.props.FloatProperty(attr="v_down",
                                name="v down",
                                description="Value on mouse down",
                                default=0.0)

    v_up = bpy.props.FloatProperty(attr="v_up",
                                name="v up",
                                description="Value on mouse up",
                                default=0.0)

    v_hold = bpy.props.FloatProperty(attr="v_hold",
                                name="v hold",
                                description="Value on mouse hold",
                                default=0.0)

    v_on = bpy.props.FloatProperty(attr="v_on",
                                name="v on",
                                description="On value",
                                default=0.0)

    v_off = bpy.props.FloatProperty(attr="v_off",
                                name="v off",
                                description="Off value",
                                default=0.0)

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

# Class: XPlaneCockpitRegion
# Defines settings for a cockpit region.
#
# Properties:
#   int top - top position of the region in px
#   int left - left position of the region in px
#   int width - width of the region in powers of 2
#   int height - height of the region in powers of 2
class XPlaneCockpitRegion(bpy.types.PropertyGroup):
    expanded = bpy.props.BoolProperty(name="Expanded",
                                  description="Toggle this cockpit region settings visibility.",
                                  default=False)

    top = bpy.props.IntProperty(attr="top",
                                name="Top",
                                description="Top",
                                default=0,
                                min=0,
                                max=2048)

    left = bpy.props.IntProperty(attr="left",
                                name="Left",
                                description="Left",
                                default=0,
                                min=0,
                                max=2048)

    width = bpy.props.IntProperty(attr="width",
                                name="Width",
                                description="Width in powers of 2.",
                                default=1,
                                min=1,
                                max=11)

    height = bpy.props.IntProperty(attr="height",
                                name="Height",
                                description="Height in powers of 2.",
                                default=1,
                                min=1,
                                max=11)

# Class: XPlaneLOD
# Defines settings for a level of detail.
#
# Properties:
#   int near - near distance
#   int far - far distance
class XPlaneLOD(bpy.types.PropertyGroup):
    expanded = bpy.props.BoolProperty(name="Expanded",
                                  description="Toggle this LOD settings visibility.",
                                  default=False)

    near = bpy.props.IntProperty(name="Near",
                                description="Near distance (inclusive) in meters",
                                default=0,
                                min=0)

    far = bpy.props.IntProperty(name="Far",
                                description="Far distance (exclusive) in meters",
                                default=0,
                                min=0)

# Class: XPlaneLayer
# Defines settings for a OBJ file. Is "parented" to a Blender layer.
#
# Properties:
#   int index - index of this layer.
#   bool expanded - True if the settings of this layer are expanded in the UI.
#   string name - Name of the OBJ file to export from this layer.
#   bool cockpit - True if this layer serves as a cockpit OBJ.
#   float slungLoadWeight - Slung Load weight
#   string texture - Texture file to use for this OBJ.
#   string texture_lit - Night Texture to use for this OBJ.
#   string texture_normal - Normal/Specular Texture to use for this OBJ.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane header attributes.
class XPlaneLayer(bpy.types.PropertyGroup):
    index = bpy.props.IntProperty(attr="index",
                                    name="Index",
                                    description="The blender layer index.",
                                    default=-1)

    export = bpy.props.BoolProperty(attr="export",
                                    name="Export",
                                    description="If checked, this layer will be exported if visible.",
                                    default=True)

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
                                    subtype="FILE_PATH",
                                    name="Texture",
                                    description="Texture to use for objects on this layer.",
                                    default="")

    texture_lit = bpy.props.StringProperty(attr="texture_lit",
                                    subtype="FILE_PATH",
                                    name="Night Texture",
                                    description="Night Texture to use for objects on this layer.",
                                    default="")

    texture_normal = bpy.props.StringProperty(attr="texture_normal",
                                    subtype="FILE_PATH",
                                    name="Normal/Specular Texture",
                                    description="Normal/Specular Texture to use for objects on this layer.",
                                    default="")

    cockpit_regions = bpy.props.EnumProperty(attr="cockpit_regions",
                                    name="Cockpit regions",
                                    description="Number of Cockpit regions to use.",
                                    default="0",
                                    items=[("0","none","none"),("1","1","1"),("2","2","2"),("3","3","3"),("4","4","4")])

    cockpit_region = bpy.props.CollectionProperty(name="cockpit_region",
                                    type=XPlaneCockpitRegion,
                                    description="Cockpit Region")

    lods = bpy.props.EnumProperty(name="Levels of detail",
                                    description="Levels of detail",
                                    default="0",
                                    items=[("0","none","none"),("2","2","2"),("3","3","3")])

    lod = bpy.props.CollectionProperty(name="LOD",
                                    type=XPlaneLOD,
                                    description="Level of detail")

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane header attributes",
                                      description="User defined header attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

# Class: XPlaneSceneSettings
# Settings for Blender scenes.
#
# Properties:
#   layers - Collection of <XPlaneLayers>. Export settings for the Blender layers.
class XPlaneSceneSettings(bpy.types.PropertyGroup):
    debug = bpy.props.BoolProperty(attr="debug",
                                    name="Debug",
                                    description="If checked debug information will be printed to the console and into OBJ files.",
                                    default=False)

    profile = bpy.props.BoolProperty(attr="profile",
                                    name="Profiling",
                                    description="If checked profiling information will be printed together with the debug information.",
                                    default=False)

    log = bpy.props.BoolProperty(attr="log",
                                    name="Log",
                                    description="If checked the debug information will be written to a log file.",
                                    default=False)


    layers = bpy.props.CollectionProperty(attr="layers",
                                            name="Layers",
                                            description="Export settings for the Blender layers",
                                            type=XPlaneLayer)

    optimize = bpy.props.BoolProperty(attr="optimize",
                                        name="Optimize",
                                        description="If checked file size will be optimized. However this can increase export time dramatically.",
                                        default=False)

# Class: XPlaneObjectSettings
# Settings for Blender objects.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
#   bool depth - True if object will use depth culling.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
#   bool panel - True if object is part of the cockpit panel.
#   XPlaneManipulator manip - Manipulator settings.
#   bool lightLevel - True if object overrides default light levels.
#   float lightLevel_v1 - Light Level Value 1
#   float lightLevel_v2 - Light Level Value 2
#   string lightLevel_dataref - Light Level Dataref
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

    customAnimAttributes = bpy.props.CollectionProperty(attr="customAnimAttributes",
                                      name="Custom X-Plane animation attributes",
                                      description="User defined attributes for animation of the Object.",
                                      type=XPlaneCustomAttribute)

    manip = bpy.props.PointerProperty(attr="manip",
                                        name="Manipulator",
                                        description="XPlane Manipulator Settings.",
                                        type=XPlaneManipulator)

    lod = bpy.props.BoolVectorProperty(name="Levels of detail",
                                        description="Define in wich LODs this object will be used. If none is checked it will be used in all.",
                                        default=(False,False,False),
                                        size=3)

    override_weight = bpy.props.BoolProperty(name="Override weight",
                                        description="If checked you can override the internal weight of the object. Heavier objects will be written later in OBJ.",
                                        default=False)

    weight = bpy.props.IntProperty(name="Weight",
                                    description="Usual weights are: Meshes 0-8999, Lines 9000 - 9999, Lamps >=10000.",
                                    default=0,
                                    min=0)

# Class: XPlaneBoneSettings
# Settings for Blender bones.
#
# Properties:
#   datarefs - Collection of <XPlaneDatarefs>. X-Plane Datarefs
class XPlaneBoneSettings(bpy.types.PropertyGroup):
    datarefs = bpy.props.CollectionProperty(attr="datarefs",
                                        name="X-Plane Datarefs",
                                        description="X-Plane Datarefs",
                                        type=XPlaneDataref)

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane attributes",
                                      description="User defined attributes for the Object.",
                                      type=XPlaneCustomAttribute)

    customAnimAttributes = bpy.props.CollectionProperty(attr="customAnimAttributes",
                                      name="Custom X-Plane animation attributes",
                                      description="User defined attributes for animation of the Object.",
                                      type=XPlaneCustomAttribute)

# Class: XPlaneMaterialSettings
# Settings for Blender materials.
#
# Properties:
#   enum surfaceType - Surface type as defined in OBJ specs.
#   bool blend - True if the material uses alpha cutoff.
#   float blendRatio - Alpha cutoff ratio.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
class XPlaneMaterialSettings(bpy.types.PropertyGroup):
    draw = bpy.props.BoolProperty(attr="draw",
                                    name="Draw enabled",
                                    description="if turned off, objects with this material won't be drawn.",
                                    default=True)

    overrideSpecularity = bpy.props.BoolProperty(attr="overrideSpecularity",
                                                name="Override specularity",
                                                description="If checked you will override Blenders specularity with the 'Shiny Ratio'.",
                                                default=False)

    shinyRatio = bpy.props.FloatProperty(attr='shinyRatio',
                                            name='Shiny ratio',
                                            description='Controls the amount of specularity of the material in X-Plane.',
                                            default=0.0,
                                            min=0.0)

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

    deck = bpy.props.BoolProperty(name="Deck",
                                    description="Allows the user to fly under the surface.",
                                    default=False)

    solid_camera = bpy.props.BoolProperty(name="Camera collision",
                                        description="Will impede the movement of the 3-d camera. Works only in Cockpits.",
                                        default=False)

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

    panel = bpy.props.BoolProperty(attr="panel",
                                        name="Part of cockpit panel",
                                        description="If checked this object will use the panel texture and will be clickable.",
                                        default=False)

    cockpit_region = bpy.props.EnumProperty(attr="cockpit_region",
                                        name="Cockpit region",
                                        description="Cockpit region to use.",
                                        default="0",
                                        items=[("0","none","none"),("1","1","1"),("2","2","2"),("3","3","3"),("4","4","4")])

    lightLevel = bpy.props.BoolProperty(attr="lightLevel",
                                        name="Light Level",
                                        description="If checked values will change the brightness of the _LIT texture for the object. This overrides the sim's decision about object lighting.",
                                        default=False)

    lightLevel_v1 = bpy.props.FloatProperty(attr="lightLevel_v1",
                                        name="Light Level v1",
                                        description="Value 1",
                                        default=0.0)

    lightLevel_v2 = bpy.props.FloatProperty(attr="lightLevel_v2",
                                        name="Light Level v2",
                                        description="Value 2",
                                        default=1.0)

    lightLevel_dataref = bpy.props.StringProperty(attr="lightLevel_dataref",
                                        name="Light Level Dataref",
                                        description="The dataref is interpreted as a value between v1 and v2. Values outside v1 and v2 are clamped.",
                                        default="")

    poly_os = bpy.props.IntProperty(name="Polygon offset",
                                    description="Sets the polygon offset state. Leave at 0 for default behaviour.",
                                    default=0,
                                    step=1,
                                    min=0)

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane material attributes",
                                      description="User defined material attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

# Class: XPlaneLampSettings
# Settings for Blender lamps.
#
# Properties:
#   enum type - Light type as defined in OBJ specs.
#   string name - Light name, if "type" is 'named'.
#   string params - Light params, if "type" is 'param'.
#   float size - Light size, if "type" is 'custom'.
#   string dataref - Dataref driving the light, if "type" is 'custom'.
#   customAttributes - Collection of <XPlaneCustomAttributes>. Custom X-Plane attributes
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

    uv = bpy.props.FloatVectorProperty(name="Texture coordinates",
                                        description="The texture coordinates in the following order: left,top,right,bottom (fractions from 0 to 1).",
                                        default=(0.0,0.0,1.0,1.0),
                                        min=0.0,
                                        max=1.0,
                                        precision=3,
                                        size=4)

    customAttributes = bpy.props.CollectionProperty(attr="customAttributes",
                                      name="Custom X-Plane light attributes",
                                      description="User defined light attributes for the X-Plane file.",
                                      type=XPlaneCustomAttribute)

# Function: addXPlaneRNA
# Registers all properties.
def addXPlaneRNA():
    # basic classes
    bpy.utils.register_class(XPlaneCustomAttribute)
    bpy.utils.register_class(XPlaneDataref)
    #bpy.utils.register_class(XPlaneDatarefSearch)
    bpy.utils.register_class(XPlaneManipulator)
    bpy.utils.register_class(XPlaneCockpitRegion)
    bpy.utils.register_class(XPlaneLOD)

    # complex classes, depending on basic classes
    bpy.utils.register_class(XPlaneLayer)
    bpy.utils.register_class(XPlaneObjectSettings)
    bpy.utils.register_class(XPlaneBoneSettings)
    bpy.utils.register_class(XPlaneMaterialSettings)
    bpy.utils.register_class(XPlaneLampSettings)
    bpy.utils.register_class(XPlaneSceneSettings)    

    bpy.types.Scene.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneSceneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Object.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Bone.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneBoneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Material.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneMaterialSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Lamp.xplane = bpy.props.PointerProperty(attr="xplane",type=XPlaneLampSettings, name="XPlane", description="XPlane Export Settings")
#    bpy.types.Scene.xplane_datarefs = bpy.props.CollectionProperty(attr="xplane_datarefs",
#                                                                    name="XPlane Datarefs",
#                                                                    description="XPlane Datarefs",
#                                                                    type=XPlaneDatarefSearch)
                                                                    

#    XPlaneLayerSettings.exportChildren = bpy.props.BoolProperty(attr="exportChildren",
#                                name="Export Children",
#                                description="Export children of this to X-Plane.",
#                                default = False)

    # TODO: cockpit region

    

# Function: removeXPlaneRNA
# Unregisters all properties.
def removeXPlaneRNA():
    # complex classes, depending on basic classes
    bpy.utils.unregister_class(XPlaneObjectSettings)
    bpy.utils.unregister_class(XPlaneBoneSettings)
    bpy.utils.unregister_class(XPlaneMaterialSettings)
    bpy.utils.unregister_class(XPlaneLampSettings)
    bpy.utils.unregister_class(XPlaneSceneSettings)
    bpy.utils.unregister_class(XPlaneLayer)

    # basic classes
    bpy.utils.unregister_class(XPlaneCustomAttribute)
    bpy.utils.unregister_class(XPlaneDataref)
    #bpy.utils.unregister_class(XPlaneDatarefSearch)
    bpy.utils.unregister_class(XPlaneManipulator)
    bpy.utils.unregister_class(XPlaneCockpitRegion)
    bpy.utils.unregister_class(XPlaneLOD)
    
