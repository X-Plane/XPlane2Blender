import bpy
import os
import platform
from collections import OrderedDict
from ..xplane_helpers import floatToStr

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

        # TODO: use Attributes object instead
        self.attributes = OrderedDict([
            ("TEXTURE", None),
            ("TEXTURE_LIT", None),
            ("TEXTURE_NORMAL", None),
            ("POINT_COUNTS", None),
            ("slung_load_weight", None),
            ("COCKPIT_REGION", None),
            ("GLOBAL_no_blend", None),
            ("GLOBAL_shadow_blend", None),
            ("GLOBAL_specular", None),
            ("GLOBAL_no_shadow", None),
            ("SLOPE_LIMIT", None),
            ("TILTED", None),
            ("REQUIRE_WET", None),
            ("REQUIRE_DRY", None),
            ("GLOBAL_cockpit_lit", None)
        ])

    def init(self):
        # set slung load
        if self.xplaneFile.options.slungLoadWeight > 0:
            self.attributes['slung_load_weight'] = floatToStr(self.xplaneFile.options.slungLoadWeight)

        # set Texture
        blenddir = os.path.dirname(bpy.context.blend_data.filepath)

        # normalize the exporpath
        if os.path.isabs(self.xplaneFile.filename):
            exportdir = os.path.dirname(os.path.normpath(self.xplaneFile.filename))
        else:
            exportdir = os.path.dirname(os.path.abspath(os.path.normpath(os.path.join(blenddir, self.xplaneFile.filename))))

        if self.xplaneFile.options.texture != '':
            self.attributes['TEXTURE'] = self.getTexturePath(self.xplaneFile.options.texture, exportdir, blenddir)

        if self.xplaneFile.options.texture_lit!='':
            self.attributes['TEXTURE_LIT'] = self.getTexturePath(self.xplaneFile.options.texture_lit, exportdir, blenddir)

        if self.xplaneFile.options.texture_normal!='':
            self.attributes['TEXTURE_NORMAL'] = self.getTexturePath(self.xplaneFile.options.texture_normal, exportdir, blenddir)

        # set cockpit regions
        num_regions = int(self.xplaneFile.options.cockpit_regions)

        if num_regions > 0:
            self.attributes['COCKPIT_REGION'] = []

            for i in range(0, num_regions):
                cockpit_region = self.xplaneFile.options.cockpit_region[i]
                self.attributes['COCKPIT_REGION'].append('%d\t%d\t%d\t%d' % (cockpit_region.left, cockpit_region.top, cockpit_region.left + (2 ** cockpit_region.width), cockpit_region.top + (2 ** cockpit_region.height)))

        # get point counts
        tris = len(self.xplaneFile.mesh.vertices)
        lines = 0
        lights = len(self.xplaneFile.lights.items)
        indices = len(self.xplaneFile.mesh.indices)

        self.attributes['POINT_COUNTS'] = "%d\t%d\t%d\t%d" % (tris, lines, lights, indices)

        xplane_version = int(bpy.context.scene.xplane.version)

        # v1000
        if xplane_version >= 1000:
            # blend
            if self.xplaneFile.options.blend == "off":
                self.attributes['GLOBAL_no_blend'] = floatToStr(self.xplaneFile.options.blendRatio)
            elif self.xplaneFile.options.blend == 'shadow':
                self.attributes['GLOBAL_shadow_blend'] = True

            # specular
            if self.xplaneFile.options.overrideSpecularity == True:
                self.attributes['GLOBAL_specular'] = floatToStr(self.xplaneFile.options.specular)

            # tilted
            if self.xplaneFile.options.tilted == True:
                self.attributes['TILTED'] = True

            # slope_limit
            if self.xplaneFile.options.slope_limit == True:
                self.attributes['SLOPE_LIMIT'] = '%s\t%s\t%s\t%s' % (
                    floatToStr(self.xplaneFile.options.slope_limit_min_pitch),
                    floatToStr(self.xplaneFile.options.slope_limit_max_pitch),
                    floatToStr(self.xplaneFile.options.slope_limit_min_roll),
                    floatToStr(self.xplaneFile.options.slope_limit_max_roll)
                )

            # require surface
            if self.xplaneFile.options.require_surface == 'wet':
                self.attributes['REQUIRE_WET'] = True
            elif self.xplaneFile.options.require_surface == 'dry':
                self.attributes['REQUIRE_DRY'] = True

        # v1010
        if xplane_version >= 1010:
            # shadow
            if self.xplaneFile.options.shadow == False:
                self.attributes['GLOBAL_no_shadow'] = True

            # cockpit_lit
            if self.xplaneFile.options.cockpit == True and self.xplaneFile.options.cockpit_lit == True:
                self.attributes['GLOBAL_cockpit_lit'] = True

        # add custom attributes
        for attr in self.xplaneFile.options.customAttributes:
            self.attributes[attr.name] = attr.value

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
        for attr in self.attributes:
            if self.attributes[attr] != None:
                if type(self.attributes[attr]).__name__ == 'list':
                    for value in self.attributes[attr]:
                        if value == True:
                            o += '%s\n' % attr
                        else:
                            o += '%s\t%s\n' % (attr, value)
                else:
                    if self.attributes[attr] == True:
                        o += '%s\n' % attr
                    else:
                        o += '%s\t%s\n' % (attr, self.attributes[attr])

        return o
