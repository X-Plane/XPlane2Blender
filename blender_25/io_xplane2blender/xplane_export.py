import os.path
import bpy
import struct
import os
import math
from mathutils import Matrix
from bpy.props import *
from collections import OrderedDict

debug = True
version = 3200

# python mathutils supports euler order so you could convert the rotation this way
# probably transform rotation as a matrix into the exported space without the flipped axis, then convert to a euler with the order you need, and flip the axis
class XPlaneCoords():
    def __init__(self,object):
        self.object = object

    def worldLocation(self):
        matrix = XPlaneCoords.convertMatrix(self.object.matrix_world)
        loc = matrix.translation_part()
        return loc #self.convert([loc[0],loc[1],loc[2]])

    def worldRotation(self):
        matrix = XPlaneCoords.convertMatrix(self.object.matrix_world)
        rot = matrix.rotation_part().to_euler("XZY")
        return rot #[-rot[0],rot[1],rot[2]]

    def worldAngle(self):
        return self.angle(self.worldRotation())

    def worldScale(self):
        matrix = XPlaneCoords.convertMatrix(self.object.matrix_world)
        scale = matrix.scale_part()
        return scale #self.convert([scale[0],scale[1],scale[2]],True)

    def world(self):
        matrix = XPlaneCoords.convertMatrix(self.object.matrix_world)
        loc = matrix.translation_part()
        #loc = self.convert([loc[0],loc[1],loc[2]])
        rot = matrix.rotation_part().to_euler("XZY")
        #rot = [-rot[0],rot[1],rot[2]]
        scale = matrix.scale_part()
        #scale = self.convert([scale[0],scale[1],scale[2]],True)
        return {'location':loc,'rotation':rot,'scale':scale,'angle':self.angle(rot)}

    def localLocation(self,parent):
        matrix = XPlaneCoords.convertMatrix(self.relativeMatrix(parent))
        loc = matrix.translation_part()
        return loc #self.convert([loc[0],loc[1],loc[2]])
        
    def localRotation(self,parent):
        matrix = XPlaneCoords.convertMatrix(self.relativeMatrix(parent))
        rot = matrix.rotation_part().to_euler("XYZ")
        return rot #self.convert([rot[0],rot[1],rot[2]])

    def localAngle(self,parent):
        return self.angle(self.localRotation())

    def localScale(self,parent):
        matrix = XPlaneCoords.convertMatrix(self.relativeMatrix(parent))
        scale = matrix.scale_part()
        return scale #self.convert([scale[0],scale[1],scale[2]],True)

    def local(self,parent):
#        coordsParent = XPlaneCoords(parent).world()
#        coords = self.world()
#        for i in range(0,3):
#            if (i==0):
#                coords["location"][i] = coords["location"][i]-coordsParent["location"][i]
#                coords["rotation"][i] = coords["rotation"][i]-coordsParent["rotation"][i]
#                coords["angle"][i] = coords["angle"][i]-coordsParent["angle"][i]
#            else:
#                coords["location"][i] = coords["location"][i]+coordsParent["location"][i]
#                coords["rotation"][i] = coords["rotation"][i]+coordsParent["rotation"][i]
#                coords["angle"][i] = coords["angle"][i]+coordsParent["angle"][i]
#
#        return coords
            
        matrix = XPlaneCoords.convertMatrix(self.relativeMatrix(parent))
        loc = matrix.translation_part()
        #loc = self.convert([loc[0],loc[1],loc[2]])
        rot = matrix.rotation_part().to_euler("XYZ")
        #rot = self.convert([rot[0],rot[1],rot[2]])
        scale = matrix.scale_part()
        #scale = self.convert([scale[0],scale[1],scale[2]],True)
        return {'location':loc,'rotation':rot,'scale':scale,'angle':self.angle(rot)}

    def angle(self,rot):
        return [math.degrees(rot[0]),math.degrees(rot[1]),math.degrees(rot[2])]

    def convert(self,co,scale = False):
        if (scale):
            return [co[0],co[2],co[1]]
        else:
            return [-co[0],co[2],co[1]]

    def relativeMatrix(self,parent):
        return self.object.matrix_world * parent.matrix_world.copy().invert()

    def conversionMatrix(self):
        cmatrix = Matrix()
        cmatrix[0][0] = 1
        cmatrix[1][2] = 1
        #cmatrix[1][1] = 1
        cmatrix[2][1] = -1
        return cmatrix

    @staticmethod
    def convertMatrix(matrix):
