import bpy

def findFCurveByPath(fcurves,path):
    i = 0
    fcurve = None
    
    # find fcurve
    while i<len(fcurves):
        if fcurves[i].data_path == path:
            fcurve = fcurves[i]
            i = len(fcurves)
        i+=1
    return fcurve

def getDatarefValuePath(index):
    return '["xplane"]["datarefs"]['+str(index)+']["value"]'

class XPlaneSceneSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLayerSettings(bpy.types.IDPropertyGroup):
    pass

class XPlaneLayer(bpy.types.IDPropertyGroup):
    pass

class XPlaneObjectSettings(bpy.types.IDPropertyGroup):
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

class SCENE_OT_add_xplane_layers(bpy.types.Operator):
    bl_label = 'Add X-Plane layers'
    bl_idname = 'scene.add_xplane_layers'
    bl_label = 'Add X-Plane layers'
    bl_description = 'Add a X-Plane export layers'

    def execute(self,context):
        scene = context.scene
        while len(scene.xplane.layers)<len(scene.layers):
            scene.xplane.layers.add()

        # re-add hidden data that user cannot change
        for i in range(0,len(scene.xplane.layers)):
            scene.xplane.layers[i].index = i
        return {'FINISHED'}

class SCENE_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'scene.add_xplane_layer_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        scene = context.scene
        scene.xplane.layers[self.index].customAttributes.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'scene.remove_xplane_layer_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntVectorProperty(size=2)

    def execute(self,context):
        scene = context.scene
        scene.xplane.layers[self.index[0]].customAttributes.remove(self.index[1])
        return {'FINISHED'}

class OBJECT_OT_add_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_object_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_object_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

class OBJECT_OT_add_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_material_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.active_material
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_material_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object.active_material
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

class OBJECT_OT_add_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_lamp_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.data
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_lamp_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object.data
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

class OBJECT_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'object.add_xplane_dataref'
    bl_label = 'Add Dataref'
    bl_description = 'Add a X-Plane Dataref'

    def execute(self,context):
        obj = context.object
        obj.xplane.datarefs.add()
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = 'Remove Dataref'
    bl_idname = 'object.remove_xplane_dataref'
    bl_label = 'Remove Dataref'
    bl_description = 'Remove the X-Plane Dataref'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        obj.xplane.datarefs.remove(self.index)

        path = getDatarefValuePath(self.index)

        # remove FCurves too
        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve:              
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {'FINISHED'}

class OBJECT_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Add Dataref keyframe'
    bl_idname = 'object.add_xplane_dataref_keyframe'
    bl_label = 'Add Dataref keyframe'
    bl_description = 'Add a X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        value = obj.xplane.datarefs[self.index].value
        #obj.xplane.datarefs[self.index].keyframe_insert(data_path="value",group="XPlane Datarefs")
        #obj.xplane.datarefs[self.index].value.keyframe_insert(group="XPlane Datarefs")
        
        #current workaround for setting keyframes to nested custom properties is adding an FCurve manually and assign its data_path and then set a keyframe
        if (obj.animation_data == None):
            obj.animation_data_create()
        if (obj.animation_data.action == None):
            obj.animation_data.action = bpy.data.actions.new(name=obj.name+"Action")

        # add keyframe to fcurve
        fcurve = None

        if len(obj.animation_data.action.fcurves) == 0:
            fcurve = obj.animation_data.action.fcurves.new(data_path=path,action_group="XPlane Datarefs")
            #fcurve.extrapolation = "LINEAR" # assign linear extrapolation as XPlane only uses these
        else:
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve == None:
                fcurve = obj.animation_data.action.fcurves.new(data_path=path,action_group="XPlane Datarefs")

        if fcurve:
            keyframe = fcurve.keyframe_points.add(frame=bpy.context.scene.frame_current,value=value)
            keyframe.interpolation = 'LINEAR' # assign linear interpolation as XPlane only uses these
        
        return {'FINISHED'}

class OBJECT_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'object.remove_xplane_dataref_keyframe'
    bl_label = 'Remove Dataref keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        fcurve = None

        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)

        if fcurve:
            # find keyframe
            keyframe = None
            if len(fcurve.keyframe_points)>0:
                i = 0
                while i<len(fcurve.keyframe_points):
                    if fcurve.keyframe_points[i].co[0] == bpy.context.scene.frame_current:
                        keyframe = fcurve.keyframe_points[i]
                        i = len(fcurve.keyframe_points)
                    i+=1

            if keyframe:
                fcurve.keyframe_points.remove(keyframe=keyframe)
            
        return {'FINISHED'}

def addXPlaneRNA():
    bpy.types.Scene.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneSceneSettings, name="XPlane", description="XPlane Export Settings")
    bpy.types.Object.xplane = bpy.props.PointerProperty(attr="xplane", type=XPlaneObjectSettings, name="XPlane", description="XPlane Export Settings")
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

    # create x-plane layers
    bpy.ops.scene.add_xplane_layers()


def removeXPlaneRNA():
    del bpy.types.Object.xplane
    del bpy.types.Material.xplane
    del bpy.types.Lamp.xplane