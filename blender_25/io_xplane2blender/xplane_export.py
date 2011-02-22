import os.path
import bpy
import os
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_types import *
from io_xplane2blender.xplane_config import *
from io_utils import ImportHelper, ExportHelper

class XPlaneMesh():
    def __init__(self,file):
        self.vertices = []
        self.indices = []

        # store the global index, as we are reindexing faces
        self.globalindex = 0
        self.writeObjects(file['objects'])

    def getBakeMatrix(self,obj):
        # Bake in different matrixes depending on animation and hierarchy
        animatedParent = obj.firstAnimatedParent()
        if obj.animated():
            if obj.parent == None:
                # root level
                # Conversion matrix only. Object will be transformed during animation.
                matrix = XPlaneCoords.conversionMatrix()
            else:
                # not at root level
                if animatedParent:
                    # has some animated parent
                    # bake rotation of the parent relative to the animated parent so we do not need to worry about it later
                    matrix = XPlaneCoords.relativeConvertedMatrix(obj.parent.getMatrix(True),animatedParent.getMatrix(True))
                    matrix = XPlaneCoords.convertMatrix(matrix.to_euler().to_matrix().to_4x4())
                else:
                    # no animated parent
                    # bake rotation of the parent so we do not need to worry about it later
                    matrix = XPlaneCoords.convertMatrix(obj.parent.getMatrix(True).to_euler().to_matrix().to_4x4())
        else:
            if animatedParent:
                # object has some animated parent, so we need to bake the matrix relative to animated parent
                matrix = XPlaneCoords.relativeConvertedMatrix(obj.getMatrix(True),animatedParent.getMatrix(True))
            else:
                # no animated objects up in hierarchy, so this will become a static mesh on root level
                # we can savely bake the world matrix as no transforms will occur
                matrix = XPlaneCoords.convertMatrix(obj.getMatrix(True))
                
        return matrix

    def writeObjects(self,objects):
        for obj in objects:
            if obj.type == 'PRIMITIVE':
                obj.indices[0] = len(self.indices)

                # create a copy of the object mesh with modifiers applied
                mesh = obj.object.create_mesh(bpy.context.scene, True, "PREVIEW")

                # now get the bake matrix
                # and bake it to the mesh
                obj.bakeMatrix = self.getBakeMatrix(obj)
                mesh.transform(obj.bakeMatrix)

                # with the new mesh get uvFaces list
                uvFaces = self.getUVFaces(mesh,obj.material.uv_name)

    #            faces = XPlaneFaces()

                # convert faces to triangles
                tempfaces = []
                for i in range(0,len(mesh.faces)):
                    if uvFaces != None:
                        tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],uvFaces[i]))
                    else:
                        tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],None))

                for f in tempfaces:
    #                xplaneFace = XPlaneFace()
                    l = len(f['indices'])
                    for i in range(0,len(f['indices'])):
                        # get the original index but reverse order, as this is reversing normals
                        vindex = f['indices'][2-i]

                        # get the vertice from original mesh
                        v = mesh.vertices[vindex]
                        co = v.co

                        vert = [co[0],co[1],co[2],v.normal[0],v.normal[1],v.normal[2],f['uv'][i][0],f['uv'][i][1]]

                        index = self.globalindex
                        self.vertices.append(vert)
                        self.globalindex+=1

                        # store face information alltogether in one struct
    #                    xplaneFace.vertices[i] = (vert[0],vert[1],vert[2])
    #                    xplaneFace.normals[i] = (vert[3],vert[4],vert[5])
    #                    xplaneFace.uvs[i] = (vert[6],vert[7])
    #                    xplaneFace.indices[i] = index

                        self.indices.append(index)

    #                faces.append(xplaneFace)

                # store the faces in the prim
    #            prim.faces = faces
                obj.indices[1] = len(self.indices)

            self.writeObjects(obj.children)

            #TODO: now optimize vertex-table and remove duplicates
            #index = self.getDupliVerticeIndex(vert,endIndex)
        
            
    def getDupliVerticeIndex(self,v,startIndex = 0):
        if profile:
            profiler.start('XPlaneMesh.getDupliVerticeIndex')
            
        for i in range(len(self.vertices)):
            match = True
            ii = startIndex
            while ii<len(self.vertices[i]):
                if self.vertices[i][ii] != v[ii]:
                    match = False
                    ii = len(self.vertices[i])
                ii+=1
                
            if match:
                return i

        if profile:
            profiler.end('XPlaneMesh.getDupliVerticeIndex')

        return -1

    def getUVFaces(self,mesh,uv_name):
        # get the uv_texture
        if (uv_name != None and len(mesh.uv_textures)>0):
            uv_layer = None
            if uv_name=="":
                uv_layer = mesh.uv_textures[0]
            else:
                i = 0
                while uv_layer == None and i<len(mesh.uv_textures):
                    if mesh.uv_textures[i].name == uv_name:
                        uv_layer = mesh.uv_textures[i]
                    i+=1

            if uv_layer!=None:
                return uv_layer.data
            else:
                return None
        else:
            return None

    def faceToTrianglesWithUV(self,face,uv):
        if profile:
            profiler.start('XPlaneMesh.faceToTrianglesWithUV')

        triangles = []
        #inverse uv's as we are inversing face indices later
        if len(face.vertices)==4: #quad
            if uv != None:
                triangles.append( {"uv":[[uv.uv3[0], uv.uv3[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv1[0], uv.uv1[1]]], "indices":[face.vertices[0], face.vertices[1], face.vertices[2]]})
                triangles.append( {"uv":[[uv.uv1[0], uv.uv1[1]], [uv.uv4[0], uv.uv4[1]], [uv.uv3[0], uv.uv3[1]]], "indices":[face.vertices[2], face.vertices[3], face.vertices[0]]})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[face.vertices[0], face.vertices[1], face.vertices[2]]})
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[face.vertices[2], face.vertices[3], face.vertices[0]]})
        else:
            if uv != None:
                triangles.append( {"uv":[[uv.uv3[0], uv.uv3[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv1[0], uv.uv1[1]]], "indices":face.vertices})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":face.vertices})

        if profile:
            profiler.end('XPlaneMesh.faceToTrianglesWithUV')

        return triangles

    def faceValues(self,face, mesh, matrix):
        fv = []
        for verti in face.vertices_raw:
            fv.append(matrix * mesh.vertices[verti].co)
        return fv

    def writeVertices(self):
        if profile:
            profiler.start('XPlaneMesh.writeVertices')

        o=''
        for v in self.vertices:
            # dump the vertex data
            o+="VT"
            for i in v:
                o+="\t%6.4f" % i
            o+="\n"

        if profile:
            profiler.end('XPlaneMesh.writeVertices')

        return o

    def writeIndices(self):
        if profile:
            profiler.start('XPlaneMesh.writeIndices')

        o=''
        group = []
        for i in self.indices:
            # append index to group if we havent collected 10 yet
            if len(group)<10:
                group.append(i)
            else:
                # dump 10 indices at once
                o+='IDX10'
                for ii in group:
                    o+="\t%d" % ii

                o+="\n"
                group = []
                group.append(i)
        
        # dump overhanging indices
        for i in group:
            o+="IDX\t%d\n" % i

        if profile:
            profiler.end('XPlaneMesh.writeIndices')

        return o


class XPlaneLights():
    def __init__(self,file):
        self.lights = []
        self.indices = []

        # store the global index, as we are reindexing faces
        globalindex = 0

        for light in file['lights']:
            light.indices[0] = globalindex

            # get the location

            matrix = XPlaneCoords.convertMatrix(light.getMatrix(True))
            coords = XPlaneCoords.fromMatrix(matrix)
            co = coords['location']

            if light.lightType=="named":
                self.lights.append("LIGHT_NAMED\t%s\t%6.4f\t%6.4f\t%6.4f" % (light.lightName,co[0],co[1],co[2]))
            elif light.lightType=="param":
                self.lights.append("LIGHT_PARAM\t%s\t%6.4f\t%6.4f\t%6.4f\t%s" % (light.lightName,co[0],co[1],co[2],light.params))
            elif light.lightType=="custom":
                self.lights.append("LIGHT_CUSTOM\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0.0\t0.0\t1.0\t1.0\t%s" % (co[0],co[1],co[2],light.color[0],light.color[1],light.color[2],light.energy,light.dataref))
            else:
                self.lights.append("VLIGHT\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f" % (co[0],co[1],co[2],light.color[0],light.color[1],light.color[2]))
            self.indices.append(globalindex)
            globalindex+=1

            light.indices[1] = globalindex

    def writeLights(self):
        o=''
        for l in self.lights:
            o+=l+'\n'
        return o


class XPlaneCommands():
    def __init__(self,file):
        self.file = file
        
        # stores attribtues that reset other attributes
        self.reseters = {}

        # stores all already written attributes
        self.written = {}

    def write(self):
        o=''
         
        # write down all objects
        for obj in self.file['objects']:
            o+=self.writeObject(obj,0)

        # write down all lights
        # TODO: write them in writeObjects instead to allow light animation and nesting
        if len(self.file['lights'])>0:
            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])
            
        return o
        
    def writeObject(self,obj,animLevel):
        if profile:
            profiler.start("XPlaneCommands.writeObject")
            
        o = ''
        
        animationStarted = False
        tabs = self.getAnimTabs(animLevel)

        if debug:
            o+="%s# %s\n" % (tabs,obj.name)

        if obj.animated():
            animationStarted = True

            # begin animation block
            oAnim = ''
            animLevel+=1
            tabs = self.getAnimTabs(animLevel)
            
            for dataref in obj.animations:
                if len(obj.animations[dataref])>1:
                    oAnim+=self.writeKeyframes(obj,dataref,tabs)
            
            if oAnim!='':
                o+="%sANIM_begin\n" % self.getAnimTabs(animLevel-1)
                o+=oAnim

        if hasattr(obj,'material'):
            o+=self.writeMaterial(obj,tabs)

        if hasattr(obj,'attributes'):
            o+=self.writeCustomAttributes(obj,tabs)

        # write cockpit attributes
        if self.file['parent'].cockpit and hasattr(obj,'cockpitAttributes'):
            o+=self.writeCockpitAttributes(obj,tabs)

        # triangle rendering
        if hasattr(obj,'indices'):
            offset = obj.indices[0]
            count = obj.indices[1]-obj.indices[0]
            o+="%sTRIS\t%d %d\n" % (tabs,offset,count)

        if animationStarted:
            for child in obj.children:
                o+=self.writeObject(child,animLevel)
            # TODO: check if Object has an animated parent in another file, if so add a dummy anim-block around it?

            # end animation block
            if oAnim!='':
                o+="%sANIM_end\n" % self.getAnimTabs(animLevel-1)
        else:
            for child in obj.children:
                o+=self.writeObject(child,animLevel+1)

        if profile:
            profiler.end("XPlaneCommands.writeObject")
            
        return o

    def getAnimTabs(self,level):
        tabs = ''
        for i in range(0,level):
            tabs+='\t'
        
        return tabs

    def getAnimLevel(self,obj):
        parent = obj
        level = 0
        
        while parent != None:
            parent = parent.parent
            if (parent!=None):
                level+=1
        
        return level

    def writeAttribute(self,attr,value):
        if value!=None:
            if value==True:
                return '%s\n' % attr
            else:
                return '%s\t%s\n' % (attr,value)
        else:
            return None

    def writeMaterial(self,prim,tabs):
        o = ''
        for attr in prim.material.attributes:
            line = self.writeAttribute(attr,prim.material.attributes[attr])
            if line:
                o+=tabs+line
                # only write line if attribtue wasn't already written with same value
