import os.path
import bpy
import struct
import os
import math
from bpy.props import *
from collections import OrderedDict

debug = True
version = 3200

def localToGlobal(object):
    matrix = object.matrix_world
    loc = matrix.translation_part()
    loc = [loc[0],loc[1],loc[2]]
    rot = matrix.rotation_part().to_euler("XYZ")
    rot = [rot[0],rot[1],rot[2]]
    scale = matrix.scale_part()
    scale = [scale[0],scale[1],scale[2]]
    return {"loc":loc,"rot":rot,"scale":scale}

def convertCoords(co):
    return [-co[0],co[2],co[1]]

class XPlaneLight():
    def __init__(self,object):
        self.object = object
        self.name = object.name
        self.indices = [0,0]
        self.color = [object.data.color[0],object.data.color[1],object.data.color[2]]
        self.type = object.data.xplane.lightType

        # change color according to type
        if self.type=='flashing':
            self.color[0] = -self.color[0]
        elif self.type=='pulsing':
            self.color[0] = 9.9
            self.color[1] = 9.9
            self.color[2] = 9.9
        elif self.type=='strobe':
            self.color[0] = 9.8
            self.color[1] = 9.8
            self.color[2] = 9.8
        elif self.type=='traffic':
            self.color[0] = 9.7
            self.color[1] = 9.7
            self.color[2] = 9.7


class XPlaneLine():
    def __init_(self,object):
        self.object = object
        self.name = object.name
        self.indices = [0,0]


class XPlaneKeyframe():
    def __init__(self,keyframe,index,dataref,prim):
        self.value = keyframe.co[1]
        self.dataref = dataref
        self.translation = [0.0,0.0,0.0]
        self.rotation = [0.0,0.0,0.0]
        object = prim.object

        # goto keyframe and read out object values
        # TODO: support subframes?
        frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame=frame)

        # update object so we get values from the keyframe
        object.update(scene=bpy.context.scene)
        
        # convert local to global
        glob = localToGlobal(object)
        location = glob['loc']
        rotation = glob['rot']
        
        # swap y and z and invert x (right handed system)
        self.location = [-location[0],location[2],location[1]]
        self.angle = [math.degrees(rotation[0]),math.degrees(rotation[2]),math.degrees(rotation[1])]
        
        self.hide = object.hide_render

        # remove initial location and rotation to get offset
        for i in range(0,3):
            self.translation[i] = self.location[i]-prim.location[i]
            self.rotation[i] = self.angle[i]-prim.angle[i]

#        if index>0:
#            # remove location, rotation and scale from previous keyframe to get the offset
#            keyframes = prim.animations[dataref]
#
#            for i in range(0,3):
#                self.translation[i] = self.location[i]-keyframes[index-1].location[i]
#                self.rotation[i] = self.angle[i]-keyframes[index-1].angle[i]
                
class XPlanePrimitive():
    def __init__(self,object):
        self.object = object
        self.name = object.name
        
        # update object display so we have initial values
        object.update(scene=bpy.context.scene)

        # convert local to global
        glob = localToGlobal(object)
        location = glob['loc']
        rotation = glob['rot']

        # store initial global location, rotation and scale
        self.location = [-location[0],location[2],location[1]]
        self.angle = [math.degrees(rotation[0]),math.degrees(rotation[2]),math.degrees(rotation[1])]

        self.indices = [0,0]
        self.material = XPlaneMaterial(self.object)
        self.faces = None
        self.datarefs = {}
        self.attributes = {}
        self.animations = {}

        #check for animation
        if debug:
            print("\t\t checking animations")
        if (object.animation_data != None and object.animation_data.action != None and len(object.animation_data.action.fcurves)>0):
            if debug:
                print("\t\t animation found")
            #check for dataref animation by getting fcurves with the dataref group
            for fcurve in object.animation_data.action.fcurves:
                if debug:
                    print("\t\t checking FCurve %s" % fcurve.data_path)
                if (fcurve.group != None and fcurve.group.name == "XPlane Datarefs"):
                    # get dataref name
                    index = int(fcurve.data_path.replace('["xplane"]["datarefs"][','').replace(']["value"]',''))
                    dataref = object.xplane.datarefs[index].path

                    if debug:
                        print("\t\t adding dataref animation: %s" % dataref)
                        
                    if len(fcurve.keyframe_points)>1:
                        # time to add dataref to animations
                        self.animations[dataref] = []

                        # store keyframes temporary, so we can resort them
                        keyframes = []

                        for keyframe in fcurve.keyframe_points:
                            if debug:
                                print("\t\t adding keyframe: %6.3f" % keyframe.co[0])
                            keyframes.append(keyframe)

                        # sort keyframes by frame number
                        keyframesSorted = sorted(keyframes, key=lambda keyframe: keyframe.co[0])
                        
                        for i in range(0,len(keyframesSorted)):
                            self.animations[dataref].append(XPlaneKeyframe(keyframesSorted[i],i,dataref,self))

        # add custom attributes
        for attr in object.xplane.customAttributes:
            self.attributes[attr.name] = attr.value


