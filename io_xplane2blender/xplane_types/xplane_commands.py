from ..xplane_config import getDebug, getDebugger

# Class: XPlaneCommands
# Creates the OBJ commands table.
class XPlaneCommands():
    # Property: reseters
    # dict - Stores attribtues that reset other attributes.
    reseters = {}

    # Property: written
    # dict - Stores all already written attributes and theire values.
    written = {}

    # Property: staticWritten
    # list - Stores names of objects whos static translations/rotations have already been written.
    staticWritten = []

    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self, xplaneFile):
        self.xplaneFile = xplaneFile

        self.reseters = {
            'ATTR_light_level':'ATTR_light_level_reset',
            'ATTR_cockpit':'ATTR_no_cockpit',
#            'ATTR_cockpit_region':'ATTR_no_cockpit',
            'ATTR_manip_drag_xy':'ATTR_manip_none',
            'ATTR_manip_drag_axis':'ATTR_manip_none',
            'ATTR_manip_command':'ATTR_manip_none',
            'ATTR_manip_command_axis':'ATTR_manip_none',
            'ATTR_manip_push':'ATTR_manip_none',
            'ATTR_manip_radio':'ATTR_manip_none',
            'ATTR_manip_toggle':'ATTR_manip_none',
            'ATTR_manip_delta':'ATTR_manip_none',
            'ATTR_manip_wrap':'ATTR_manip_none',
            'ATTR_draw_disable':'ATTR_draw_enable',
            'ATTR_poly_os':'ATTR_poly_os 0',
            'ATTR_no_cull':'ATTR_cull',
            'ATTR_hard':'ATTR_no_hard',
            'ATTR_hard_deck':'ATTR_no_hard',
            'ATTR_no_depth':'ATTR_depth',
            'ATTR_no_blend':'ATTR_blend'
        }
        self.written = {}
        self.staticWritten = []

    # Method: write
    # Returns the OBJ commands table.
    #
    # Params:
    #   int lod - (default -1) Level of detail randing from 0..2, if -1 no level of detail will be used
    #
    # Returns:
    #   string - The OBJ commands table.
    def write(self, lod = -1):
        o = ''
        o += self.writeXPlaneBone(self.xplaneFile.rootBone, lod)

        # write down all lights
        # TODO: write them in writeObjects instead to allow light animation and nesting