#If your matrix looks like this:
#{ rx, ry, rz, 0 }
#{ ux, uy, uz, 0 }
#{ lx, ly, lz, 0 }
#{ px, py, pz, 1 }
#
#To change it from left to right or right to left, flip it like this:
#{ rx, rz, ry, 0 }
#{ lx, lz, ly, 0 }
#{ ux, uz, uy, 0 }
#{ px, pz, py, 1 }
#        cmatrix = Matrix(( 1, 0, 0, 0),
#                         ( 0, 1, 0, 0),
#                         ( 0, 0,-1, 0),
#                         ( 0, 0, 0, 1))
#        cmatrix = Matrix(( 1, 0, 0, 0),
#                         ( 0,-1, 0, 0),
#                         ( 0, 0, 1, 0),
#                         ( 0, 0, 0, 1))
#        cmatrix = Matrix(( 1, 0, 0, 0),
#                         ( 0,-1, 0, 0),
#                         ( 0, 0,-1, 0),
#                         ( 0, 0, 0, 1))
#        cmatrix = Matrix(( 1, 0, 0, 0),
#                         ( 0, 0,-1, 0),
#                         ( 0,-1, 0, 0),
#                         ( 0, 0, 0, 1))
        cmatrix = Matrix(( matrix[0][0], matrix[0][2], -matrix[0][1], matrix[0][3]),
                         ( matrix[2][0], matrix[2][2], -matrix[2][1], matrix[2][3]),
                         ( matrix[1][0], matrix[1][2], -matrix[1][1], matrix[1][3]),
                         ( matrix[3][0], matrix[3][2],  matrix[3][1], matrix[3][3]))
        #return matrix*cmatrix
        return cmatrix


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
        self.scale = [0.0,0.0,0.0]
        self.index = index
        self.primitive = prim
        object = prim.object

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame=self.frame)
        coords = XPlaneCoords(object)

        self.hide = object.hide_render

        if prim.parent!=None:
             # update object so we get values from the keyframe
            prim.parent.object.update(scene=bpy.context.scene)
            object.update(scene=bpy.context.scene)
            
            world = coords.world()
            local = coords.local(prim.parent.object)

            self.location = world["location"]
            self.angle = world["angle"]
            self.scale = world["scale"]           
            
            self.locationLocal = local["location"]
            self.angleLocal = local["angle"]
            self.scaleLocal = local["scale"]
            # TODO: multiply location with scale of parent
            
            for i in range(0,3):
                # remove initial location and rotation to get offset
                self.translation[i] = self.locationLocal[i]-prim.locationLocal[i]
                self.rotation[i] = self.angleLocal[i]-prim.angleLocal[i]
        else:
            # update object so we get values from the keyframe
            object.update(scene=bpy.context.scene)

            world = coords.world()

            self.location = world["location"]
            self.angle = world["angle"]
            self.scale = world["scale"]

            self.locationLocal = self.location
            self.angleLocal = self.angle
            self.scaleLocal = self.scale

            # remove initial location and rotation to get offset
            for i in range(0,3):
                self.translation[i] = self.location[i]-prim.location[i]
                self.rotation[i] = self.angle[i]-prim.angle[i]