class XPlaneMaterial():
    def __init__(self,object):
        self.object = object
        self.texture = None
        self.uv_name = None

        # Material
        self.attributes = {"ATTR_diffuse_rgb":None,
                           "ATTR_specular_rgb":None,
                           "ATTR_emission_rgb":None,
                           "ATTR_shiny_rat":None,
                           "ATTR_hard":None,
                           "ATTR_no_hard":None,
                           "ATTR_cull":None,
                           "ATTR_no_cull":None,                           
                           "ATTR_depth":None,
                           "ATTR_no_depth":None,
                           "ATTR_blend":None,
                           "ATTR_no_blend":None}

        if len(object.data.materials)>0:
            mat = object.data.materials[0]

            # diffuse
            if mat.diffuse_intensity>0:
                diffuse = [mat.diffuse_intensity*mat.diffuse_color[0],
                            mat.diffuse_intensity*mat.diffuse_color[1],
                            mat.diffuse_intensity*mat.diffuse_color[2]]
                self.attributes['ATTR_diffuse_rgb'] = "%6.3f %6.3f %6.3f" % (diffuse[0], diffuse[1], diffuse[2])

            # specular
            if mat.specular_intensity>0:
                specular = [mat.specular_intensity*mat.specular_color[0],
                            mat.specular_intensity*mat.specular_color[1],
                            mat.specular_intensity*mat.specular_color[2]]
                self.attributes['ATTR_specular_rgb'] = "%6.3f %6.3f %6.3f" % (specular[0], specular[1], specular[2])
                self.attributes['ATTR_shiny_rat'] = "%6.3f" % mat.specular_hardness

            # emission
            if mat.emit>0:
                emission = [mat.emit*mat.diffuse_color[0],
                            mat.emit*mat.diffuse_color[1],
                            mat.emit*mat.diffuse_color[2]]
                self.attributes['ATTR_emission_rgb'] = "%6.3f %6.3f %6.3f" % (emission[0], emission[1], emission[2])

            # surface type
            if mat.xplane.surfaceType != 'none':
                self.attributes['ATTR_hard'] = mat.xplane.surfaceType

            # backface culling
            if self.object.data.show_double_sided:
                self.attributes['ATTR_no_cull'] = True

            # blend
            if mat.xplane.blend:
                self.attributes['ATTR_no_blend'] = "%6.3f" % mat.xplane.blendRatio

            # depth check
            if self.object.xplane.depth == False:
                self.attributes['ATTR_no_depth'] = True;

            # Texture and uv-coordinates
            if(len(mat.texture_slots)>0 and hasattr(mat.texture_slots[0],'use') and mat.texture_slots[0].use and mat.texture_slots[0].texture.type=="IMAGE"):
                tex =  mat.texture_slots[0].texture
                if(tex.image.file_format=='PNG'):
                    self.texture = os.path.basename(tex.image.filepath)

                if mat.texture_slots[0].texture_coords == 'UV':
                    self.uv_name = mat.texture_slots[0].uv_layer

            # add custom attributes
            for attr in mat.xplane.customAttributes:
                self.attributes[attr.name] = attr.value

#    def write(self):
#        o=''
#        for attr in self.attributes:
#            if self.attributes[attr]!=None:
#                if(self.attributes[attr]==True):
#                    o+='%s\n' % attr
#                else:
#                    o+='%s\t%s\n' % (attr,self.attributes[attr])
#
#        return o

