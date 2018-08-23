import os
import platform
import re
from collections import OrderedDict

import bpy
from io_xplane2blender.xplane_constants import (EXPORT_TYPE_AIRCRAFT,
                                                EXPORT_TYPE_SCENERY)

from ..xplane_constants import *
from ..xplane_helpers import floatToStr, logger, resolveBlenderPath
from ..xplane_image_composer import (combineSpecularAndNormal,
                                     getImageByFilepath, normalWithoutAlpha,
                                     specularToGrayscale)
from .xplane_attribute import XPlaneAttribute
from .xplane_attributes import XPlaneAttributes

from typing import List

# Class: XPlaneHeader
# Create an OBJ header.
class XPlaneHeader():
    '''
    Stores and writes OBJ info related to the OBJ8 header, such as POINT_COUNTS and TEXTURE.
    Also the starting point for is responsible for autodetecting and compositing textures.
    '''

    # Constructor: __init__
    #
    # Parameters:
    #   XPlaneFile xplaneFile - A <XPlaneFile>.
    #   int obj_version - OBJ format version.
    def __init__(self, xplaneFile:'XPlaneFile', obj_version:int):
        self.obj_version = obj_version
        self.xplaneFile = xplaneFile

        # A list of tuples in the form of (lib path, physical path)
        # for example, if the path in the box is 'lib/g10/cars/car.obj'
        # and the file is getting exported to '/code/x-plane/Custom Scenery/Kansas City/cars/honda.obj'
        # you would have ('lib/g10/cars/car.obj','cars/honda.obj')
        self.export_path_dirs = [] # type: List[str,str]

        for export_path_directive in self.xplaneFile.options.export_path_directives:
            export_path_directive.export_path = export_path_directive.export_path.lstrip()
            if len(export_path_directive.export_path) == 0:
                continue

            cleaned_path = bpy.data.filepath.replace('\\', '/')
            #              everything before
            #               |         scenery directory
            #               |               |        one directory afterward
            #               |               |                   |    optional directories and path to .blend file
            #               |               |                   |        |
            #               v               v                   v        v
            regex_str = r"(.*(Custom Scenery|default_scenery)(/[^/]+/)(.*))"
            potential_match = re.match(regex_str, cleaned_path)

            if potential_match is None:
                logger.error('Export path %s is not properly formed. Ensure it contains the words "Custom Scenery" or "default_scenery" followed by a directory')
                return
            else:
                last_folder = os.path.dirname(potential_match.group(4)).split('/')[-1:][0]

                if len(last_folder) > 0:
                    last_folder += '/' #Re-append slash

                self.export_path_dirs.append((export_path_directive.export_path, last_folder + xplaneFile.filename + ".obj"))

        self.attributes = XPlaneAttributes()
        
        # object attributes
        self.attributes.add(XPlaneAttribute("PARTICLE_SYSTEM", None))
        self.attributes.add(XPlaneAttribute("ATTR_layer_group", None))
        self.attributes.add(XPlaneAttribute("COCKPIT_REGION", None))
        self.attributes.add(XPlaneAttribute("DEBUG", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_cockpit_lit", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_tint", None))
        self.attributes.add(XPlaneAttribute("REQUIRE_WET", None))
        self.attributes.add(XPlaneAttribute("REQUIRE_DRY", None))
        self.attributes.add(XPlaneAttribute("SLOPE_LIMIT", None))
        self.attributes.add(XPlaneAttribute("slung_load_weight", None))
        self.attributes.add(XPlaneAttribute("TILTED", None))

        # shader attributes
        self.attributes.add(XPlaneAttribute("TEXTURE", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_LIT", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_NORMAL", None))
        self.attributes.add(XPlaneAttribute("NORMAL_METALNESS", None))#NORMAL_METALNESS for textures
        self.attributes.add(XPlaneAttribute("GLOBAL_no_blend", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_no_shadow", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_shadow_blend", None))
        self.attributes.add(XPlaneAttribute("GLOBAL_specular", None))
        self.attributes.add(XPlaneAttribute("BLEND_GLASS", None))
        
        # draped shader attributes
        self.attributes.add(XPlaneAttribute("TEXTURE_DRAPED", None))
        self.attributes.add(XPlaneAttribute("TEXTURE_DRAPED_NORMAL", None))
        
        # This is a hack to get around duplicate keynames!
        # There is no NORMAL_METALNESS_draped_hack,
        # self.write will check later for draped_hack and remove it
        #
        # If later on we have more duplicate keynames we'll figure something
        # else out. -Ted, 8/9/2018
        self.attributes.add(XPlaneAttribute("NORMAL_METALNESS_draped_hack", None))#NORMAL_METALNESS for draped textures
        self.attributes.add(XPlaneAttribute("BUMP_LEVEL", None))
        self.attributes.add(XPlaneAttribute("NO_BLEND", None))
        self.attributes.add(XPlaneAttribute("SPECULAR", None))

        # draped general attributes
        self.attributes.add(XPlaneAttribute("ATTR_layer_group_draped", None))
        self.attributes.add(XPlaneAttribute("ATTR_LOD_draped", None))

        self.attributes.add(XPlaneAttribute("EXPORT", None))

        # previously labeled object attributes, it must be the last thing
        self.attributes.add(XPlaneAttribute("POINT_COUNTS", None))


    # TODO: Shouldn't this just be inside XPlaneHeader.write if it is only called once and only here?
    # If not should it be called collect?
    def init(self):
        isAircraft = self.xplaneFile.options.export_type == EXPORT_TYPE_AIRCRAFT
        isCockpit  = self.xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT
        isInstance = self.xplaneFile.options.export_type == EXPORT_TYPE_INSTANCED_SCENERY
        isScenery  = self.xplaneFile.options.export_type == EXPORT_TYPE_SCENERY

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
            self.attributes['TEXTURE'].setValue(self.getPathRelativeToOBJ(self.xplaneFile.options.texture, exportdir, blenddir))

        if self.xplaneFile.options.texture_lit != '':
            self.attributes['TEXTURE_LIT'].setValue(self.getPathRelativeToOBJ(self.xplaneFile.options.texture_lit, exportdir, blenddir))

        if self.xplaneFile.options.texture_normal != '':
            self.attributes['TEXTURE_NORMAL'].setValue(self.getPathRelativeToOBJ(self.xplaneFile.options.texture_normal, exportdir, blenddir))


        xplane_version = int(bpy.context.scene.xplane.version)
        if xplane_version >= 1100:
            mat = self.xplaneFile.referenceMaterials[0]
            if mat:
                self.attributes['NORMAL_METALNESS'].setValue(mat.getEffectiveNormalMetalness())
                has_texture_normal = self.attributes['TEXTURE_NORMAL'].getValue(0) is not None
                if has_texture_normal:
                    if mat.options.panel is False:
                        self.attributes['NORMAL_METALNESS']\
                                .setValue(mat.getEffectiveNormalMetalness())
                elif not has_texture_normal and mat.getEffectiveNormalMetalness():
                    logger.warn("Material '%s' has Normal Metalness, but no Normal Texture" % mat.name)
        
        if xplane_version >= 1100:
            if self.xplaneFile.referenceMaterials[0] or self.xplaneFile.referenceMaterials[1]:
                mat = self.xplaneFile.referenceMaterials[0] or self.xplaneFile.referenceMaterials[1]
                self.attributes['BLEND_GLASS'].setValue(mat.getEffectiveBlendGlass())

        if canHaveDraped:
            # draped textures
            if self.xplaneFile.options.texture_draped != '':
                self.attributes['TEXTURE_DRAPED'].setValue(self.getPathRelativeToOBJ(self.xplaneFile.options.texture_draped, exportdir, blenddir))

            if self.xplaneFile.options.texture_draped_normal != '':
                #Special "1.0" required by X-Plane
                #"That's the scaling factor for the normal map available ONLY for the draped info. Without that , it can't find the texture.
                #That makes a non-fatal error in x-plane. Without the normal map, the metalness directive is ignored" -Ben Supnik, 07/06/17 8:35pm
                self.attributes['TEXTURE_DRAPED_NORMAL'].setValue("1.0 " + self.getPathRelativeToOBJ(self.xplaneFile.options.texture_draped_normal, exportdir, blenddir))
            
            if self.xplaneFile.referenceMaterials[1]:
                mat = self.xplaneFile.referenceMaterials[1]
                if xplane_version >= 1100:
                    has_texture_draped_nml = self.attributes['TEXTURE_DRAPED_NORMAL'].getValue(0) is not None
                    if has_texture_draped_nml:
                        if mat.options.panel is False:
                            self.attributes['NORMAL_METALNESS_draped_hack'].setValue(mat.getEffectiveNormalMetalness())
                    elif not has_texture_draped_nml and mat.getEffectiveNormalMetalness():
                        logger.warn("Material '%s' has Normal Metalness, but no Draped Normal Texture" % mat.name)

                # draped bump level
                if mat.options.bump_level != 1.0:
                    self.attributes['BUMP_LEVEL'].setValue(mat.bump_level)

                # draped no blend
                self.attributes['NO_BLEND'].setValue(mat.attributes['ATTR_no_blend'].getValue())
                # prevent of writing again in material
                mat.attributes['ATTR_no_blend'].setValue(None)

                # draped specular
                if xplane_version >= 1100 and mat.getEffectiveNormalMetalness():
                    # draped specular
                    self.attributes['SPECULAR'].setValue(1.0)
                else:
                    # draped specular
                    self.attributes['SPECULAR'].setValue(mat.attributes['ATTR_shiny_rat'].getValue())
                
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


        if xplane_version >= 1130:
            if self.xplaneFile.options.particle_system_file:
                blenddir = os.path.dirname(bpy.context.blend_data.filepath)

                # normalize the exporpath
                if os.path.isabs(self.xplaneFile.filename):
                    exportdir = os.path.dirname(os.path.normpath(self.xplaneFile.filename))
                else:
                    exportdir = os.path.dirname(
                        os.path.abspath(
                            os.path.normpath(
                                os.path.join(blenddir, self.xplaneFile.filename)
                                )))
                pss = self.getPathRelativeToOBJ(
                    self.xplaneFile.options.particle_system_file,
                    exportdir,
                    blenddir
                )

                objs = self.xplaneFile.objects

                if not list(filter(lambda obj: obj[1].type == "EMPTY" and\
                        obj[1].blenderObject.xplane.special_empty_props.special_type == EMPTY_USAGE_EMITTER_PARTICLE or\
                        obj[1].blenderObject.xplane.special_empty_props.special_type == EMPTY_USAGE_EMITTER_SOUND,\
                        objs.items())):
                    logger.warn("Particle System File {} is given, but no emitter objects are used".format(pss))

                if not pss.endswith('.pss'):
                    logger.error("Particle System File {} must be a .pss file".format(pss))

                self.attributes["PARTICLE_SYSTEM"].setValue(pss)

        # get point counts
        tris = len(self.xplaneFile.mesh.vertices)
        lines = 0
        lights = len(self.xplaneFile.lights.items)
        indices = len(self.xplaneFile.mesh.indices)

        self.attributes['POINT_COUNTS'].setValue((tris, lines, lights, indices))

        write_user_specular_values = True

        if xplane_version >= 1100 and self.xplaneFile.referenceMaterials[0]:
            mat = self.xplaneFile.referenceMaterials[0]
            if mat.getEffectiveNormalMetalness():
                self.attributes['GLOBAL_specular'].setValue(1.0)
                self.xplaneFile.commands.written['ATTR_shiny_rat'] = 1.0 # Here we are fooling ourselves
                write_user_specular_values = False #It will be skipped from now on
        
        # v1000
        if xplane_version >= 1000:
            if self.xplaneFile.options.export_type == EXPORT_TYPE_INSTANCED_SCENERY and\
               self.xplaneFile.referenceMaterials[0]:
                mat = self.xplaneFile.referenceMaterials[0]

                # no blend
                attr = mat.attributes['ATTR_no_blend']
                if attr.getValue():
                    self.attributes['GLOBAL_no_blend'].setValue(attr.getValue())
                    self.xplaneFile.commands.written['ATTR_no_blend'] = attr.getValue()

                # shadow blend
                attr = mat.attributes['ATTR_shadow_blend']
                if attr.getValue():
                    self.attributes['GLOBAL_shadow_blend'].setValue(attr.getValue())
                    self.xplaneFile.commands.written['ATTR_shadow_blend'] = attr.getValue()

                # specular
                attr = mat.attributes['ATTR_shiny_rat']
                if write_user_specular_values and attr.getValue():
                    self.attributes['GLOBAL_specular'].setValue(attr.getValue())
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
            is_scenery_like_export = (self.xplaneFile.options.export_type == EXPORT_TYPE_SCENERY or \
                                      self.xplaneFile.options.export_type == EXPORT_TYPE_INSTANCED_SCENERY)

            if self.xplaneFile.options.shadow == False and is_scenery_like_export:
                self.attributes['GLOBAL_no_shadow'].setValue(True)

            # cockpit_lit
            if isCockpit and (self.xplaneFile.options.cockpit_lit == True or xplane_version >= 1100):
                self.attributes['GLOBAL_cockpit_lit'].setValue(True)

        if len(self.export_path_dirs):
            self.attributes["EXPORT"].value = [path_dir[0] + " " + path_dir[1]\
                                                for path_dir in self.export_path_dirs]

        for attr in self.xplaneFile.options.customAttributes:
            self.attributes.add(XPlaneAttribute(attr.name, attr.value))


    def _compositeNormalTextureNeedsRecompile(self, compositePath, sourcePaths):
        compositePath = resolveBlenderPath(compositePath)

        if not os.path.exists(compositePath):
            return True
        else:
            compositeTime = os.path.getmtime(compositePath)

            for sourcePath in sourcePaths:
                sourcePath = resolveBlenderPath(sourcePath)

                if os.path.exists(sourcePath):
                    sourceTime = os.path.getmtime(sourcePath)

                    if sourceTime > compositeTime:
                        return True

        return False

    def _getCompositeNormalTexture(self, textureNormal, textureSpecular):
        normalImage = None
        specularImage = None
        texture = None
        image = None
        filepath = None
        channels = 4

        if textureNormal:
            normalImage = getImageByFilepath(textureNormal)

        if textureSpecular:
            specularImage = getImageByFilepath(textureSpecular)

        # only normals, no specular
        if normalImage and not specularImage:
            filename, extension = os.path.splitext(textureNormal)
            filepath = texture = filename + '_nm' + extension
            channels = 3

            if self._compositeNormalTextureNeedsRecompile(filepath, (textureNormal)):
                image = normalWithoutAlpha(normalImage, normalImage.name + '_nm')

        # normal + specular
        elif normalImage and specularImage:
            filename, extension = os.path.splitext(textureNormal)
            filepath = texture = filename + '_nm_spec' + extension
            channels = 4

            if self._compositeNormalTextureNeedsRecompile(filepath, (textureNormal, textureSpecular)):
                image = combineSpecularAndNormal(specularImage, normalImage, normalImage.name + '_nm_spec')

        # specular only
        elif not normalImage and specularImage:
            filename, extension = os.path.splitext(textureSpecular)
            filepath = texture = filename + '_spec' + extension
            channels = 1

            if self._compositeNormalTextureNeedsRecompile(filepath, (textureSpecular)):
                image = specularToGrayscale(specularImage, specularImage.name + '_spec')

        if image:
            savepath = resolveBlenderPath(filepath)

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
        hasDraped = False

        for xplaneObject in xplaneObjects:
            # skip non-mesh objects and objects without a xplane bone
            # also skip invalid materials
            if xplaneObject.type == 'MESH' and \
               xplaneObject.xplaneBone and \
               xplaneObject.material.options:
                mat = xplaneObject.material

                if mat.uv_name == None and mat.options.draw:
                    logger.warn('Object "%s" has no UV-Map.' % xplaneObject.name)

                if mat.options.draped:
                    hasDraped = True

                    if textureDraped == None and mat.texture:
                        textureDraped = mat.texture

                    if textureDrapedNormal == None and mat.textureNormal:
                        textureDrapedNormal = mat.textureNormal

                    if textureDrapedSpecular == None and mat.textureSpecular:
                        textureDrapedSpecular = mat.textureSpecular
                elif not mat.options.panel and not mat.options.solid_camera:
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
            # skip non-mesh objects and objects without a xplane bone
            if xplaneObject.type == 'MESH' and xplaneObject.xplaneBone:
                mat = xplaneObject.material

                if mat.options.draped:
                    if textureDraped and \
                       self._getCanonicalTexturePath(textureDraped) != self._getCanonicalTexturePath(mat.texture):
                        logger.warn('Material "%s" in Object "%s" must use the draped texture "%s" but uses "%s".' % (mat.name, xplaneObject.name, textureDraped, mat.texture))

                    if textureDrapedNormal and \
                       self._getCanonicalTexturePath(textureDrapedNormal) != self._getCanonicalTexturePath(mat.textureNormal):
                        logger.warn('Material "%s" in Object "%s" must use the draped normal/specular texture "%s" but uses "%s".' % (mat.name, xplaneObject.name, textureDrapedNormal, mat.textureNormal))
                elif not mat.options.panel and not mat.options.solid_camera:
                    if texture and \
                       self._getCanonicalTexturePath(texture) != self._getCanonicalTexturePath(mat.texture):
                        logger.warn('Material "%s" in Object "%s" must use the color texture "%s" but uses "%s".' % (mat.name, xplaneObject.name, texture, mat.texture))

                    if textureLit and \
                       self._getCanonicalTexturePath(textureLit) != self._getCanonicalTexturePath(mat.textureLit):
                        logger.warn('Material "%s" in Object "%s" must use the night/lit texture "%s" but uses "%s".' % (mat.name, xplaneObject.name, textureLit, mat.textureLit))

                    if textureNormal and \
                       self._getCanonicalTexturePath(textureNormal) != self._getCanonicalTexturePath(mat.textureNormal):
                        logger.warn('Material "%s" in Object "%s" must use the normal/specular texture "%s" but uses "%s".' % (mat.name, xplaneObject.name, textureNormal, mat.textureNormal))

        # generate composite normal texture if needed
        if bpy.context.scene.xplane.compositeTextures:
            textureNormal = self._getCompositeNormalTexture(textureNormal, textureSpecular)

            if hasDraped:
                textureDrapedNormal = self._getCompositeNormalTexture(textureDrapedNormal, textureDrapedSpecular)

        self.xplaneFile.options.texture = texture or ''
        self.xplaneFile.options.texture_normal = textureNormal or ''
        self.xplaneFile.options.texture_lit = textureLit or ''
        self.xplaneFile.options.texture_draped = textureDraped or ''
        self.xplaneFile.options.texture_draped_normal = textureDrapedNormal or ''


    # Method: getPathRelativeToOBJ
    # Returns the resource path relative to the exported OBJ
    #
    # Parameters:
    #   string respath - the relative or absolute resource path (such as a texture or .pss file) as chosen by the user
    #   string exportdir - the absolute export directory
    #   string blenddir - the absolute path to the directory the blend is in
    #
    # Returns:
    #   string - the resource path relative to the exported OBJ
    def getPathRelativeToOBJ(self, respath:str, exportdir:str, blenddir:str)->str:
        # blender stores relative paths on UNIX with leading double slash
        if respath[0:2] == '//':
            respath = respath[2:]

        if os.path.isabs(respath):
            respath = os.path.abspath(os.path.normpath(respath))
        else:
            respath = os.path.abspath(os.path.normpath(os.path.join(blenddir, respath)))

        respath = os.path.relpath(respath, exportdir)

        #Replace any \ separators if you're on Windows. For other platforms this does nothing
        return respath.replace("\\","/")

    # Method: _getCanonicalTexturePath
    # Returns normalized (canonical) path to texture
    #
    # Parameters:
    #   string texpath - the relative or absolute texture path as chosen by the user
    #
    # Returns:
    #   string - the absolute/normalized path to the texture
    def _getCanonicalTexturePath(self, texpath):
        blenddir = os.path.dirname(bpy.context.blend_data.filepath)

        if texpath[0:2] == '//':
            texpath = texpath[2:]

        if os.path.isabs(texpath):
            texpath = os.path.abspath(os.path.normpath(texpath))
        else:
            texpath = os.path.abspath(os.path.normpath(os.path.join(blenddir, texpath)))

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

        # obj version number
        if self.obj_version >= 8:
            o += '800\n'

        o += 'OBJ\n\n'

        self.attributes.move_to_end('POINT_COUNTS')

        # attributes
        for attr_name,attr in self.attributes.items():
            if attr_name == "NORMAL_METALNESS_draped_hack":
                # Hack: See note in __init__
                attr.name = "NORMAL_METALNESS"

            values = attr.value
            if values[0] != None:
                if len(values) > 1:
                    for vi in range(0, len(values)):
                        o += '%s\t%s\n' % (attr.name, attr.getValueAsString(vi))

                else:
                    #This is a double fix. Boolean values with True get written (sans the word true), False does not,
                    #and strings that start with True or False don't get treated as as booleans 
                    is_bool = len(values) == 1 and isinstance(values[0],bool)
                    if is_bool and values[0] == True:
                        o += '%s\n' % (attr.name)
                    elif not is_bool: #True case already taken care of, don't care about False case - implicitly skipped
                        o += '%s\t%s\n' % (attr.name, attr.getValueAsString())


        return o

