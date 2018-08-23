import bpy
import io_xplane2blender
from typing import List,Tuple
from ..xplane_config import getDebug
from ..xplane_helpers import floatToStr, logger
from ..xplane_constants import *
from .xplane_attributes import XPlaneAttributes
from .xplane_attribute import XPlaneAttribute
#from .xplane_file import getXPlaneVersion

# Class: XPlaneMaterial
# A Material
class XPlaneMaterial():
    # Property: object
    # XPlaneObject - A <XPlaneObject>

    # Property: texture
    # string - Path to the texture in use for this material, or None if no texture is present.
    # This property is no longer important as textures are defined by layer.

    # Property: uv_name
    # string - Name of the uv layer to be used for texture UVs.

    # Property: name
    # string - Name of the Blender material.

    # Property: attributes
    # dict - Material attributes that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines the <attributes> by reading the original Blender material from the <object>.
    # Also adds custom attributes to <attributes>.
    #
    # Parameters:
    #   xplaneObject - A <XPlaneObject>
    def __init__(self, xplaneObject):
        from os import path

        self.xplaneObject = xplaneObject
        self.blenderObject = self.xplaneObject.blenderObject
        self.blenderMaterial = None
        # The options from mat.xplane
        self.options = None
        self.texture = None
        self.textureLit = None
        self.textureNormal = None
        self.textureSpecular = None
        self.uv_name = None
        self.name = None

        # Material
        self.attributes = XPlaneAttributes()

        # useless according to Ben Supnik
        # self.attributes.add(XPlaneAttribute("ATTR_specular_rgb"))

        self.attributes.add(XPlaneAttribute("ATTR_shiny_rat"))
        self.attributes.add(XPlaneAttribute("ATTR_hard"))
        self.attributes.add(XPlaneAttribute("ATTR_hard_deck"))
        self.attributes.add(XPlaneAttribute("ATTR_no_hard"))

        self.attributes.add(XPlaneAttribute("ATTR_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_shadow_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_no_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_enable"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_disable"))
        self.attributes.add(XPlaneAttribute("ATTR_solid_camera"))
        self.attributes.add(XPlaneAttribute("ATTR_no_solid_camera"))

        self.attributes.add(XPlaneAttribute('ATTR_light_level', None, 1000))
        self.attributes.add(XPlaneAttribute('ATTR_poly_os', None, 1000))
        self.attributes.add(XPlaneAttribute('ATTR_draped', None, 1000))
        self.attributes.add(XPlaneAttribute('ATTR_no_draped', True, 1000))

        self.cockpitAttributes = XPlaneAttributes()
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_cockpit', None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_no_cockpit', True, 2000))
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_cockpit_region', None, 2000))

        self.conditions = []

    def collect(self):
        if len(self.blenderObject.data.materials) > 0 and \
           hasattr(self.blenderObject.data.materials[0], 'name'):
            mat = self.blenderObject.data.materials[0]
            self.name = mat.name
            self.blenderMaterial = mat
            self.options = mat.xplane # type: xplane_props.XPlaneMaterialSettings

            if mat.xplane.draw:
                self.attributes['ATTR_draw_enable'].setValue(True)

                # add cockpit attributes
                self.collectCockpitAttributes(mat)

                # add light level attritubes
                self.collectLightLevelAttributes(mat)

                # add conditions
                self.collectConditions(mat)

                # polygon offsett attribute
                if mat.xplane.poly_os > 0:
                    self.attributes['ATTR_poly_os'].setValue(mat.xplane.poly_os)

                if mat.xplane.panel == False:
                    self.attributes['ATTR_draw_enable'].setValue(True)

                    # specular
                    # include texture intensity of specular texture if any
                    textureSpec = 0

                    for texture in mat.texture_slots:
                        if texture and texture.use_map_specular:
                            textureSpec += texture.specular_factor

                    #SPECIAL CASE!
                    if self.getEffectiveNormalMetalness() == False:
                        self.attributes['ATTR_shiny_rat'].setValue(mat.specular_intensity + textureSpec)

                    # blend
                    xplane_version = int(bpy.context.scene.xplane.version)
                    if xplane_version >= 1000:
                        xplane_blend_enum = mat.xplane.blend_v1000
                    
                    if xplane_version >= 1000:
                        if xplane_blend_enum == BLEND_OFF:
                            self.attributes['ATTR_no_blend'].setValue(mat.xplane.blendRatio)
                        elif xplane_blend_enum == BLEND_ON:
                            self.attributes['ATTR_blend'].setValue(True)
                        elif xplane_blend_enum == BLEND_SHADOW:
                            self.attributes['ATTR_shadow_blend'].setValue(True)
                    elif xplane_version < 1000:
                        if mat.xplane.blend:
                            self.attributes['ATTR_no_blend'].setValue(mat.xplane.blendRatio)
                        else:
                            self.attributes['ATTR_blend'].setValue(True)
                # draped
                if mat.xplane.draped:
                    self.attributes['ATTR_draped'].setValue(True)
                    self.attributes['ATTR_no_draped'].setValue(False)
                else:
                    self.attributes['ATTR_no_draped'].setValue(True)
            else:
                self.attributes['ATTR_draw_disable'].setValue(True)

            # surface type
            if mat.xplane.surfaceType != SURFACE_TYPE_NONE:
                if mat.xplane.deck:
                    self.attributes['ATTR_hard_deck'].setValue(mat.xplane.surfaceType)
                else:
                    self.attributes['ATTR_hard'].setValue(mat.xplane.surfaceType)
            else:
                self.attributes['ATTR_no_hard'].setValue(True)

            # camera collision
            if mat.xplane.solid_camera:
                self.attributes['ATTR_solid_camera'].setValue(True)
                self.attributes['ATTR_no_solid_camera'].setValue(False)
            else:
                self.attributes['ATTR_no_solid_camera'].setValue(True)

            # try to find uv layer
            if len(self.blenderObject.data.uv_textures) > 0:
                self.uv_name = self.blenderObject.data.uv_textures.active.name

            # try to detect textures
            self._detectTextures(mat)

            # add custom attributes
            self.collectCustomAttributes(mat)

        else:
            logger.error('%s: No Material found.' % self.blenderObject.name)

        self.attributes.order()

    def _detectTextures(self, mat):
        '''
        Detects the texture by using Blender's texture slot properties:
        Diffuse->Color, Shading->Emit, Geometry->Normal, and Specular-> Intensity
        '''
        for i in range(0, len(mat.texture_slots)):
            slot = mat.texture_slots[i]

            if slot and slot.use and slot.texture.type == 'IMAGE':
                if slot.texture.image is not None:
                    #Props->Texture->Influence->Diffuse->[X] Color
                    if slot.use_map_color_diffuse and self.texture == None:
                        self.texture = slot.texture.image.filepath
                    #Props->Texture->Influence->Shading->[X] Emit
                    elif slot.use_map_emit and self.textureLit == None:
                        self.textureLit = slot.texture.image.filepath
                    #Props->Texture->Influence->Geometry->[X] Normal
                    elif slot.use_map_normal and self.textureNormal == None:
                        self.textureNormal = slot.texture.image.filepath
                    #Props->Texture->Influence->Specular->[X] Intensity
                    elif slot.use_map_specular and self.textureSpecular == None:
                        self.textureSpecular = slot.texture.image.filepath
                else:
                    logger.error("Texture '{0}' has no image".format(slot.texture.name))
                    return

        # panel materials have only a color texture
        if self.options.panel:
            self.textureLit = None
            self.textureNormal = None
            self.textureSpecular = None

    def collectCustomAttributes(self, mat):
        xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        if mat.xplane.customAttributes:
            for attr in mat.xplane.customAttributes:
                if attr.reset:
                    commands.addReseter(attr.name, attr.reset)
                self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))


    def collectCockpitAttributes(self, mat):
        if mat.xplane.panel:
            self.cockpitAttributes['ATTR_cockpit'].setValue(True)
            self.cockpitAttributes['ATTR_no_cockpit'].setValue(None)
            cockpit_region = int(mat.xplane.cockpit_region)
            if cockpit_region > 0:
                self.cockpitAttributes['ATTR_cockpit_region'].setValue(cockpit_region - 1)

    # Method: collectLightLevelAttributes
    # Defines light level attributes in <attributes> based on settings in <XPlaneObjectSettings>.
    def collectLightLevelAttributes(self, mat):
        if mat.xplane.lightLevel:
            self.attributes['ATTR_light_level'].setValue((
                mat.xplane.lightLevel_v1,
                mat.xplane.lightLevel_v2,
                mat.xplane.lightLevel_dataref
            ))

    def collectConditions(self, mat):
        if mat.xplane.conditions:
            self.conditions = mat.xplane.conditions

    def write(self):
        debug = getDebug()
        o = ''
        indent = self.xplaneObject.xplaneBone.getIndent()

        if debug:
            o += indent + '# MATERIAL: %s\n' % (self.name)

        xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        for attr in self.attributes:
            o += commands.writeAttribute(self.attributes[attr], self.xplaneObject)

        # if the file is a cockpit file write all cockpit attributes
        if xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT or \
            (bpy.context.scene.xplane.version >= VERSION_1040 and \
            xplaneFile.options.export_type == EXPORT_TYPE_AIRCRAFT):
            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self.xplaneObject)

        return o

    # Method: isCompatibleTo
    # Checks if a material is compatible to other material based on an export type.
    #
    # Parameters:
    # refMat <XPlaneMaterial> - reference material to compare against
    # exportType <string> - one of "aircraft", "cockpit", "scenery", "instanced_scenery"
    #
    # Returns:
    #   list,list - A list of errors and a list of warnings
    def isCompatibleTo(self, refMat, exportType,autodetectTextures)->Tuple[List[str],List[str]]:
        import io_xplane2blender
        return io_xplane2blender.xplane_types.xplane_material_utils.compare(refMat, self, exportType,autodetectTextures)

    def isValid(self, exportType:str)->Tuple[List[str],List[str]]:
        '''
        # Method: isValid
        # Checks if material is valid based on an export type.
        #
        # Parameters:
        # exportType <string> - one of "aircraft", "cockpit", "scenery", "instanced_scenery"
        #
        # Returns:
        #   Tuple[List[str],Liststr]] A tuple of a list of errors and a list of warnings
        #   bool, list - True if Material is valid, else False + a list of errors
        '''
        return io_xplane2blender.xplane_types.xplane_material_utils.validate(self, exportType)

    # Method: getEffectiveNormalMetalness
    # Predicate that returns the effective value of NORMAL_METALNESS, taking into account the current xplane version
    #
    # Returns:
    # bool - True or false if the version of X-Plane chosen supports NORMAL_METALNESS and what its value is,
    # False if the current XPLane version doesn't support it
    def getEffectiveNormalMetalness(self)->bool:
        if int(bpy.context.scene.xplane.version) >= 1100:
            return self.options.normal_metalness
        else:
            return False
        
    # Method: getEffectiveBlendGlass
    # Predicate that returns the effective value of BLEND_GLASS, taking into account the current xplane version
    #
    # Returns:
    # bool - True or false if the version of X-Plane chosen supports BLEND_GLASS and what its value is,
    # False if the current XPLane version doesn't support it
    def getEffectiveBlendGlass(self)->bool:
        xplane_version  = int(bpy.context.scene.xplane.version)
        
        if xplane_version >= 1100:
            return self.options.blend_glass
        else:
            return False