#                    if attr in self.written:
#                        if self.written[attr]!=value:
#                            o+=line
#                            self.written[attr] = value
#                    else:
#                        o+=line
#                        self.written[attr] = value
        return o

    def writeCustomAttributes(self,obj,tabs):
        o = ''
        for attr in obj.attributes:
            line = self.writeAttribute(attr,obj.attributes[attr])
            if line!=None:
                o+=tabs+line
        return o

    def writeCockpitAttributes(self,obj,tabs):
        o = ''
        for attr in obj.cockpitAttributes:
            line = self.writeAttribute(attr,obj.cockpitAttributes[attr])
            if line:
                o+=tabs+line
        return o

    def writeKeyframes(self,obj,dataref,tabs):
        o = ''

        keyframes = obj.animations[dataref]

        totalTrans = [0.0,0.0,0.0]
        totalRot = [0.0,0.0,0.0]

        # now get static Transformations based up on hierarchy and animations in parents
        # rotations are always applied at origin, even if a static translation happend before
        # TODO: static transformations can be merged into keyframe transformations
        static = {'trans':['',''],'rot':['','','']}
        staticRot = [0.0,0.0,0.0]
        staticTrans = [[0.0,0.0,0.0],[0.0,0.0,0.0]]

        animatedParent = obj.firstAnimatedParent()
        
        # root level
        if obj.parent == None:
            world = obj.getWorld()
            # move object to world location
            staticTrans[0] = world['location']

        # not root level and no animated parent
        elif animatedParent == None:
            # move object to world location
            # rotation of parent is already baked
            world = obj.getWorld()
            local = obj.parent.getLocal()
            staticTrans[0] = world['location']
                
        # not root level and we have an animated parent somewhere in the hierarchy
        elif animatedParent:
            # move object to the location relative to animated Parent
            relative = obj.getRelative(animatedParent)
            staticTrans[0] = relative['location']
            
        # ignore high precision values
        for i in range(0,2):    
            if round(staticTrans[i][0],4)!=0.0 or round(staticTrans[i][1],4)!=0.0 or round(staticTrans[i][2],4)!=0.0:
                static['trans'][i] = "%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,staticTrans[i][0],staticTrans[i][1],staticTrans[i][2],staticTrans[i][0],staticTrans[i][1],staticTrans[i][2])

        for i in range(0,3):
            if (round(staticRot[i],4)!=0.0):
                vec = [0.0,0.0,0.0]
                vec[i] = 1.0
                static['rot'][i] = "%sANIM_rotate\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,vec[0],vec[1],vec[2],staticRot[i],staticRot[i])
        
        trans = "%sANIM_trans_begin\t%s\n" % (tabs,dataref)

        print(obj.vectors)
        rot = ['','','']
        rot[0] = "%sANIM_rotate_begin\t%6.4f\t%6.4f\t%6.4f\t%s\n" % (tabs,obj.vectors[0][0],obj.vectors[0][1],obj.vectors[0][2],dataref)
        rot[1] = "%sANIM_rotate_begin\t%6.4f\t%6.4f\t%6.4f\t%s\n" % (tabs,obj.vectors[1][0],obj.vectors[1][1],obj.vectors[1][2],dataref)
        rot[2] = "%sANIM_rotate_begin\t%6.4f\t%6.4f\t%6.4f\t%s\n" % (tabs,obj.vectors[2][0],obj.vectors[2][1],obj.vectors[2][2],dataref)
        
        for keyframe in keyframes:
            totalTrans[0]+=abs(keyframe.translation[0])
            totalTrans[1]+=abs(keyframe.translation[1])
            totalTrans[2]+=abs(keyframe.translation[2])
            trans+="%s\tANIM_trans_key\t%6.4f\t%6.4f\t%6.4f\t%6.4f\n" % (tabs,keyframe.value,keyframe.translation[0],keyframe.translation[1],keyframe.translation[2])
            
            totalRot[0]+=abs(keyframe.rotation[0])
            totalRot[1]+=abs(keyframe.rotation[1])
            totalRot[2]+=abs(keyframe.rotation[2])
            
            for i in range(0,3):
                rot[i]+="%s\tANIM_rotate_key\t%6.4f\t%6.4f\n" % (tabs,keyframe.value,keyframe.rotation[i])

            if debug:
                debugger.debug("%s keyframe %d@%d" % (keyframe.object.name,keyframe.index,keyframe.frame))
            
        trans+="%sANIM_trans_end\n" % tabs
        rot[0]+="%sANIM_rotate_end\n" % tabs
        rot[1]+="%sANIM_rotate_end\n" % tabs
        rot[2]+="%sANIM_rotate_end\n" % tabs

        # ignore high precision changes that won't be written anyway
        totalTrans[0] = round(totalTrans[0],4)
        totalTrans[1] = round(totalTrans[1],4)
        totalTrans[2] = round(totalTrans[2],4)

        o+=static['trans'][0]
        o+=static['rot'][0]
        o+=static['rot'][1]
        o+=static['rot'][2]

        if totalTrans[0]!=0.0 or totalTrans[1]!=0.0 or totalTrans[2]!=0.0:
            o+=trans
        # add loops if any
        if obj.datarefs[dataref].loop>0:
            o+="%sANIM_keyframe_loop\t%d\n" % (tabs,obj.datarefs[dataref].loop)
                
        # ignore high precision changes that won't be written anyway
        totalRot[0] = round(totalRot[0],4)
        totalRot[1] = round(totalRot[1],4)
        totalRot[2] = round(totalRot[2],4)
        
        if totalRot[0]!=0.0:
            o+=rot[0]
        if totalRot[1]!=0.0:
            o+=rot[1]
        if totalRot[2]!=0.0:
            o+=rot[2]

        # add loops if any
        if obj.datarefs[dataref].loop>0:
            o+="%sANIM_keyframe_loop\t%d\n" % (tabs,obj.datarefs[dataref].loop)

        o+=static['trans'][1]
        return o