class XPlaneFace():
    def __init__(self):
        self.vertices = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.normals = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.indices = [0,0,0]
        self.uvs = [(0.0,0.0),(0.0,0.0),(0.0,0.0)]
        self.smooth = False


class XPlaneFaces():
    def __init__(self):
        self.faces = []

    def append(self,face):
        self.faces.append(face)

    def remove(self,face):
        del self.faces[face]

    def get(self,i):
        if len(self.faces)-1>=i:
            return self.faces[i]
        else:
            return None

    def write(self):
        # TODO: collect groups of face attributes and dump them together with the TRIS command?
        return ''


class XPlaneMesh():
    def __init__(self,file):
        self.vertices = []
        self.indices = []

        # store the global index, as we are reindexing faces
        globalindex = 0

        for prim in file['primitives']:
            prim.indices[0] = len(self.indices)
            
            # store the world translation matrix
            matrix = prim.object.matrix_world
            
            # create a copy of the object mesh with modifiers applied
            mesh = prim.object.create_mesh(bpy.context.scene, True, "PREVIEW")

            # transform mesh with the world matrix
            mesh.transform(matrix)

            # with the new mesh get uvFaces list
            uvFaces = self.getUVFaces(mesh,prim.material.uv_name)

            faces = XPlaneFaces()

            # convert faces to triangles
            tempfaces = []
            for i in range(0,len(mesh.faces)):
                if uvFaces != None:
                    tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],uvFaces[i]))
                else:
                    tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],None))
                    
            for f in tempfaces:
                xplaneFace = XPlaneFace()
                l = len(f['indices'])
                for i in range(0,len(f['indices'])):
                    # get the original index, reverse direction because of axis swap
                    vindex = f['indices'][l-1-i]

                    # get the vertice from original mesh
                    v = mesh.vertices[vindex]
                    
                    # convert local to global coordinates
                    #co = matrix * v.co
                    co = v.co

                    # swap y and z and invert x (right handed system)
                    vert = [-co[0],co[2],co[1],-v.normal[0],v.normal[2],v.normal[1],f['uv'][i][0],f['uv'][i][1]]

                    # use dupli vertice if any
                    index = self.getDupliVerticeIndex(vert)
                    if (index==-1):
                        index = globalindex
                        self.vertices.append(vert)
                        globalindex+=1

                    # store face information alltogether in one struct
                    xplaneFace.vertices[i] = (vert[0],vert[1],vert[2])
                    xplaneFace.normals[i] = (vert[3],vert[4],vert[5])
                    xplaneFace.uvs[i] = (vert[6],vert[7])
                    xplaneFace.indices[i] = index  
                    
                    self.indices.append(index)
                    
                faces.append(xplaneFace)

            # store the faces in the prim
            prim.faces = faces
            prim.indices[1] = len(self.indices)
            
    def getDupliVerticeIndex(self,v):
        for i in range(len(self.vertices)):
            match = True
            ii = 0
            while ii<len(self.vertices[i]):
                if self.vertices[i][ii] != v[ii]:
                    match = False
                    ii = len(self.vertices[i])
                ii+=1
                
            if match:
                return i
            
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
        triangles = []
        if len(face.vertices_raw)==4: #quad
            if uv != None:
                triangles.append( {"uv":[[uv.uv1[0], uv.uv1[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv3[0], uv.uv3[1]]], "indices":[face.vertices_raw[0], face.vertices_raw[1], face.vertices_raw[2]]})
                triangles.append( {"uv":[[uv.uv3[0], uv.uv3[1]], [uv.uv4[0], uv.uv4[1]], [uv.uv1[0], uv.uv1[1]]], "indices":[ face.vertices_raw[2], face.vertices_raw[3], face.vertices_raw[0]]})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[face.vertices_raw[0], face.vertices_raw[1], face.vertices_raw[2]]})
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[ face.vertices_raw[2], face.vertices_raw[3], face.vertices_raw[0]]})
        else:
            if uv != None:
                triangles.append( {"uv":[[uv.uv1[0], uv.uv1[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv3[0], uv.uv3[1]]], "indices":face.vertices_raw})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":face.vertices_raw})

        return triangles

    def faceValues(self,face, mesh, matrix):
        fv = []
        for verti in face.vertices_raw:
            fv.append(matrix * mesh.vertices[verti].co)
        return fv

    def writeVertices(self):
        o=''
        for v in self.vertices:
            # dump the vertex data
            o+="VT"
            for i in v:
                o+="\t%6.4f" % i
            o+="\n"
        
        return o

    def writeIndices(self):
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
            
        return o

class XPlaneLights():
    def __init__(self,file):
        self.vertices = []
        self.indices = []

        # store the global index, as we are reindexing faces
        globalindex = 0

        for light in file['lights']:
            light.indices[0] = globalindex

            # store the world translation matrix
            matrix = light.object.matrix_world
            
            # get the vertice from original mesh
            v = light.object.location

            # convert local to global coordinates
            co = matrix * v

            self.vertices.append([-co[0],co[2],co[1],light.color[0],light.color[1],light.color[2]])
            self.indices.append(globalindex)
            globalindex+=1

            light.indices[1] = globalindex

        # reverse indices due to the inverted z axis
        self.indices.reverse()

    def writeVertices(self):
        o=''
        for v in self.vertices:
            o+='VLIGHT'
            for f in v:
                o+='\t%6.4f' % f
            o+='\n'
        
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
        for prim in self.file['primitives']:
            animationStarted = False
            if debug:
                o+="# %s\n" % prim.name
                
            tabs = ''
            if len(prim.animations)>0:
                animationStarted = True
                animLevel = self.getAnimLevel(prim)
                
                # begin animation block
                o+="%sANIM_begin\n" % self.getAnimTabs(animLevel)
                animLevel+=1
                tabs = self.getAnimTabs(animLevel)
                
                for dataref in prim.animations:
                    if len(prim.animations[dataref])>1:
                        o+=self.writeKeyframes(prim,dataref,tabs)

#                    for i in range(0,len(prim.animations[dataref])):
#                        o+=self.writeKeyframe(prim,dataref,i,tabs)
                    
            #material
            for attr in prim.material.attributes:
                if prim.material.attributes[attr]!=None:
                    if(prim.material.attributes[attr]==True):
                        value = ""
                        line = '%s\n' % attr
                    else:
                        value = prim.material.attributes[attr]
                        line = '%s\t%s\n' % (attr,value)

                    o+=tabs+line
                    # only write line if attribtue wasn't already written with same value
#                    if attr in self.written:
#                        if self.written[attr]!=value:
#                            o+=line
#                            self.written[attr] = value
#                    else:
#                        o+=line
#                        self.written[attr] = value

            #custom object attributes
            for attr in prim.attributes:
                line='%s\t%s\n' % (attr,prim.attributes[attr])
                o+=tabs+line
            
            #o+=prim.material.write()
            o+=prim.faces.write()
            offset = prim.indices[0]
            count = prim.indices[1]-prim.indices[0]
            o+="%sTRIS\t%d %d\n" % (tabs,offset,count)

            if animationStarted:
                # end animation block
                animLevel-=1
                o+="%sANIM_end\n" % self.getAnimTabs(animLevel)

        # write down all lights
        if len(self.file['lights'])>0:
            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])
            
        return o

    def getAnimTabs(self,level):
        tabs = ''
        if level>0:
            i = 1
            while i<=level:
                tabs+='\t'
                i+=1
        
        return tabs

    def getAnimLevel(self,prim):
        parent = prim.object
        level = 0
        
        while parent != None:
            parent = parent.parent
            if (parent!=None and parent.type!="EMPTY"):
                level+=1
        
        return level

    def writeKeyframes(self,prim,dataref,tabs):
        o = ''

        keyframes = prim.animations[dataref]

        totalTrans = [0.0,0.0,0.0]
        totalRot = [0.0,0.0,0.0]

        # TODO: staticTrans can be merged into regular translations
        staticTrans = ['','']
        staticTrans[0] = "%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,prim.location[0],prim.location[1],prim.location[2],prim.location[0],prim.location[1],prim.location[2])
        staticTrans[1] = "%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,-prim.location[0],-prim.location[1],-prim.location[2],-prim.location[0],-prim.location[1],-prim.location[2])
        
        trans = "%sANIM_trans_begin\t%s\n" % (tabs,dataref)
        rot = ['','','']
        rot[0] = "%sANIM_rotate_begin\t1.0\t0.0\t0.0\t%s\n" % (tabs,dataref)
        rot[1] = "%sANIM_rotate_begin\t0.0\t1.0\t0.0\t%s\n" % (tabs,dataref)
        rot[2] = "%sANIM_rotate_begin\t0.0\t0.0\t1.0\t%s\n" % (tabs,dataref)
        
        for keyframe in keyframes:
            totalTrans[0]+=keyframe.translation[0]
            totalTrans[1]+=keyframe.translation[1]
            totalTrans[2]+=keyframe.translation[2]
            trans+="%s\tANIM_trans_key\t%6.4f\t%6.4f\t%6.4f\t%6.4f\n" % (tabs,keyframe.value,keyframe.translation[0],keyframe.translation[1],keyframe.translation[2])
            
            totalRot[0]+=keyframe.rotation[0]
            totalRot[1]+=keyframe.rotation[1]
            totalRot[2]+=keyframe.rotation[2]

            for i in range(0,3):
                rot[i]+="%s\tANIM_rotate_key\t%6.4f\t%6.4f\n" % (tabs,keyframe.value,keyframe.rotation[i])
            
        trans+="%sANIM_trans_end\n" % tabs
        rot[0]+="%sANIM_rotate_end\n" % tabs
        rot[1]+="%sANIM_rotate_end\n" % tabs
        rot[2]+="%sANIM_rotate_end\n" % tabs

        if totalTrans[0]!=0.0 or totalTrans[1]!=0.0 or totalTrans[2]!=0.0:
            o+=trans

        if totalRot[0]!=0.0 or totalRot[1]!=0.0 or totalRot[2]!=0.0:
            o+=staticTrans[0]
            
            if totalRot[0]!=0.0:
                o+=rot[0]
            if totalRot[1]!=0.0:
                o+=rot[1]
            if totalRot[2]!=0.0:
                o+=rot[2]

            o+=staticTrans[1]
        
        return o