class XPlanePrimitive():
    def __init__(self,object,parent = None):
        self.object = object
        self.name = object.name
        self.children = []
        self.parent = parent

        self.indices = [0,0]
        self.material = XPlaneMaterial(self.object)
        self.faces = None
        self.datarefs = {}
        self.attributes = {}
        self.animations = {}
        self.datarefs = {}
        
        # add custom attributes
        for attr in object.xplane.customAttributes:
            self.attributes[attr.name] = attr.value

        self.getCoordinates()
        self.getAnimations()

    def getCoordinates(self):
        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame=1)
        coords = XPlaneCoords(self.object)

        if self.parent!=None:
            # update object display so we have initial values
            self.parent.object.update(scene=bpy.context.scene)
            self.object.update(scene=bpy.context.scene)

            world = coords.world()
            local = coords.local(self.parent.object)

            # store initial location, rotation and scale
            self.location = world["location"]
            self.angle = world["angle"]
            self.scale = world["scale"]           
            
            self.locationLocal = local["location"]
            self.angleLocal = local["angle"]
            self.scaleLocal = local["scale"]
        else:
            # update object display so we have initial values
            self.object.update(scene=bpy.context.scene)
            
            world = coords.world()

            # store initial location, rotation and scale
            self.location = world["location"]
            self.angle = world["angle"]
            self.scale = world["scale"]
            self.locationLocal = [0.0,0.0,0.0]
            self.angleLocal = [0.0,0.0,0.0]
            self.scaleLocal = [0.0,0.0,0.0]

    def getAnimations(self):
        #check for animation
        if debug:
            print("\t\t checking animations")
        if (self.object.animation_data != None and self.object.animation_data.action != None and len(self.object.animation_data.action.fcurves)>0):
            if debug:
                print("\t\t animation found")
            #check for dataref animation by getting fcurves with the dataref group
            for fcurve in self.object.animation_data.action.fcurves:
                if debug:
                    print("\t\t checking FCurve %s" % fcurve.data_path)
                if (fcurve.group != None and fcurve.group.name == "XPlane Datarefs"):
                    # get dataref name
                    index = int(fcurve.data_path.replace('["xplane"]["datarefs"][','').replace(']["value"]',''))
                    dataref = self.object.xplane.datarefs[index].path

                    if debug:
                        print("\t\t adding dataref animation: %s" % dataref)
                        
                    if len(fcurve.keyframe_points)>1:
                        # time to add dataref to animations
                        self.animations[dataref] = []
                        self.datarefs[dataref] = self.object.xplane.datarefs[index]

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