class XPlaneData():
    def __init__(self):
        self.files = {}

    # Returns the corresponding xplane-Layer to a blender layer index
    def getXPlaneLayer(self,layer):
        return bpy.context.scene.xplane.layers[layer]

    # Returns the filename for a layer. If no name was given by user it will be generated.
    def getFilenameFromXPlaneLayer(self,xplaneLayer):
        if xplaneLayer.name == "":
            filename = "layer_%s" % (str(xplaneLayer.index+1).zfill(2))
        else:
            filename = xplaneLayer.name

#        if xplaneLayer.cockpit:
#            filename +="_cockpit"

        return filename

    # Returns indices of all active blender layers
    def getActiveLayers(self):
        layers = []
        for i in range(0,len(bpy.context.scene.layers)):
            if bpy.context.scene.layers[i]:
                layers.append(i)

        return layers

    # Returns all first level Objects of a blender layer
    def getObjectsByLayer(self,layer):
        objects = []
        for object in bpy.context.scene.objects:
            #only add top level objects that have no parents
            if (object.parent==None):
                for i in range(len(object.layers)):
                    if object.layers[i]==True and i == layer:
                        objects.append(object)

        return objects

    # Returns an empty obj-file hash
    def getEmptyFile(self,parent):
        return {'objects':[],'lights':[],'lines':[],'primitives':[],'parent':parent}

    # Returns exportable child objects. If those are nested within bones or something else it will look recursive for objects.
    def getChildObjects(self,parent,found = None):
        if found==None:
            found = []
        if len(parent.children)>0:
            for child in parent.children:
                found.append(child)