#        if len(self.file['lights'])>0:
#            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])

        return o

    def writeXPlaneBone(self, xplaneBone, lod):
        o = ''
        o += xplaneBone.writeAnimationPrefix()
        xplaneObject = xplaneBone.xplaneObject

        if xplaneObject:
            if lod == -1:
                # only write objects that are in no lod
                if xplaneObject.lod[0] == False and xplaneObject.lod[1] == False and xplaneObject.lod[2] == False:
                    o += xplaneObject.write()

            # write objects that are within that lod and in no lod, as those should appear everywhere
            elif xplaneObject.lod[lod] == True or (xplaneObject.lod[0] == False and xplaneObject.lod[1] == False and xplaneObject.lod[2] == False):
                o += xplaneObject.write()

        # write bone children
        for childBone in xplaneBone.children:
            o += self.writeXPlaneBone(childBone, lod)

        o += xplaneBone.writeAnimationSuffix()

        return o

    # Method: writeObject
    # Returns the commands for one <XPlaneObject>.
    #
    # Parameters:
    #   XPlaneObject xplaneObject - A <XPlaneObject>.
    #   int animLevel - Level of animation.
    #   int lod - (default -1) Level of detail randing from 0..2, if -1 no level of detail will be used
    #
    # Returns:
    #   string - OBJ Commands for the "obj".
    '''
    def writeXPlaneObject(self, xplaneObject, lod = -1):
        debug = getDebug()
        debugger = getDebugger()

        o = ''
        return o

        animationStarted = False
        tabs = self.getAnimTabs(animLevel)

        if debug:
            o+="%s# %s: %s\tweight: %d\n" % (tabs,obj.type,obj.name,obj.weight)

        # only write objects that are in current layer/file
        if self.objectInFile(obj):
            # open conditions
            if hasattr(obj, 'material') and self.canExportMesh(obj):
                o += self.writeConditions(obj.material, tabs)

            o += self.writeConditions(obj, tabs)

            if obj.animated() or obj.hasAnimAttributes():
                animationStarted = True

                # begin animation block
                oAnim = ''
                animLevel+=1
                tabs = self.getAnimTabs(animLevel)

                if obj.animated():
                    for dataref in obj.animations:
                        if len(obj.animations[dataref])>1:
                            oAnim+=self.writeKeyframes(obj,dataref,tabs)
                if obj.hasAnimAttributes():
                    oAnim+=self.writeAnimAttributes(obj,tabs)

                if oAnim!='':
                    o+="%sANIM_begin\n" % self.getAnimTabs(animLevel-1)
                    o+=oAnim


#            if debug:
#                debugger.debug('\nWriting attributes for %s' % obj.name)

            o+=self.writeReseters(obj,tabs)

            if hasattr(obj,'attributes'):
                o+=self.writeCustomAttributes(obj,tabs)

            if hasattr(obj,'material') and self.canExportMesh(obj):
                o+=self.writeMaterial(obj,tabs)

            # write cockpit attributes
            if self.file['parent'].cockpit and hasattr(obj,'cockpitAttributes') and self.canExportMesh(obj):
                o+=self.writeCockpitAttributes(obj,tabs)

            # rendering (do not render meshes/objects with no indices)
            if hasattr(obj,'indices') and obj.indices[1]>obj.indices[0] and self.canExportMesh(obj):
                offset = obj.indices[0]
                count = obj.indices[1]-obj.indices[0]

                if obj.type == 'PRIMITIVE':
                    o+="%sTRIS\t%d %d\n" % (tabs,offset,count)
                elif obj.type == 'LIGHT':
                    if obj.lightType not in ('named','param','custom'):
                        o+="%sLIGHTS\t%d %d\n" % (tabs,offset,count)

            if obj.type == 'LIGHT' and obj.lightType in ('named','param','custom'):
                o+=self.writeLight(obj,animLevel)

            # close conditions
            if hasattr(obj, 'material') and self.canExportMesh(obj):
                o += self.writeConditions(obj.material, tabs, True)

            o += self.writeConditions(obj, tabs, True)

        if animationStarted:
            for child in obj.children:
                o+=self.writeObject(child,animLevel)
            # TODO: check if Object has an animated parent in another file, if so add a dummy anim-block around it?

            # end animation block
            if oAnim!='':
                o+="%sANIM_end\n" % self.getAnimTabs(animLevel-1)
        else:
            for child in obj.children:
                if lod == -1:
                    if child.lod[0] == False and child.lod[1] == False and child.lod[2] == False: # only write objects that are in no lod
                        o+=self.writeObject(child,animLevel+1, lod)
                elif child.lod[lod] == True or (child.lod[0] == False and child.lod[1] == False and child.lod[2] == False): # write objects that are within that lod and in no lod, as those should appear everywhere
                    o+=self.writeObject(child,animLevel+1, lod)

        if profile:
            profiler.end("XPlaneCommands.writeObject")

        return o
        '''

    def writeLight(self, light, animLevel):
        tabs = self.getAnimTabs(animLevel)

        bakeMatrix = getBakeMatrix(light)

        coords = XPlaneCoords.fromMatrix(bakeMatrix)
        co = coords['location']

        o = ''

        if light.lightType=="named":
            o+="%sLIGHT_NAMED\t%s\t%6.8f\t%6.8f\t%6.8f\n" % (tabs, light.lightName, co[0], co[1], co[2])
        elif light.lightType=="param":
            o+="%sLIGHT_PARAM\t%s\t%6.8f\t%6.8f\t%6.8f\t%s\n" % (tabs, light.lightName, co[0], co[1], co[2], light.params)
        elif light.lightType=="custom":
            o+="%sLIGHT_CUSTOM\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%s\n" % (tabs, co[0], co[1], co[2], light.color[0], light.color[1], light.color[2], light.energy, light.size, light.uv[0], light.uv[1], light.uv[2], light.uv[3], light.dataref)

        return o

    def canExportMesh(self, obj):
        return hasattr(obj, 'export_mesh') and obj.export_mesh[self.file['parent'].index] == True

    def objectInFile(self,obj):
        layer = self.file['parent'].index
        if obj.type=='BONE':
            obj = obj.armature
        for i in range(len(obj.object.layers)):
            if obj.object.layers[i]==True and i == layer:
                return True
        return False

    # Method: getAnimTabs
    # Returns the tabs used to indent the commands for better readibility in the OBJ file.
    #
    # Parameters:
    #   int level - Level of animation.
    #
    # Returns:
    #   string - The tabs.
    def getAnimTabs(self,level):
        tabs = ''
        for i in range(0,level):
            tabs+='\t'

        return tabs

    # Method: getAnimLevel
    # Returns the animation level of an <XPlaneObject>. This is basically the nesting level of an object.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>.
    #
    # Returns:
    #   int - the animation level.
    def getAnimLevel(self,obj):
        parent = obj
        level = 0

        while parent != None:
            parent = parent.parent
            if (parent!=None):
                level+=1

        return level

    # Method: writeAttribute
    # Returns the Command line for an attribute.
    # Uses <canWrite> to determine if the command needs to be written.
    #
    # Parameters:
    #   string attr - The attribute name.
    #   string value - The attribute value.
    #   XPlaneObject object - A <XPlaneObject>.
    #
    # Returns:
    #   string or None if the command must not be written.
    def writeAttribute(self,attr,value,object):