#    def writeKeyframe(self,prim,dataref,index,tabs):
#        o = ''
#
#        if index>0:
#            if debug:
#                o+="%s# keyframes %d,%d\n" % (tabs,index-1,index)
#
#            prevKeyframe = None
#            translations = []
#            rotations = []
#            prevKeyframe = prim.animations[dataref][index-1]
#
#            keyframe = prim.animations[dataref][index]
#
#            # check for translation and rotation
#            for i in range(0,3):
#                if keyframe.translation[i]!=0:
#                    translations.append(i)
#                if keyframe.rotation[i]!=0:
#                    rotations.append(i)
#
#            if len(rotations)>0:
#                # move object center to world origin by adding a static translation
#                o+="%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,keyframe.location[0],keyframe.location[1],keyframe.location[2],keyframe.location[0],keyframe.location[1],keyframe.location[2])
#
#                #now add rotation from prev to current keyframe
#                for i in rotations:
#                    rot = [0.0,0.0,0.0]
#                    rot[i] = 1.0
#                    o+="%sANIM_rotate\t%6.4f\t%6.4f\t%6.4f\t0.0\t%6.4f\t%6.4f\t%6.4f\t%s\n" % (tabs,rot[0],rot[1],rot[2],keyframe.rotation[i],prevKeyframe.value,keyframe.value,dataref)
#
#                # move object back to original position to add translation
#                o+="%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,-keyframe.location[0],-keyframe.location[1],-keyframe.location[2],-keyframe.location[0],-keyframe.location[1],-keyframe.location[2])
#
#            if len(translations)>0:
#                #now add translation from prev to current keyframe
#                o+="%sANIM_trans\t0.0\t0.0\t0.0\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%s\n" % (tabs,keyframe.translation[0],keyframe.translation[1],keyframe.translation[2],prevKeyframe.value,keyframe.value,dataref)
#
#
#        return o

