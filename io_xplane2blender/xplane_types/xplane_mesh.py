import bpy
from ..xplane_config import getDebug, getDebugger
from ..xplane_helpers import floatToStr
from .xplane_face import XPlaneFace

# Class: XPlaneMesh
# Creates the OBJ meshes.
class XPlaneMesh():
    # Property: vertices
    # list - contains all mesh vertices
    vertices = []

    # Property: indices
    # list - contains all face indices
    indices = []

    # Property: globalindex
    # int - Stores the current global vertex index.
    globalindex = 0

    # Constructor: __init__
    def __init__(self):
        self.vertices = []
        self.indices = []
        self.faces = []
        self.globalindex = 0
        self.debug = []

    # Method: collectXPlaneObjects
    # Fills the <vertices> and <indices> from a list of <XPlaneObjects>.
    # This method works recursively on the children of each <XPlaneObject>.
    #
    # Parameters:
    #   list xplaneObjects - list of <XPlaneObjects>.
    def collectXPlaneObjects(self, xplaneObjects):
        debug = getDebug()
        debugger = getDebugger()

        for xplaneObject in xplaneObjects:
            if xplaneObject.type == 'PRIMITIVE':
                xplaneObject.indices[0] = len(self.indices)
                first_vertice_of_this_xplaneObject = len(self.vertices)

                # create a copy of the xplaneObject mesh with modifiers applied and triangulated
                mesh = xplaneObject.blenderObject.to_mesh(bpy.context.scene, True, "PREVIEW")

                # now get the bake matrix
                # and bake it to the mesh
                xplaneObject.bakeMatrix = xplaneObject.xplaneBone.getBakeMatrix()
                mesh.transform(xplaneObject.bakeMatrix)

                if hasattr(mesh, 'polygons'): # BMesh
                    mesh.update(calc_tessface=True)
                    mesh.calc_tessface()
                    mesh_faces = mesh.tessfaces
                else:
                    mesh_faces = mesh.faces

                # with the new mesh get uvFaces list
                uvFaces = self.getUVFaces(mesh, xplaneObject.material.uv_name)

                faces = []

                if debug:
                    d = {'name': xplaneObject.name,'obj_face': 0,'faces': len(mesh_faces),'quads': 0,'vertices': len(mesh.vertices),'uvs': 0}

                # convert faces to triangles
                if len(mesh_faces) > 0:
                    tempfaces = []

                    for i in range(0, len(mesh_faces)):
                        if uvFaces != None:
                            f = self.faceToTrianglesWithUV(mesh_faces[i], uvFaces[i])
                            tempfaces.extend(f)

                            if debug:
                                d['uvs'] += 1

                                if len(f) > 1:
                                    d['quads'] += 1

                        else:
                            f = self.faceToTrianglesWithUV(mesh_faces[i], None)
                            tempfaces.extend(f)

                            if debug:
                                if len(f) > 1:
                                    d['quads']+=1

                    if debug:
                        d['obj_faces'] = len(tempfaces)

                    for f in tempfaces:
                        xplaneFace = XPlaneFace()
                        l = len(f['indices'])

                        for i in range(0, l):
                            # get the original index but reverse order, as this is reversing normals
                            vindex = f['indices'][2 - i]

                            # get the vertice from original mesh
                            v = mesh.vertices[vindex]
                            co = v.co

                            if f['original_face'].use_smooth: # use smoothed vertex normal
                                vert = [
                                    co[0], co[2], -co[1],
                                    v.normal[0], v.normal[2], -v.normal[1],
                                    f['uv'][i][0], f['uv'][i][1]
                                ]
                            else: # use flat face normal
                                vert = [
                                    co[0], co[2], -co[1],
                                    f['original_face'].normal[0], f['original_face'].normal[2], -f['original_face'].normal[1],
                                    f['uv'][i][0], f['uv'][i][1]
                                ]

                            if bpy.context.scene.xplane.optimize:
                                #check for duplicates
                                index = self.getDupliVerticeIndex(vert, first_vertice_of_this_xplaneObject)
                            else:
                                index = -1

                            if index == -1:
                                index = self.globalindex
                                self.vertices.append(vert)
                                self.globalindex += 1

                            # store face information in one struct
                            xplaneFace.vertices[i] = (vert[0], vert[1], vert[2])
                            xplaneFace.normals[i] = (vert[3], vert[4], vert[5])
                            xplaneFace.uvs[i] = (vert[6], vert[7])
                            xplaneFace.indices[i] = index

                            self.indices.append(index)

                        faces.append(xplaneFace)

                    # store the faces in the prim
                    xplaneObject.faces = faces
                    xplaneObject.indices[1] = len(self.indices)
                    self.faces.extend(faces)

                if debug:
                    d['start_index'] = xplaneObject.indices[0]
                    d['end_index'] = xplaneObject.indices[1]
                    self.debug.append(d)

        if debug:
            try:
                self.debug.sort(key=lambda k: k['obj_faces'],reverse=True)
            except:
                pass

            for d in self.debug:
                tris_to_quads = 1.0

                if not 'obj_faces' in d:
                    d['obj_faces'] = 0

                if d['faces'] > 0:
                    tris_to_quads = d['obj_faces'] / d['faces']

                debugger.debug('%s: faces %d | xplaneObject-faces %d | tris-to-quads ratio %6.2f | indices %d | vertices %d' % (d['name'],d['faces'],d['obj_faces'],tris_to_quads,d['end_index']-d['start_index'],d['vertices']))

            debugger.debug('POINT COUNTS: faces %d - vertices %d - indices %d' % (len(self.faces),len(self.vertices),len(self.indices)))

    # Method: getDupliVerticeIndex
    # Returns the index of a vertice duplicate if any.
    #
    # Parameters:
    #   v - The OBJ vertice.
    #   int startIndex - (default=0) From which index to start searching for duplicates.
    #
    # Returns:
    #   int - Index of the duplicate or -1 if none was found.
    def getDupliVerticeIndex(self,v,startIndex = 0):
        l = len(self.vertices)

        for i in range(startIndex, l):
            match = True
            ii = 0

            while ii < l:
                if self.vertices[i][ii] != v[ii]:
                    match = False
                    ii = l

                ii += 1

            if match:
                return i

        return -1


    # Method: getUVFaces
    # Returns Blender the UV faces of a Blender mesh.
    #
    # Parameters:
    #   mesh - Blender mesh
    #   string uv_name - Name of the uv layer to use. If not given the first layer will be used.
    #
    # Returns:
    #   None if no UV faces could be found or the Blender UV Faces.
    def getUVFaces(self,mesh,uv_name):
        # get the uv_texture
        if hasattr(mesh,'polygons'): # BMesh
            uv_textures = mesh.tessface_uv_textures
        else:
            uv_textures = mesh.uv_textures

        if (uv_name != None and len(uv_textures) > 0):
            uv_layer = None

            if uv_name=="":
                uv_layer = uv_textures[0]
            else:
                i = 0

                while uv_layer == None and i < len(uv_textures):
                    if uv_textures[i].name == uv_name:
                        uv_layer = uv_textures[i]

                    i += 1

            if uv_layer != None:
                return uv_layer.data
            else:
                return None

        else:
            return None

    # Method: getTriangulatedMesh
    # Returns a triangulated mesh from a given Blender xplaneObjectect.
    #
    # Parameters:
    #   blenderObject - Blender Object
    #
    # Returns:
    #   A Blender mesh
    #
    # Todos:
    #   - Does not remove temporarily created mesh/xplaneObjectect yet.
    def getTriangulatedMesh(self, blenderObject):
        me_da = blenderObject.data.copy() #copy data
        me_ob = blenderObject.copy() #copy xplaneObjectect
        #note two copy two types else it will use the current data or mesh
        me_ob.data = me_da
        bpy.context.scene.objects.link(me_ob) #link the xplaneObjectect to the scene #current xplaneObjectect location

        for i in bpy.context.scene.objects: i.select = False #deselect all xplaneObjectects

        me_ob.select = True
        bpy.context.scene.objects.active = me_ob #set the mesh xplaneObjectect to current
        bpy.ops.object.mode_set(mode='EDIT') #Operators
        bpy.ops.mesh.select_all(action='SELECT')#select all the face/vertex/edge
        bpy.ops.mesh.quads_convert_to_tris() #Operators
        bpy.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT') # set it in xplaneObjectect

        mesh = me_ob.to_mesh(bpy.context.scene, True, "PREVIEW")

        bpy.context.scene.objects.unlink(me_ob)
        return mesh

    # Method: faceToTrianglesWithUV
    # Converts a Blender face (3 or 4 sided) into one or two 3-sided faces together with the texture coordinates.
    #
    # Parameters:
    #   face - A Blender face.
    #   uv - UV coordiantes of a Blender UV face.
    #
    # Returns:
    #   list - [{'uv':[[u1,v1],[u2,v2],[u3,v3]],'indices':[i1,i2,i3]},..] In length 1 or 2.
    def faceToTrianglesWithUV(self,face,uv):
        triangles = []
        #inverse uv's as we are inversing face indices later
        if len(face.vertices) == 4: #quad
            if uv != None:
                triangles.append( {"uv":[[uv.uv3[0], uv.uv3[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv1[0], uv.uv1[1]]], "indices":[face.vertices[0], face.vertices[1], face.vertices[2]],'original_face':face})
                triangles.append( {"uv":[[uv.uv1[0], uv.uv1[1]], [uv.uv4[0], uv.uv4[1]], [uv.uv3[0], uv.uv3[1]]], "indices":[face.vertices[2], face.vertices[3], face.vertices[0]],'original_face':face})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[face.vertices[0], face.vertices[1], face.vertices[2]],'original_face':face})
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":[face.vertices[2], face.vertices[3], face.vertices[0]],'original_face':face})

        else:
            if uv != None:
                triangles.append( {"uv":[[uv.uv3[0], uv.uv3[1]], [uv.uv2[0], uv.uv2[1]], [uv.uv1[0], uv.uv1[1]]], "indices":face.vertices,'original_face':face})
            else:
                triangles.append( {"uv":[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]], "indices":face.vertices,'original_face':face})

        return triangles

    # Method: faceValues
    # Returns the converted vertices of a face.
    #
    # Parameters:
    #   face - A Blender face.
    #   mesh - A Blender mesh.
    #   Matrix matrix - The conversion matrix.
    #
    # Returns:
    #   list - List of vertices.
    def faceValues(self,face, mesh, matrix):
        fv = []

        for verti in face.vertices_raw:
            fv.append(matrix * mesh.vertices[verti].co)

        return fv

    # Method: writeVertices
    # Returns the OBJ vertex table by iterating <vertices>.
    #
    # Returns:
    #   string - The OBJ vertex table.
    def writeVertices(self):
        debug = getDebug()
        o = ''
        index = 0

        for v in self.vertices:
            # dump the vertex data
            o += "VT"

            for i in v:
                o += "\t%s" % floatToStr(i)

            if debug:
                o += '\t# %d' % index

            o += "\n"
            index += 1

        return o

    # Method: writeIndices
    # Returns the OBJ indices table by itering <indices>.
    #
    # Returns:
    #   string - The OBJ indices table.
    def writeIndices(self):
        o=''
        group = []

        for i in self.indices:
            # append index to group if we havent collected 10 yet
            if len(group) < 10:
                group.append(i)
            else:
                # dump 10 indices at once
                o += 'IDX10'

                for ii in group:
                    o += "\t%d" % ii

                o += "\n"
                group = []
                group.append(i)

        # dump overhanging indices
        for i in group:
            o += "IDX\t%d\n" % i

        return o

    def write(self):
        o = ''
        o += self.writeVertices()
        o += '\n'
        o += self.writeIndices()

        return o