#        debug = getDebug()
#        debugger = getDebugger()

        if value!=None:
            if value==True:
                o = '%s\n' % attr
            else:
                value = self.parseAttributeValue(value,object)
                o = '%s\t%s\n' % (attr,value)

            if self.canWrite(attr,value):
#                if debug and draw:
#                    debugger.debug('writing Attribute %s = %s' % (attr,str(value)))
                self.written[attr] = value

                # check if this thing has a reseter and remove counterpart if any
                if attr in self.reseters and self.reseters[attr] in self.written:
#                    if debug and draw:
#                        debugger.debug('removing reseter counterpart %s' % self.reseters[attr])
                    del self.written[self.reseters[attr]]

                # check if a reseter counterpart has been written and if so delete its reseter
                for reseter in self.reseters:
                    if self.reseters[reseter] == attr and reseter in self.written:
#                        if debug and draw:
#                            debugger.debug('removing reseter %s' % reseter)
                        del self.written[reseter]
                return o
            else:
#                if debug and draw:
#                    debugger.debug("can't write Attribute %s = %s" % (attr,str(value)))
                return None
        else:
#            if debug and draw:
#                debugger.debug('empty Attribute %s = %s' % (attr,str(value)))
            return None

    # Method: parseAttributeValue
    # Returns a string with the parsed attribute value (replacing insert tags)
    #
    # Parameters:
    #   string value - The attribute value.
    #   XPlaneObject object - A <XPlaneObject>.
    #
    # Returns:
    #   string - The value with replaced insert tags.
    def parseAttributeValue(self,value,object):
        if str(value).find('{{xyz}}')!=-1:
            return str(value).replace('{{xyz}}','%6.8f\t%6.8f\t%6.8f' % (object.locationLocal[0],object.locationLocal[1],object.locationLocal[2]))
        else:
            return value


    # Method: canWrite
    # Determines if an attribute must be written.
    #
    # Parameters:
    #   string attr - The attribute name.
    #   string value - The attribute value.
    #
    # Returns:
    #   bool - True if the attribute must be written, else false.
    def canWrite(self,attr,value):
        if attr not in self.written:
            return True
        elif self.written[attr]==value:
            return False
        else:
            return True

    # Method: attributeIsReseter
    # Determines if a given attribute is a resetter.
    #
    # Parameters:
    #  string attr - The attribute name
    #  dict reseters - optional (default = self.reseters) a dict of reseters
    #
    # Returns:
    #  bool - True if attribute is a reseter, else False
    def attributeIsReseter(self,attr,reseters = None):
      if reseters == None: reseters = self.reseters

      for reseter_attr in reseters:
        if attr == reseters[reseter_attr]: return True

      return False

    # Method: writeCustomAttributes
    # Returns the commands for custom attributes of a <XPlaneObject>.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeCustomAttributes(self,obj,tabs):
        o = ''
        for attr in obj.attributes:
            line = self.writeAttribute(attr,obj.attributes[attr].getValue(),obj)

            # add reseter to own reseters list
            if attr in obj.reseters and obj.reseters[attr]!='':
                self.reseters[attr] = obj.reseters[attr]

            if line!=None:
                o+=tabs+line
        return o

    # Method: writeCockpitAttributes
    # Returns the commands for a <XPlaneObject> cockpit related attributes (e.g. Manipulators).
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeCockpitAttributes(self,obj,tabs):
        o = ''
        for attr in obj.cockpitAttributes:
            line = self.writeAttribute(attr,obj.cockpitAttributes[attr].getValue(),obj)
            if line:
                o+=tabs+line
        return o

    # Method: writeReseters
    # Returns the commands for a <XPlaneObject> needed to reset previous commands.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeReseters(self,obj,tabs):
        debug = getDebug()
        debugger = getDebugger()
        o = ''

        # create a temporary attributes dict
        attributes = XPlaneAttributes()
        # add custom attributes
        for attr in obj.attributes:
            if obj.attributes[attr]:
                attributes.add(obj.attributes[attr])
        # add material attributes if any
        if hasattr(obj,'material'):
            for attr in obj.material.attributes:
                if obj.material.attributes[attr]:
                    attributes.add(obj.material.attributes[attr])
        # add cockpit attributes
        for attr in obj.cockpitAttributes:
            if obj.cockpitAttributes[attr]:
                attributes.add(obj.cockpitAttributes[attr])

        for attr in self.reseters:
            # only reset attributes that wont be written with this object again
            if attr not in attributes and attr in self.written:
#                if debug:
#                    debugger.debug('writing Reseter for %s: %s' % (attr,self.reseters[attr]))

                # write reseter and add it to written
                o+=tabs+self.reseters[attr]+"\n"
                self.written[self.reseters[attr]] = True

                # we've reset an attribute so remove it from written as it will need rewrite with next object
                del self.written[attr]
        return o

    # Method: writeAnimAttributes
    # Returns the commands for animation attributes of a <XPlaneObject>.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeAnimAttributes(self,obj,tabs):
        o = ''
        for attr in obj.animAttributes:
            for value in obj.animAttributes[attr].getValues():
                line = "%s\t%s\n" % (attr,value)
                o+=tabs+line
        return o

    # Method: writeMaterial
    # Returns the commands for a <XPlaneObject> material.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>.
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeMaterial(self,obj,tabs):
        debug = getDebug()
        o = ''
        if debug:
            o+='%s# MATERIAL: %s\n' % (tabs,obj.material.name)
        for attr in obj.material.attributes:
            # do not write own reseters just now
            if self.attributeIsReseter(attr,obj.reseters) == False:
              line = self.writeAttribute(attr,obj.material.attributes[attr].getValue(),obj)
              if line:
                  o+=tabs+line

        if self.file['parent'].cockpit:
            for attr in obj.material.cockpitAttributes:
                #do not write own reseters just now
                if self.attributeIsReseter(attr,obj.reseters) == False:
                  line = self.writeAttribute(attr,obj.material.cockpitAttributes[attr].getValue(),obj)
                  if line:
                      o+=tabs+line

        return o

    # Method: writeKeyframes
    # Returns the commands for a <XPlaneObject> keyframes.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #   string dataref - Name of the dataref that is driving this animation.
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeKeyframes(self, obj, dataref, tabs):
        debug = getDebug()
        debugger = getDebugger()

        o = ''

        keyframes = obj.animations[dataref]

        totalTrans = [0.0, 0.0, 0.0]
        totalRot = [0.0, 0.0, 0.0]

        # now get static Transformations based up on hierarchy and animations in parents
        # rotations are always applied at origin, even if a static translation happend before
        # TODO: static transformations can be merged into keyframe transformations
        static = {'trans': ['', ''], 'rot': ['', '', '']}
        staticRot = [0.0, 0.0, 0.0]
        staticTrans = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]

        animatedParent = obj.firstAnimatedParent()

        # root level
        if obj.parent == None:
            world = obj.getWorld()
            # move object to world location
            staticTrans[0] = world['location']
            if debug:
                debugger.debug('%s root level' % obj.name)

        # not root level and no animated parent
        elif animatedParent == None:
            # move object to world location
            # rotation of parent is already baked
            world = obj.getWorld()
            local = obj.parent.getLocal()
            staticTrans[0] = world['location']
            if debug:
                debugger.debug('%s not root level and no animated parent' % obj.name)

        # not root level and we have an animated parent somewhere in the hierarchy
        elif animatedParent:
            # move object to the location relative to animated Parent
            relative = obj.getRelative(animatedParent)
            staticTrans[0] = relative['location']
            if debug:
                debugger.debug('%s not root level and animated parent' % obj.name)
            # direct parent is animated so rotate statically to parents bake matrix rotation
            if animatedParent == obj.parent:
                bake = XPlaneCoords.fromMatrix(obj.parent.bakeMatrix)
                staticRot = bake['angle']


        # ignore high precision values
        for i in range(0,2):
            if round(staticTrans[i][0], 4) != 0.0 or round(staticTrans[i][1], 4) != 0.0 or round(staticTrans[i][2], 4) != 0.0:
                static['trans'][i] = "%sANIM_trans\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t0\t0\tnone\n" % (tabs, staticTrans[i][0], staticTrans[i][1], staticTrans[i][2], staticTrans[i][0], staticTrans[i][1], staticTrans[i][2])

        vectors = obj.getVectors()
        for i in range(0, 3):
            if (round(staticRot[i], 4) != 0.0):
                vec = vectors[i]
                static['rot'][i] = "%sANIM_rotate\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t%6.8f\t0\t0\tnone\n" % (tabs, vec[0], vec[1], vec[2], staticRot[i], staticRot[i])

        # add loops if any
        if obj.datarefs[dataref].loop > 0:
            loops = "%s\tANIM_keyframe_loop\t%6.8f\n" % (tabs, obj.datarefs[dataref].loop)
        else:
            loops = ''

        trans = "%sANIM_trans_begin\t%s\n" % (tabs, dataref)