#                if child.type in ["MESH","LAMP"]:
#                    found.append(child)
#                else:
#                    self.getChildObjects(child,found)
        
        return found

    # collects all exportable objects from the scene
    def collect(self):
        if profile:
            profiler.start("XPlaneData.collect")
        
        for layer in self.getActiveLayers():
            xplaneLayer = self.getXPlaneLayer(layer)
            filename = self.getFilenameFromXPlaneLayer(xplaneLayer)
            self.files[filename] = self.getEmptyFile(xplaneLayer)
            self.collectObjects(self.getObjectsByLayer(layer),filename)
            #self.splitFileByTexture(xplaneLayer)
                
        if profile:
            profiler.end("XPlaneData.collect")

    def collectBones(self,bones,filename,parent):
        for bone in bones:
            if debug:
                debugger.debug("scanning "+bone.name)
                debugger.debug("\t "+bone.name+": adding to list")

            xplaneBone = XPlaneBone(bone,parent)
            parent.children.append(xplaneBone)

            # get child objects this bone might be a parent of
            self.collectBoneObjects(xplaneBone,filename)
            
            # recursion
            self.collectBones(bone.children,filename,xplaneBone)

    def collectBoneObjects(self,xplaneBone,filename):
        if xplaneBone.armature != None:
            for obj in xplaneBone.armature.object.children:
                if obj.parent_bone == xplaneBone.name:
                    self.collectObjects([obj],filename,xplaneBone)
                
    def collectObjects(self,objects,filename,parent = None):
        for obj in objects:
            if debug:
                debugger.debug("scanning "+obj.name)
                
            if obj.hide==False:
                # look for children
                children = self.getChildObjects(obj)

                # armature: go through the children and check if they are parented to a bone
                if obj.type == 'ARMATURE':
                    armature = XPlaneArmature(obj,parent)
                    if parent == None:
                        self.files[filename]["objects"].append(armature)

                    # add to child list
                    if parent != None:
                        parent.children.append(armature)

                    for bone in obj.data.bones:
                        rootBones = []
                        # root bones only
                        if bone.parent == None:
                            rootBones.append(bone)

                        # recursion
                        self.collectBones(rootBones,filename,armature)

                # unsuported object type: Keep it to store hierarchy
                elif obj.type in ['EMPTY','CAMERA','SURFACE','CURVE','FONT','META','LATTICE']:
                    if debug:
                        debugger.debug("\t "+obj.name+": adding to list")
                    xplaneObj = XPlaneObject(obj,parent)
                    if parent == None:
                        self.files[filename]["objects"].append(xplaneObj)

                    # add to child list
                    if parent != None:
                        parent.children.append(xplaneObj)

                    # recursion
                    if len(children)>0:
                        self.collectObjects(children,filename,xplaneObj)
                    
                # mesh: let's create a prim out of it
                elif obj.type=="MESH":
                    if debug:
                        debugger.debug("\t "+obj.name+": adding to list")
                    prim = XPlanePrimitive(obj,parent)
                    if parent == None:
                        self.files[filename]['objects'].append(prim)

                    self.files[filename]['primitives'].append(prim)

                    # add to child list
                    if parent != None:
                        parent.children.append(prim)

                    # recursion
                    if len(children)>0:
                        self.collectObjects(children,filename,prim)

                # lamp: let's create a XPlaneLight. Those cannot have children (yet).
                elif obj.type=="LAMP":
                    if debug:
                        debugger.debug("\t "+obj.name+": adding to list")
                    light = XPlaneLight(obj,parent)
                    
                    if parent == None:
                        self.files[filename]['objects'].append(light)

                    self.files[filename]['lights'].append(light)

                    # add to child list
                    if parent != None:
                        parent.children.append(xplaneObj)
                
    def getBone(self,armature,name):
        for bone in armature.bones:
            if bone.name == name:
                return bone
        return None

    # TODO: not working with new nested export. Propably XPlane Layers must hold texture info?
    def splitFileByTexture(self,parent):
        name = self.getFilenameFromXPlaneLayer(parent)
        filename = None
        textures = []
        if len(self.files[name])>0:
            # stores prims that have to be removed after iteration
            remove = []
            for obj in self.files[name]['objects']:
                if obj.type=='PRIMITIVE' and obj.material.texture!=None:
                    filename = name+'_'+obj.material.texture[0:-4]
                    
                    # create new file list if not existant
                    if filename not in self.files:
                        self.files[filename] = self.getEmptyFile(parent)

                    # store prim in the file list
                    self.files[filename]['objects'].append(obj)
                    remove.append(obj)

            # remove prims that have been placed in other files
            for obj in remove:
                self.files[name]['objects'].remove(obj)

            # add texture to list
            if filename:
                textures.append(filename)

            # do some house cleaning
            # if there is only one texture in use and no objects without texture, put everything in one file
            if (len(textures)==1 and len(self.files[name]['objects'])==0):
                self.files[textures[0]]['lights'] = self.files[name]['lights']
                self.files[textures[0]]['lines'] = self.files[name]['lines']
                del self.files[name]
    