class XPlaneData():
    def __init__(self):
        self.files = {}

    def getEmptyFile(self,parent):
        return {'primitives':[],'lights':[],'lines':[],'parent':parent}

    # collect all exportable objects from the scene
    def collect(self):
        for obj in bpy.context.scene.objects:
            if debug:
                print("scanning "+obj.name)
                
            if(obj.type=="EMPTY" and obj.xplane.exportChildren and obj.hide==False):
                if debug:
                    print(obj.name+": export children")

                self.files[obj.name] = self.getEmptyFile(obj)
                for child in obj.children:
                    if debug:
                        print("\t scanning "+child.name)

                    if child.hide==False:
                        if child.type=="MESH":
                            if debug:
                                print("\t "+child.name+": adding to list")
                            self.files[obj.name]['primitives'].append(XPlanePrimitive(child))
                        if child.type=="LAMP":
                            if debug:
                                print("\t "+child.name+": adding to list")
                            self.files[obj.name]['lights'].append(XPlaneLight(child))

                # apply further splitting by textures
                self.splitFileByTexture(obj)

    def splitFileByTexture(self,parent):
        name = parent.name
        filename = None
        textures = []
        if len(self.files[name])>0:
            # stores prims that have to be removed after iteration
            remove = []
            for prim in self.files[name]['primitives']:
                if prim.material.texture!=None:
                    filename = name+'_'+prim.material.texture[0:-4]
                    
                    # create new file list if not existant
                    if filename not in self.files:
                        self.files[filename] = self.getEmptyFile(parent)

                    # store prim in the file list
                    self.files[filename]['primitives'].append(prim)
                    remove.append(prim)

            # remove prims that have been placed in other files
            for prim in remove:
                self.files[name]['primitives'].remove(prim)

            # add texture to list
            if filename:
                textures.append(filename)

            # do some house cleaning
            # if there is only one texture in use and no objects without texture, put everything in one file
            if (len(textures)==1 and len(self.files[name]['primitives'])==0):
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
        if file['parent'].xplane.slungLoadWeight>0:
            self.attributes['slung_load_weight'] = file['parent'].xplane.slungLoadWeight

        # set Texture
        if(len(file['primitives'])>0 and file['primitives'][0].material.texture != None):
            tex = file['primitives'][0].material.texture
            self.attributes['TEXTURE'] = tex
            self.attributes['TEXTURE_LIT'] = tex[0:-4]+'_LIT.png'
            self.attributes['TEXTURE_NORMAL'] = tex[0:-4]+'_NML.png'

        # get point counts
        tris = len(mesh.vertices)
        lines = 0
        lites = len(lights.vertices)
        indices = len(mesh.indices)
        
        self.attributes['POINT_COUNTS'] = "%d\t%d\t%d\t%d" % (tris,lines,lites,indices)

        # add custom attributes
        for attr in file['parent'].xplane.customAttributes:
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
        

