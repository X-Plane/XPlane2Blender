import bpy
import os
import platform
from collections import OrderedDict
from ..xplane_helpers import floatToStr, logger
from ..xplane_constants import *
from .xplane_attributes import XPlaneAttributes
from .xplane_attribute import XPlaneAttribute
from ..xplane_image_composer import getImageByFilepath, specularToGrayscale, normalWithoutAlpha, combineSpecularAndNormal

# Class: XPlaneHeader
# Create an OBJ header.
class XPlaneHeader():
    # Property: version
    # OBJ format version

    # Property: mode
    # The OBJ xplaneFile mode. ("default" or "cockpit"). This is currently not in use, I think.

    # Property: attributes
    # OrderedDict - Key value pairs of all Header attributes

    # Constructor: __init__
    #
    # Parameters:
    #   XPlaneFile xplaneFile - A <XPlaneFile>.
    #   int version - OBJ format version.
    def __init__(self, xplaneFile, version):
        self.version = version
        self.mode = "default"
        self.xplaneFile = xplaneFile

        self.attributes = XPlaneAttributes()

        # object attributes
        self.attributes.add(XPlaneAttribute("ATTR_layer_group", None))
        self.attributes.add(XPlaneAttribute("COCKPIT_REGION", None))
        self.attributes.add(XPlaneAttribute("DEBUG", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_cockpit_lit", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_tint", None))
        self.attributes.add(XPlaneAttribute("POINT_COUNTS", None))
        self.attributes.add(XPlaneAttribute("REQUIRE_WET", None))
        self.attributes.add(XPlaneAttribute("REQUIRE_DRY", None))
        self.attributes.add(XPlaneAttribute("SLOPE_LIMIT", None))
        self.attributes.add(XPlaneAttribute("slung_load_weight", None))
        self.attributes.add(XPlaneAttribute("TILTED", None))

        # shader attributes
        self.attributes.add(XPlaneAttribute("TEXTURE", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_LIT", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_NORMAL", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_no_blend", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_no_shadow", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_shadow_blend", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_specular", None))

        # draped shader attributes
        self.attributes.add(XPlaneAttribute("TEXTURE_DRAPED", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_DRAPED_NORMAL", None))
        self.attributes.add(XPlaneAttribute("BUMP_LEVEL", None))
        self.attributes.add(XPlaneAttribute("NO_BLEND", None))
        self.attributes.add(XPlaneAttribute("SPECULAR", None))

        # draped general attributes
        self.attributes.add(XPlaneAttribute("ATTR_layer_group_draped", None))
        self.attributes.add(XPlaneAttribute("ATTR_LOD_draped", None))

    def init(self):
        isInstance = self.xplaneFile.options.export_type == EXPORT_TYPE_INSTANCED_SCENERY
        isCockpit = self.xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT
        canHaveDraped = self.xplaneFile.options.export_type not in [EXPORT_TYPE_AIRCRAFT, EXPORT_TYPE_COCKPIT]

        # layer groups
        if self.xplaneFile.options.layer_group != LAYER_GROUP_NONE:
            self.attributes['ATTR_layer_group'].setValue((self.xplaneFile.options.layer_group, self.xplaneFile.options.layer_group_offset))

        # draped layer groups
        if canHaveDraped and self.xplaneFile.options.layer_group_draped != LAYER_GROUP_NONE:
            self.attributes['ATTR_layer_group_draped'].setValue((self.xplaneFile.options.layer_group_draped, self.xplaneFile.options.layer_group_draped_offset))

        # set slung load
        if self.xplaneFile.options.slungLoadWeight > 0:
            self.attributes['slung_load_weight'].setValue(self.xplaneFile.options.slungLoadWeight)

        # set Texture
        blenddir = os.path.dirname(bpy.context.blend_data.filepath)

        # normalize the exporpath
        if os.path.isabs(self.xplaneFile.filename):
            exportdir = os.path.dirname(os.path.normpath(self.xplaneFile.filename))
        else:
            exportdir = os.path.dirname(os.path.abspath(os.path.normpath(os.path.join(blenddir, self.xplaneFile.filename))))

        if self.xplaneFile.options.autodetectTextures:
            self._autodetectTextures()

        # standard textures
        if self.xplaneFile.options.texture != '':
            self.attributes['TEXTURE'].setValue(self.getTexturePath(self.xplaneFile.options.texture, exportdir, blenddir))

        if self.xplaneFile.options.texture_lit != '':
            self.attributes['TEXTURE_LIT'].setValue(self.getTexturePath(self.xplaneFile.options.texture_lit, exportdir, blenddir))

        if self.xplaneFile.options.texture_normal != '':
            self.attributes['TEXTURE_NORMAL'].setValue(self.getTexturePath(self.xplaneFile.options.texture_normal, exportdir, blenddir))

        if canHaveDraped:
            # draped textures
            if self.xplaneFile.options.texture_draped != '':
                self.attributes['TEXTURE_DRAPED'].setValue(self.getTexturePath(self.xplaneFile.options.texture_draped, exportdir, blenddir))

            if self.xplaneFile.options.texture_draped_normal != '':
                self.attributes['TEXTURE_DRAPED_NORMAL'].setValue(self.getTexturePath(self.xplaneFile.options.texture_draped_normal, exportdir, blenddir))

            if self.xplaneFile.referenceMaterials[1]:
                mat = self.xplaneFile.referenceMaterials[1]

                # draped bump level
                if mat.options.bump_level != 1.0:
                    self.attributes['BUMP_LEVEL'].setValue(mat.bump_level)

                # draped no blend
                self.attributes['NO_BLEND'] = mat.attributes['ATTR_no_blend']
                # prevent of writing again in material
                mat.attributes['ATTR_no_blend'].setValue(None)

                # draped specular
                self.attributes['SPECULAR'] = mat.attributes['ATTR_shiny_rat']
                # prevent of writing again in material
                mat.attributes['ATTR_shiny_rat'].setValue(None)

            # draped LOD
            if self.xplaneFile.options.lod_draped != 0.0:
                self.attributes['ATTR_LOD_draped'].setValue(self.xplaneFile.options.lod_draped)

        # set cockpit regions
        if isCockpit:
            num_regions = int(self.xplaneFile.options.cockpit_regions)

            if num_regions > 0:
                self.attributes['COCKPIT_REGION'].removeValues()
                for i in range(0, num_regions):
                    cockpit_region = self.xplaneFile.options.cockpit_region[i]
                    self.attributes['COCKPIT_REGION'].addValue((
                        cockpit_region.left,
                        cockpit_region.top,
                        cockpit_region.left + (2 ** cockpit_region.width),
                        cockpit_region.top + (2 ** cockpit_region.height)
                    ))

        # get point counts
        tris = len(self.xplaneFile.mesh.vertices)
        lines = 0
        lights = len(self.xplaneFile.lights.items)
        indices = len(self.xplaneFile.mesh.indices)

        self.attributes['POINT_COUNTS'].setValue((tris, lines, lights, indices))

        xplane_version = int(bpy.context.scene.xplane.version)

        # v1000
        if xplane_version >= 1000:
            if self.xplaneFile.options.export_type == EXPORT_TYPE_INSTANCED_SCENERY and\
               self.xplaneFile.referenceMaterials[0]:
                mat = self.xplaneFile.referenceMaterials[0]

                # no blend
                attr = mat.attributes['ATTR_no_blend']
                self.attributes['GLOBAL_no_blend'] = attr
                self.xplaneFile.commands.written['ATTR_no_blend'] = attr.getValue()

                # shadow blend
                attr = mat.attributes['ATTR_shadow_blend']
                self.attributes['GLOBAL_shadow_blend'] = attr
                self.xplaneFile.commands.written['ATTR_shadow_blend'] = attr.getValue()

                # specular
                attr = mat.attributes['ATTR_shiny_rat']
                self.attributes['GLOBAL_specular'] = attr
                self.xplaneFile.commands.written['ATTR_shiny_rat'] = attr.getValue()

                # tint
                if mat.options.tint:
                    self.attributes['GLOBAL_tint'].setValue((mat.options.tint_albedo, mat.options.tint_emissive))

            if not isCockpit:
                # tilted
                if self.xplaneFile.options.tilted == True:
                    self.attributes['TILTED'].setValue(True)

                # slope_limit
                if self.xplaneFile.options.slope_limit == True:
                    self.attributes['SLOPE_LIMIT'].setValue((
                        self.xplaneFile.options.slope_limit_min_pitch,
                        self.xplaneFile.options.slope_limit_max_pitch,
                        self.xplaneFile.options.slope_limit_min_roll,
                        self.xplaneFile.options.slope_limit_max_roll
                    ))

                # require surface
                if self.xplaneFile.options.require_surface == REQUIRE_SURFACE_WET:
                    self.attributes['REQUIRE_WET'].setValue(True)
                elif self.xplaneFile.options.require_surface == REQUIRE_SURFACE_DRY:
                    self.attributes['REQUIRE_DRY'].setValue(True)

        # v1010
        if xplane_version >= 1010:
            # shadow
            if self.xplaneFile.options.shadow == False:
                self.attributes['GLOBAL_no_shadow'].setValue(True)

            # cockpit_lit
            if isCockpit and self.xplaneFile.options.cockpit_lit == True:
                self.attributes['GLOBAL_cockpit_lit'].setValue(True)

        # add custom attributes
        for attr in self.xplaneFile.options.customAttributes:
            self.attributes.add(XPlaneAttribute(attr.name, attr.value))

    def _getCompositeNormalTexture(self, textureNormal, textureSpecular):
        normalImage = None
        specularImage = None
        texture = None
        image = None
        filepath = None
        blenddir = os.path.dirname(bpy.context.blend_data.filepath)
        channels = 4

        if textureNormal:
            normalImage = getImageByFilepath(textureNormal)

        if textureSpecular:
            specularImage = getImageByFilepath(textureSpecular)

        # only normals, no specular
        if normalImage and not specularImage:
            filename, extension = os.path.splitext(textureNormal)
            image = normalWithoutAlpha(normalImage, normalImage.name + '_nm')
            filepath = texture = filename + '_nm' + extension
            channels = 3

        # normal + specular
        elif normalImage and specularImage:
            filename, extension = os.path.splitext(textureNormal)
            image = combineSpecularAndNormal(specularImage, normalImage, normalImage.name + '_nm_spec')
            filepath = texture = filename + '_nm_spec' + extension
            channels = 4

        # specular only
        elif not normalImage and specularImage:
            filename, extension = os.path.splitext(textureSpecular)
            image = specularToGrayscale(specularImage, specularImage.name + '_spec')
            filepath = texture = filename + '_spec' + extension
            channels = 1

        if image:
            savepath = filepath
            # remove trailing double slash
            if savepath[0:2] == '//':
                savepath = savepath[2:]
            savepath = os.path.join(blenddir, savepath)

            color_mode = bpy.context.scene.render.image_settings.color_mode
            if channels == 4:
                bpy.context.scene.render.image_settings.color_mode = 'RGBA'
            elif channels == 3:
                bpy.context.scene.render.image_settings.color_mode = 'RGB'
            elif channels == 1:
                bpy.context.scene.render.image_settings.color_mode = 'BW'
            image.save_render(savepath, bpy.context.scene)
            image.filepath = filepath

            # restore color_mode
            bpy.context.scene.render.image_settings.color_mode = color_mode

        return texture

    def _autodetectTextures(self):
        texture = None
        textureLit = None
        textureNormal = None
        textureSpecular = None
        textureDraped = None
        textureDrapedNormal = None
        textureDrapedSpecular = None
        xplaneObjects = self.xplaneFile.getObjectsList()

        for xplaneObject in xplaneObjects:
            if xplaneObject.type == XPLANE_OBJECT_TYPE_PRIMITIVE:
                mat = xplaneObject.material

                if mat.uv_name == None:
                    logger.warn('Object "%s" has no UV-Map.' % xplaneObject.name)

                if mat.options.draped:
                    if textureDraped == None and mat.texture:
                        textureDraped = mat.texture

                    if textureDrapedNormal == None and mat.textureNormal:
                        textureDrapedNormal = mat.textureNormal

                    if textureDrapedSpecular == None and mat.textureSpecular:
                        textureDrapedSpecular = mat.textureSpecular
                else:
                    if texture == None and mat.texture:
                        texture = mat.texture

                    if textureLit == None and mat.textureLit:
                        textureLit = mat.textureLit

                    if textureNormal == None and mat.textureNormal:
                        textureNormal = mat.textureNormal

                    if textureSpecular == None and mat.textureSpecular:
                        textureSpecular = mat.textureSpecular

        # now go through all textures again and list any objects with different textures
        for xplaneObject in xplaneObjects:
            if xplaneObject.type == XPLANE_OBJECT_TYPE_PRIMITIVE:
                mat = xplaneObject.material

                if mat.options.draped:
                    if textureDraped and textureDraped != mat.texture:
                        logger.warn('Object "%s" has a different or missing draped texture.' % xplaneObject.name)

                    if textureDrapedNormal and textureDrapedNormal != mat.textureNormal:
                        logger.warn('Object "%s" has a different or missing draped normal/specular texture.' % xplaneObject.name)
                else:
                    if texture and texture != mat.texture:
                        logger.warn('Object "%s" has a different or missing color texture.' % xplaneObject.name)

                    if textureLit and textureLit != mat.textureLit:
                        logger.warn('Object "%s" has a different or missing night/lit texture.' % xplaneObject.name)

                    if textureNormal and textureNormal != mat.textureNormal:
                        logger.warn('Object "%s" has a different or missing normal/specular texture.' % xplaneObject.name)

        # generate composite normal texture if needed
        if mat.options.draped:
            textureDrapedNormal = self._getCompositeNormalTexture(textureDrapedNormal, textureDrapedSpecular)
        else:
            textureNormal = self._getCompositeNormalTexture(textureNormal, textureSpecular)

        self.xplaneFile.options.texture = texture or ''
        self.xplaneFile.options.texture_normal = textureNormal or ''
        self.xplaneFile.options.texture_lit = textureLit or ''
        self.xplaneFile.options.texture_draped = textureDraped or ''
        self.xplaneFile.options.texture_draped_normal = textureDrapedNormal or ''


    # Method: getTexturePath
    # Returns the texture path relative to the exported OBJ
    #
    # Parameters:
    #   string texpath - the relative or absolute texture path as chosen by the user
    #   string exportdir - the absolute export directory
    #   string blenddir - the absolute path to the directory the blend is in
    #
    # Returns:
    #   string - the texture path relative to the exported OBJ
    def getTexturePath(self, texpath, exportdir, blenddir):
        # blender stores relative paths on UNIX with leading double slash
        if texpath[0:2] == '//':
            texpath = texpath[2:]

        if os.path.isabs(texpath):
            texpath = os.path.abspath(os.path.normpath(texpath))
        else:
            texpath = os.path.abspath(os.path.normpath(os.path.join(blenddir, texpath)))

        texpath = os.path.relpath(texpath, exportdir)

        return texpath

    # Method: write
    # Returns the OBJ header.
    #
    # Returns:
    #   string - OBJ header
    def write(self):
        self.init()

        system = platform.system()

        # line ending types (I = UNIX/DOS, A = MacOS)
        if 'Mac OS' in system:
            o = 'A\n'
        else:
            o = 'I\n'

        # version number
        if self.version >= 8:
            o += '800\n'

        o += 'OBJ\n\n'

        # attributes
        for name in self.attributes:
            attr = self.attributes[name]
            values = attr.getValues()

            if values[0] != None:
                if len(values) > 1:
                    for vi in range(0, len(values)):
                        o += '%s\t%s\n' % (attr.name, attr.getValueAsString(vi))

                else:
                    o += '%s\t%s\n' % (attr.name, attr.getValueAsString())

        return o