class XPlaneHeader():
    def __init__(self,file,mesh,lights,version):
        self.version = version
        self.mode = "default"
        self.attributes = OrderedDict([("TEXTURE",None),
                        ("TEXTURE_LIT",None),
                        ("TEXTURE_NORMAL",None),
                        ("POINT_COUNTS",None),
                        ("slung_load_weight",None),
                        ("COCKPIT_REGION",None)])

        # set slung load
        if file['parent'].slungLoadWeight>0:
            self.attributes['slung_load_weight'] = file['parent'].slungLoadWeight

        # set Texture
#        if(len(file['primitives'])>0 and file['primitives'][0].material.texture != None):
#            tex = file['primitives'][0].material.texture
#            self.attributes['TEXTURE'] = tex
#            self.attributes['TEXTURE_LIT'] = tex[0:-4]+'_LIT.png'
#            self.attributes['TEXTURE_NORMAL'] = tex[0:-4]+'_NML.png'
        if file['parent'].texture!='':
            self.attributes['TEXTURE'] = file['parent'].texture
        if file['parent'].texture_lit!='':
            self.attributes['TEXTURE_LIT'] = file['parent'].texture_lit
        if file['parent'].texture_normal!='':
            self.attributes['TEXTURE_NORMAL'] = file['parent'].texture_normal

        # get point counts
        tris = len(mesh.vertices)
        lines = 0
        lights = len(lights.lights)
        indices = len(mesh.indices)
        
        self.attributes['POINT_COUNTS'] = "%d\t%d\t%d\t%d" % (tris,lines,lights,indices)

        # add custom attributes
        for attr in file['parent'].customAttributes:
            self.attributes[attr.name] = attr.value

    def write(self):
        import platform

        system = platform.system()

        # line ending types (I = UNIX/DOS, A = MacOS)
        if 'Mac OS' in system:
            o = 'A\n'
        else:
            o = 'I\n'

        # version number
        if self.version>=8:
            o+='800\n'

        o+='OBJ\n\n'

        # attributes
        for attr in self.attributes:
            if self.attributes[attr]!=None:
                o+='%s\t%s\n' % (attr,self.attributes[attr])
        
        return o
        

