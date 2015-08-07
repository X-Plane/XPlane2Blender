import bpy
from ..xplane_config import getDebug
from ..xplane_helpers import floatToStr
from ..xplane_ui import showError
from .xplane_attributes import XPlaneAttributes
from .xplane_attribute import XPlaneAttribute

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
        self.texture = None
        self.uv_name = None
        self.name = None

        # Material
        self.attributes = XPlaneAttributes()
        self.attributes.add(XPlaneAttribute("ATTR_diffuse_rgb"))
        #self.attributes.add(XPlaneAttribute("ATTR_specular_rgb")) # useless according to Ben Supnik
        self.attributes.add(XPlaneAttribute("ATTR_shade_smooth", True))
        self.attributes.add(XPlaneAttribute("ATTR_shade_flat"))
        self.attributes.add(XPlaneAttribute("ATTR_emission_rgb"))
        self.attributes.add(XPlaneAttribute("ATTR_shiny_rat"))
        self.attributes.add(XPlaneAttribute("ATTR_hard"))
        self.attributes.add(XPlaneAttribute("ATTR_hard_deck"))
        self.attributes.add(XPlaneAttribute("ATTR_no_hard"))
        self.attributes.add(XPlaneAttribute("ATTR_cull"))
        self.attributes.add(XPlaneAttribute("ATTR_no_cull"))
        self.attributes.add(XPlaneAttribute("ATTR_depth"))
        self.attributes.add(XPlaneAttribute("ATTR_no_depth"))
        self.attributes.add(XPlaneAttribute("ATTR_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_shadow_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_no_blend"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_enable"))
        self.attributes.add(XPlaneAttribute("ATTR_draw_disable"))
        self.attributes.add(XPlaneAttribute("ATTR_solid_camera"))
        self.attributes.add(XPlaneAttribute("ATTR_no_solid_camera"))

        self.attributes.add(XPlaneAttribute('ATTR_light_level', None, 1000))
        self.attributes.add(XPlaneAttribute('ATTR_poly_os', None, 1000))

        self.cockpitAttributes = XPlaneAttributes()
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_cockpit', None, 2000))
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_no_cockpit', True))
        self.cockpitAttributes.add(XPlaneAttribute('ATTR_cockpit_region', None, 2000))

        self.conditions = []

    def collect(self):
        if (len(self.blenderObject.data.materials) > 0 and hasattr(self.blenderObject.data.materials[0], 'name')):
            mat = self.blenderObject.data.materials[0]
            self.name = mat.name

            if mat.xplane.draw:
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

                    # diffuse
                    #if mat.diffuse_intensity>0:
                    diffuse = [mat.diffuse_intensity*mat.diffuse_color[0],
                                mat.diffuse_intensity*mat.diffuse_color[1],
                                mat.diffuse_intensity*mat.diffuse_color[2]]
                    self.attributes['ATTR_diffuse_rgb'].setValue((
                        diffuse[0],
                        diffuse[1],
                        diffuse[2]
                    ))

                    # specular
                    #if mat.specular_intensity>0:
                    # specular color is useless according to Ben Supnik
    #                specular = [mat.specular_color[0],
    #                            mat.specular_color[1],
    #                            mat.specular_color[2]]
                    #self.attributes['ATTR_specular_rgb'] = "%6.3f %6.3f %6.3f" % (specular[0], specular[1], specular[2])
                    if mat.xplane.overrideSpecularity:
                        self.attributes['ATTR_shiny_rat'].setValue(mat.xplane.shinyRatio)
                    else:
                        self.attributes['ATTR_shiny_rat'].setValue(mat.specular_intensity)

                    # emission
                    #if mat.emit>0:
                    emission = [mat.emit*mat.diffuse_color[0],
                                mat.emit*mat.diffuse_color[1],
                                mat.emit*mat.diffuse_color[2]]
                    self.attributes['ATTR_emission_rgb'].setValue((
                        emission[0],
                        emission[1],
                        emission[2]
                    ))

                    # blend
                    if (int(bpy.context.scene.xplane.version) >= 1000):
                        if mat.xplane.blend_v1000 == 'off':
                            self.attributes['ATTR_no_blend'].setValue(mat.xplane.blendRatio)
                        elif mat.xplane.blend_v1000 == 'on':
                            self.attributes['ATTR_blend'].setValue(True)
                        elif mat.xplane.blend_v1000 == 'shadow':
                            self.attributes['ATTR_shadow_blend'].setValue(True)
                    else:
                        if mat.xplane.blend:
                            self.attributes['ATTR_no_blend'].setValue(mat.xplane.blendRatio)
                        else:
                            self.attributes['ATTR_blend'].setValue(True)
            else:
                self.attributes['ATTR_draw_disable'].setValue(True)

            # depth check
            if self.blenderObject.xplane.depth == False:
                self.attributes['ATTR_no_depth'].setValue(True);
            else:
                self.attributes['ATTR_depth'].setValue(True)

            # surface type
            if mat.xplane.surfaceType != 'none':
                if mat.xplane.deck:
                    self.attributes['ATTR_hard_deck'].setValue(mat.xplane.surfaceType)
                else:
                    self.attributes['ATTR_hard'].setValue(mat.xplane.surfaceType)
            else:
                self.attributes['ATTR_no_hard'].setValue(True)

            # backface culling
            if self.blenderObject.data.show_double_sided:
                self.attributes['ATTR_no_cull'].setValue(True)
            else:
                self.attributes['ATTR_cull'].setValue(True)

            # camera collision
            if mat.xplane.solid_camera:
                self.attributes['ATTR_solid_camera'].setValue(True)
            else:
                self.attributes['ATTR_no_solid_camera'].setValue(True)

            # try to find uv layer
            if(len(self.blenderObject.data.uv_textures) > 0):
                self.uv_name = self.blenderObject.data.uv_textures.active.name

            # add custom attributes
            self.collectCustomAttributes(mat)

        else:
            showError('%s: No Material found.' % self.blenderObject.name)

        self.attributes.order()

    def collectCustomAttributes(self, mat):
        xplaneFile = self.xplaneObject.xplaneBone.xplaneFile
        commands =  xplaneFile.commands

        if mat.xplane.customAttributes:
            for attr in mat.xplane.customAttributes:
                if attr.reset:
                    commands.reseters[attr.name] = attr.reset
                self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))


    def collectCockpitAttributes(self, mat):
        if mat.xplane.panel:
            self.cockpitAttributes['ATTR_cockpit'].setValue(True)
            self.cockpitAttributes['ATTR_no_cockpit'].setValue(None)
            cockpit_region = int(mat.xplane.cockpit_region)
            if cockpit_region>0:
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
            # do not write own reseters just now
            if commands.attributeIsReseter(attr, self.xplaneObject.reseters) == False:
                o += xplaneFile.commands.writeAttribute(self.attributes[attr], self.xplaneObject)

        if hasattr(xplaneFile.options, 'cockpit') and xplaneFile.options.cockpit:
            for attr in self.material.cockpitAttributes:
                # do not write own reseters just now
                if self.attributeIsReseter(attr, self.xplaneObject.reseters) == False:
                  o += self.writeAttribute(self.xplaneObject.material.cockpitAttributes[attr], self.xplaneObject)

        return o