#        print(obj.vectors)
        rot = ['', '', '']
        rot[0] = "%sANIM_rotate_begin\t%6.8f\t%6.8f\t%6.8f\t%s\n" % (tabs, obj.vectors[0][0], obj.vectors[0][1], obj.vectors[0][2], dataref)
        rot[1] = "%sANIM_rotate_begin\t%6.8f\t%6.8f\t%6.8f\t%s\n" % (tabs, obj.vectors[1][0], obj.vectors[1][1], obj.vectors[1][2], dataref)
        rot[2] = "%sANIM_rotate_begin\t%6.8f\t%6.8f\t%6.8f\t%s\n" % (tabs, obj.vectors[2][0], obj.vectors[2][1], obj.vectors[2][2], dataref)

        for keyframe in keyframes:
            totalTrans[0] += abs(keyframe.translation[0])
            totalTrans[1] += abs(keyframe.translation[1])
            totalTrans[2] += abs(keyframe.translation[2])
            trans += "%s\tANIM_trans_key\t%6.8f\t%6.8f\t%6.8f\t%6.8f\n" % (tabs, keyframe.value, keyframe.translation[0], keyframe.translation[1], keyframe.translation[2])

            totalRot[0] += abs(keyframe.rotation[0])
            totalRot[1] += abs(keyframe.rotation[1])
            totalRot[2] += abs(keyframe.rotation[2])

            for i in range(0,3):  #modified by EagleIan
                if keyframe.index > 0:
                    prevRot = keyframes[keyframe.index - 1].rotation[i]
                    if (keyframe.rotation[i] - prevRot) > 180:
                        correctedRot = (360 - keyframe.rotation[i])*-1
                        keyframes[keyframe.index].rotation[i] = correctedRot
                rot[i] += "%s\tANIM_rotate_key\t%6.8f\t%6.8f\n" % (tabs, keyframe.value, keyframe.rotation[i])

            if debug:
                debugger.debug("%s keyframe %s@%d %s" % (keyframe.object.name, keyframe.index, keyframe.frame, keyframe.dataref))

        trans += loops
        trans += "%sANIM_trans_end\n" % tabs
        rot[0] += loops
        rot[0] += "%sANIM_rotate_end\n" % tabs
        rot[1] += loops
        rot[1] += "%sANIM_rotate_end\n" % tabs
        rot[2] += loops
        rot[2] += "%sANIM_rotate_end\n" % tabs

        # ignore high precision changes that won't be written anyway
        totalTrans[0] = round(totalTrans[0], FLOAT_PRECISION)
        totalTrans[1] = round(totalTrans[1], FLOAT_PRECISION)
        totalTrans[2] = round(totalTrans[2], FLOAT_PRECISION)

        if obj.id not in self.staticWritten:
            o += static['trans'][0]
            # o += static['rot'][0]
            o += static['rot'][1]
            o += static['rot'][2]
            o += static['rot'][0] # x-axis comes last due to coordinate conversion
            self.staticWritten.append(obj.id)

        # ignore translation if dataref has 'rotate' anim_type
        if obj.datarefs[dataref].anim_type in ('transform', 'translate'):
            if totalTrans[0] != 0.0 or totalTrans[1] != 0.0 or totalTrans[2] != 0.0:
                o += trans

        # ignore high precision changes that won't be written anyway
        totalRot[0] = round(totalRot[0],FLOAT_PRECISION)
        totalRot[1] = round(totalRot[1],FLOAT_PRECISION)
        totalRot[2] = round(totalRot[2],FLOAT_PRECISION)

        # ignore rotation if dataref has 'translate' anim_type
        if obj.datarefs[dataref].anim_type in ('transform', 'rotate'):
            # if totalRot[0] != 0.0:
            #    o += rot[0]
            if totalRot[1] != 0.0:
                o += rot[1]
            if totalRot[2] != 0.0:
                o += rot[2]
            # x-axis comes last due to coordinate conversion
            if totalRot[0] != 0.0:
                o += rot[0]

        o += static['trans'][1]
        return o

    def writeConditions(self, obj, tabs, close=False):
        o = ''
        for condition in obj.conditions:
            if close == True:
                o += tabs + 'ENDIF\n'
            else:
                if condition.value == True:
                    o += tabs + 'IF %s\n' % condition.variable
                else:
                    o += tabs + 'IF NOT %s\n' % condition.variable

        return o
