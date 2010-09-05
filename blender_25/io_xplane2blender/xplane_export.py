import os.path
import bpy
import struct
import os
from bpy.props import *
from collections import OrderedDict

debug = True

class XPlanePrimitive():
    def __init__(self,object):
        self.object = object            
        self.name = object.name
        self.indices = [0,0]
        self.material = XPlaneMaterial(self.object)
        self.animations = []
        self.commands = []

class XPlaneMaterial():
    def __init__(self,object):
        self.object = object

        # Material
        self.attributes = {"ATTR_diffuse_rgb":None,"ATTR_specular_rgb":None,"ATTR_emission_rgb":None,"ATTR_shiny_rat":None}

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


            # Texture and uv-coordinates
            self.texture = None
            if(len(mat.texture_slots)>0 and mat.texture_slots[0].use and mat.texture_slots[0].texture.type=="IMAGE"):
                tex =  mat.texture_slots[0].texture
                if(tex.image.file_format=='PNG'):
                    self.texture = os.path.basename(tex.image.filepath)

                if mat.texture_slots[0].texture_coords == 'UV':
                    self.uv_name = mat.texture_slots[0].uv_layer

    def write(self):
        o=''
        for attr in self.attributes:
            if self.attributes[attr]!=None:
                o+='%s\t%s\n' % (attr,self.attributes[attr])

        return o

class XPlaneFace():
    def __init__(self):
        self.vertices = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.normals = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.indices = [0,0,0]
        self.uvs = [(0.0,0.0),(0.0,0.0),(0.0,0.0)]

class XPlaneMesh():
    def __init__(self,primitives):
        self.vertices = []
        self.indices = []
        #self.faces = []

        # store the global index, as we are reindexing faces
        globalindex = 0
        
        for prim in primitives:
            prim.indices[0] = globalindex

            # store the world translation matrix
            matrix = prim.object.matrix_world

            # create a copy of the object mesh with modifiers applied
            mesh = prim.object.create_mesh(bpy.context.scene, True, "PREVIEW")

            # with the new mesh get uvFaces list
            uvFaces = self.getUVFaces(mesh,prim.material.uv_name)

            # convert faces to triangles
            tempfaces = []
            for i in range(0,len(mesh.faces)):
                if uvFaces != None:
                    tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],uvFaces[i]))
                else:
                    tempfaces.extend(self.faceToTrianglesWithUV(mesh.faces[i],None))

            for f in tempfaces:
                xplaneFace = XPlaneFace()
                for i in range(0,len(f['indices'])):
                    # get the original index
                    vindex = f['indices'][i]

                    # get the vertice from original mesh
                    v = mesh.vertices[vindex]
                    
                    # convert local to global coordinates
                    co = matrix * v.co
                    
                    # store face information alltogether in one struct
                    # swap y and z and invert x (right handed system)
                    xplaneFace.vertices[i] = (-co[0],co[2],co[1])
                    xplaneFace.normals[i] = (-v.normal[0],v.normal[2],v.normal[1])
                    xplaneFace.uvs[i] = (f['uv'][i][0],f['uv'][i][1])
                    xplaneFace.indices[i] = globalindex

                    self.vertices.append([-co[0],co[2],co[1],-v.normal[0],v.normal[2],v.normal[1],f['uv'][i][0],f['uv'][i][1]])
                    self.indices.append(globalindex)
                    globalindex+=1
                #self.faces.append(xplaneFace)
                
            prim.indices[1] = globalindex

        # TODO: go through all indices and check for double UVs to reduce vertice amount while remaping the indices
#        for i in range(0,len(self.indices)):
#            indexes = self.getUVDoubleVIndexes(i)
#            if len(indexes)>0:
#                
#            for index in indexes:
#                self.indices[]

        # reverse indices due to the inverted z axis
        self.indices.reverse()
            
    def getUVDoubleVIndexes(self,index):
        indexes = []

        v = self.vertices[index]

        for i in range(len(self.vertices)):
            if (self.vertices[i][6] == v[6] and self.vertices[i][7] == v[7]):
                indexes.append(i)

        return indexes

    def getUVFaces(self,mesh,uv_name):
        # get the uv_texture

        if len(mesh.uv_textures)>0:
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
            
        o+="\n"
        return o


class XPlaneCommands():
    def __init__(self,primitives):
        self.primitives = primitives

    def write(self):
        o=''
        # write down all objects and there materials
        for prim in self.primitives:
            if debug:
                o+="# %s\n" % prim.name
            o+=prim.material.write()
            offset = prim.indices[0]
            count = prim.indices[1]-prim.indices[0]
            o+="TRIS\t%d %d\n" % (offset,count)

        o+="\n"
        return o


class XPlaneData():
    def __init__(self):
        self.files = {}
    # collect all exportable objects from the scene
    def collect(self):
        for obj in bpy.context.scene.objects:
            if debug:
                print("scanning "+obj.name)
                
            if(obj.type=="EMPTY" and obj.xplane.exportChildren and obj.hide==False):
                if debug:
                    print(obj.name+": export children")

                self.files[obj.name] = []
                for child in obj.children:
                    if debug:
                        print("\t scanning "+child.name)

                    if child.hide==False and child.type=="MESH":
                        if debug:
                            print("\t "+child.name+": adding to list")
                        self.files[obj.name].append(XPlanePrimitive(child))
    

class XPlaneHeader():
    def __init__(self,primitives,mesh,version):
        self.version = version
        self.mode = "default"
        self.attributes = OrderedDict([("TEXTURE",None),
                        ("TEXTURE_LIT",None),
                        ("TEXTURE_NORMAL",None),
                        ("POINT_COUNTS",None),
                        ("slung_load_weight",None),
                        ("COCKPIT_REGION",None)])

        # set Texture
        if primitives[0].material.texture != None:
            tex = primitives[0].material.texture
            self.attributes['TEXTURE'] = tex
            self.attributes['TEXTURE_LIT'] = tex[0:-4]+'_LIT.png'
            self.attributes['TEXTURE_NORMAL'] = tex[0:-4]+'_NML.png'

        # get point counts
        tris = len(mesh.vertices)
        lines = 0
        lites = 0
        indices = len(mesh.indices)
        
        self.attributes['POINT_COUNTS'] = "%d\t%d\t%d\t%d" % (tris,lines,lites,indices)

    def write(self):
        # TODO: check if we are on MacOS and use 'A' then
        o = 'I\n' # line ending types (I = UNIX/DOS, A = MacOS)

        # version number
        if self.version>=8:
            o+='800\n'

        o+='OBJ\n\n'

        # attributes
        for attr in self.attributes:
            if self.attributes[attr]!=None:
                o+='%s\t%s\n' % (attr,self.attributes[attr])
        o+='\n'
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

        data = XPlaneData()
        data.collect()

        if len(data.files)>0:
            o=''
            for file in data.files:
                if len(data.files[file])>0:
                    mesh = XPlaneMesh(data.files[file])
                    header = XPlaneHeader(data.files[file],mesh,9)
                    commands = XPlaneCommands(data.files[file])
                    o+=header.write()
                    o+=mesh.writeVertices()
                    o+=mesh.writeIndices()
                    o+=commands.write()
                    write(os.path.join(filepath,file+'.obj'), o, context)
                else:
                    print("No objects to export, aborting ...")
        else:
            print("No objects to export, aborting ...")

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}


def write(filepath, output, context):
    '''Export Objects to XPlane Object file(s).'''
    print("Writing XPlane Object file(s) ...")
    print(output)
    # write the faces to a file
    file = open(filepath, "w")
    file.write(output)
    file.close()