class ExportXPlane9(bpy.types.Operator):
    '''Export to XPlane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export XPlane Object'
    
    filepath = StringProperty(name="File Path", description="Filepath used for exporting the XPlane file(s)", maxlen= 1024, default= "")
    check_existing = BoolProperty(name="Check Existing", description="Check and warn on overwriting existing files", default=True, options={'HIDDEN'})

    def execute(self, context):
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
            print("Writing XPlane Object file(s) ...")
            for file in data.files:
                o=''
                if (len(data.files[file]['primitives'])>0 or len(data.files[file]['lights'])>0 or len(data.files[file]['lines'])>0):
                    mesh = XPlaneMesh(data.files[file])
                    lights = XPlaneLights(data.files[file])
                    header = XPlaneHeader(data.files[file],mesh,lights,9)
                    commands = XPlaneCommands(data.files[file])
                    o+=header.write()
                    o+="\n"
                    o+=mesh.writeVertices()
                    o+="\n"
                    o+=lights.writeVertices()
                    o+="\n"
                    o+=mesh.writeIndices()
                    o+="\n"
                    o+=commands.write()
                    
                    o+="\n# Build with Blender %s (build %s) Exported with XPlane2Blender %3.2f" % (bpy.app.version_string,bpy.app.build_revision,version/1000)

                    # write the file
                    fullpath = os.path.join(filepath,file+'.obj')
                    print("Writing %s" % fullpath)
                    file = open(fullpath, "w")
                    file.write(o)
                    file.close()
                    #print(o)
                else:
                    print("No objects to export, aborting ...")
        else:
            print("No objects to export, aborting ...")

        # return to stored frame
        bpy.context.scene.frame_set(frame=currentFrame)
        bpy.context.scene.update()
        
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}