class ExportXPlane9(bpy.types.Operator, ExportHelper):
    '''Export to XPlane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export XPlane Object'
    
    filepath = StringProperty(name="File Path", description="Filepath used for exporting the XPlane file(s)", maxlen= 1024, default= "")
    #check_existing = BoolProperty(name="Check Existing", description="Check and warn on overwriting existing files", default=True, options={'HIDDEN'})

    def execute(self, context):
        if debug:
            debugger.start(log)

        if profile:
            profiler.start("ExportXPlane9")

        filepath = self.properties.filepath
        if filepath=='':
            filepath = bpy.context.blend_data.filepath

        filepath = os.path.dirname(filepath)
        #filepath = bpy.path.ensure_ext(filepath, ".obj")

        #store current frame as we will go back to it
        currentFrame = bpy.context.scene.frame_current

        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame=1)
        bpy.context.scene.update()

        data = XPlaneData()
        data.collect()

        # goto first frame again so everything is in inital state
        bpy.context.scene.frame_set(frame=1)
        bpy.context.scene.update()

        if len(data.files)>0:
            if debug:
                debugger.debug("Writing XPlane Object file(s) ...")
            for file in data.files:
                o=''
                if (len(data.files[file]['objects'])>0 or len(data.files[file]['lights'])>0 or len(data.files[file]['lines'])>0):
                    mesh = XPlaneMesh(data.files[file])
                    lights = XPlaneLights(data.files[file])
                    header = XPlaneHeader(data.files[file],mesh,lights,9)
                    commands = XPlaneCommands(data.files[file])
                    o+=header.write()
                    o+="\n"
                    o+=mesh.writeVertices()
                    o+="\n"
                    o+=lights.writeLights()
                    o+="\n"
                    o+=mesh.writeIndices()
                    o+="\n"
                    o+=commands.write()
                    
                    o+="\n# Build with Blender %s (build %s) Exported with XPlane2Blender %3.2f" % (bpy.app.version_string,bpy.app.build_revision,version/1000)

                    if profile:
                        profiler.start("ExportXPlane9 %s" % file)

                    # write the file
                    fullpath = os.path.join(filepath,file+'.obj')
                    if debug:
                        debugger.debug("Writing %s" % fullpath)
                    file = open(fullpath, "w")
                    file.write(o)
                    file.close()

                    if profile:
                        profiler.end("ExportXPlane9 %s" % file)
                else:
                    if debug:
                        debugger.debug("No objects to export, aborting ...")
        else:
            if debug:
                debugger.debug("No objects to export, aborting ...")

        # return to stored frame
        bpy.context.scene.frame_set(frame=currentFrame)
        bpy.context.scene.update()

        if profile:
            profiler.end("ExportXPlane9")
            if debug:
                debugger.debug("\nProfiling results:")
                debugger.debug(profiler.getTimes())

        if debug:
            debugger.end()
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}