class XPlaneMesh():
    def __init__(self,file):
        self.vertices = []
        self.indices = []

        # store the global index, as we are reindexing faces
        globalindex = 0

        for prim in file['primitives']:
            prim.indices[0] = len(self.indices)
            
            # store the world translation matrix
            matrix = XPlaneCoords.convertMatrix(prim.object.matrix_world)
            
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
                    vindex = f['indices'][i]

                    # get the vertice from original mesh
                    v = mesh.vertices[vindex]
                    
                    # convert local to global coordinates
                    co = v.co

                    # swap y and z and invert x (right handed system)
                    vert = [co[0],co[1],co[2],-v.normal[0],-v.normal[1],-v.normal[2],f['uv'][i][0],f['uv'][i][1]]

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

        # stores already written primitives, that have been written due to nested animations
        self.writtenPrimitives = []

    def write(self):
        o=''
         
        # write down all objects
        for prim in self.file['primitives']:
            if prim not in self.writtenPrimitives:
                o+=self.writePrimitive(prim,0)

        # write down all lights
        if len(self.file['lights'])>0:
            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])
            
        return o

    def writePrimitive(self,prim,animLevel):
        o = ''
        
        animationStarted = False
        tabs = self.getAnimTabs(animLevel)

        if debug:
            o+="%s# %s\n" % (tabs,prim.name)

        if len(prim.animations)>0:
            animationStarted = True

            # begin animation block
            o+="%sANIM_begin\n" % tabs
            animLevel+=1
            tabs = self.getAnimTabs(animLevel)

            for dataref in prim.animations:
                if len(prim.animations[dataref])>1:
                    o+=self.writeKeyframes(prim,dataref,tabs)

        o+=self.writeMaterial(prim,tabs)
        o+=self.writeCustomAttributes(prim,tabs)

        # triangle rendering
        offset = prim.indices[0]
        count = prim.indices[1]-prim.indices[0]
        o+="%sTRIS\t%d %d\n" % (tabs,offset,count)

        self.writtenPrimitives.append(prim)

        if animationStarted:
            if len(prim.children)>0:
                for childPrim in prim.children:
                    if childPrim not in self.writtenPrimitives:
                        o+=self.writePrimitive(childPrim,animLevel)
            # TODO: check if primitive has an animated parent in another file, if so add a dummy anim-block around it?

            # end animation block
            o+="%sANIM_end\n" % self.getAnimTabs(animLevel-1)
        return o

    def getAnimTabs(self,level):
        tabs = ''
        for i in range(0,level):
            tabs+='\t'
        
        return tabs

    def getAnimLevel(self,prim):
        parent = prim
        level = 0
        
        while parent != None:
            parent = parent.parent
            if (parent!=None):
                level+=1
        
        return level

    def writeMaterial(self,prim,tabs):
        o = ''
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
        return o

    def writeCustomAttributes(self,prim,tabs):
        o = ''
        for attr in prim.attributes:
            line='%s\t%s\n' % (attr,prim.attributes[attr])
            o+=tabs+line
        return o

    def writeKeyframes(self,prim,dataref,tabs):
        o = ''

        keyframes = prim.animations[dataref]

        totalTrans = [0.0,0.0,0.0]
        totalRot = [0.0,0.0,0.0]

        # TODO: staticTrans can be merged into regular translations
        staticTrans = ['','']
        staticTrans[0] = "%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,prim.locationLocal[0],prim.locationLocal[1],prim.locationLocal[2],prim.locationLocal[0],prim.locationLocal[1],prim.locationLocal[2])
        staticTrans[1] = "%sANIM_trans\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t0\t0\tnone\n" % (tabs,-prim.locationLocal[0],-prim.locationLocal[1],-prim.locationLocal[2],-prim.locationLocal[0],-prim.locationLocal[1],-prim.locationLocal[2])
        
        trans = "%sANIM_trans_begin\t%s\n" % (tabs,dataref)
        rot = ['','','']
        rot[0] = "%sANIM_rotate_begin\t1.0\t0.0\t0.0\t%s\n" % (tabs,dataref)
        rot[1] = "%sANIM_rotate_begin\t0.0\t1.0\t0.0\t%s\n" % (tabs,dataref)
        rot[2] = "%sANIM_rotate_begin\t0.0\t0.0\t1.0\t%s\n" % (tabs,dataref)
        
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
                print("%s keyframe %d@%d" % (keyframe.primitive.name,keyframe.index,keyframe.frame))
                print("location/prim.location")
                print(keyframe.location)
                print(keyframe.primitive.location)
                print("locationLocal/prim.locationLocal")
                print(keyframe.locationLocal)
                print(keyframe.primitive.locationLocal)
                print("")
            
        trans+="%sANIM_trans_end\n" % tabs
        rot[0]+="%sANIM_rotate_end\n" % tabs
        rot[1]+="%sANIM_rotate_end\n" % tabs
        rot[2]+="%sANIM_rotate_end\n" % tabs

        if totalTrans[0]!=0.0 or totalTrans[1]!=0.0 or totalTrans[2]!=0.0:
            o+=trans
            # add loops if any
            if prim.datarefs[dataref].loop>0:
                o+="%sANIM_keyframe_loop\t%d\n" % (tabs,prim.datarefs[dataref].loop)

        if totalRot[0]!=0.0 or totalRot[1]!=0.0 or totalRot[2]!=0.0:
            o+=staticTrans[0]
            
            if totalRot[0]!=0.0:
                o+=rot[0]
            if totalRot[1]!=0.0:
                o+=rot[1]
            if totalRot[2]!=0.0:
                o+=rot[2]

            # add loops if any
            if prim.datarefs[dataref].loop>0:
                o+="%sANIM_keyframe_loop\t%d\n" % (tabs,prim.datarefs[dataref].loop)
                
            o+=staticTrans[1]
        
        return o

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
                            prim = XPlanePrimitive(child)
                            self.files[obj.name]['primitives'].append(prim)

                            # look for children
                            if len(child.children)>0:
                                self.addChildren(prim,obj.name)
                                
                        if child.type=="LAMP":
                            if debug:
                                print("\t "+child.name+": adding to list")
                            self.files[obj.name]['lights'].append(XPlaneLight(child))

                # apply further splitting by textures
                self.splitFileByTexture(obj)

    def addChildren(self,prim,file):
        obj = prim.object
        
        for child in obj.children:
            if debug:
                print("\t\t scanning "+child.name)

            if child.hide==False:
                if child.type=="MESH":
                    if debug:
                        print("\t\t "+child.name+": adding to list")
                    childPrim = XPlanePrimitive(child,prim)
                    prim.children.append(childPrim)

                    # add prim to file
                    self.files[file]['primitives'].append(childPrim)

                    # recursion
                    if len(child.children)>0:
                        self.addChildren(childPrim,file)
                        
        

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