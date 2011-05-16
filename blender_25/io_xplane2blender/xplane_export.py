# File: xplane_export.py
# Defines Classes used to create OBJ files out of XPlane data types defined in <xplane_types.py>.

import os.path
import bpy
import os
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_types import *
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_ui import showError,showProgress
from io_utils import ImportHelper, ExportHelper

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
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self,file):
        self.vertices = []
        self.indices = []
        self.globalindex = 0
        self.writeObjects(file['objects'])

    # Method: getBakeMatrix
    # Returns the bake matrix of a <XPlaneObject>.
    # The bake matrix is the matrix the object vertices will be transformed with before they are written to the OBJ.
    # It depends on the object hierarchy and animation.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>
    #
    # Returns:
    #   Matrix - The bake matrix for this object.
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
                    if animatedParent!=obj.parent:
                        # bake rotation of the parent relative to the animated parent so we do not need to worry about it later
                        matrix = XPlaneCoords.relativeConvertedMatrix(obj.parent.getMatrix(True),animatedParent.getMatrix(True))
                        matrix = XPlaneCoords.convertMatrix(matrix.to_euler().to_matrix().to_4x4())
                    else:
                        matrix = XPlaneCoords.conversionMatrix()
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
                
        return matrix*XPlaneCoords.scaleMatrix(obj)

    # Method: writeObjects
    # Fills the <vertices> and <indices> from a list of <XPlaneObjects>.
    # This method works recursively on the children of each <XPlaneObject>.
    #
    # Parameters:
    #   list - list of <XPlaneObjects>.
    #
    # Todos:
    #   - optimize vertex-table by removing duplicates. This implise the reordering of the indices.
    def writeObjects(self,objects):
        for obj in objects:
            if obj.type == 'PRIMITIVE':
                obj.indices[0] = len(self.indices)

                # create a copy of the object mesh with modifiers applied and triangulated
                #mesh = self.getTriangulatedMesh(obj.object)
                mesh = obj.object.to_mesh(bpy.context.scene, True, "PREVIEW")

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

                        if bpy.context.scene.xplane.optimize:
                            #check for duplicates
                            index = self.getDupliVerticeIndex(vert,obj.indices[0])
                        else:
                            index = -1

                        if index==-1:
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
            else:
                obj.bakeMatrix = self.getBakeMatrix(obj)
                
            self.writeObjects(obj.children)

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
        if profile:
            profiler.start('XPlaneMesh.getDupliVerticeIndex')
            
        for i in range(startIndex,len(self.vertices)):
            match = True
            ii = 0
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

    # Method: getTriangulatedMesh
    # Returns a triangulated mesh from a given Blender object.
    #
    # Parameters:
    #   object - Blender object
    #
    # Returns:
    #   A Blender mesh
    #
    # Todos:
    #   - Does not remove temporarily created mesh/object yet.
    def getTriangulatedMesh(self,object):
        me_da = object.data.copy() #copy data
        me_ob = object.copy() #copy object
        #note two copy two types else it will use the current data or mesh
        me_ob.data = me_da
        bpy.context.scene.objects.link(me_ob)#link the object to the scene #current object location
        for i in bpy.context.scene.objects: i.select = False #deselect all objects
        me_ob.select = True
        bpy.context.scene.objects.active = me_ob #set the mesh object to current
        bpy.ops.object.mode_set(mode='EDIT') #Operators
        bpy.ops.mesh.select_all(action='SELECT')#select all the face/vertex/edge
        bpy.ops.mesh.quads_convert_to_tris() #Operators
        bpy.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT') # set it in object

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
        if profile:
            profiler.start('XPlaneMesh.writeVertices')

        o=''
        index = 0
        for v in self.vertices:
            # dump the vertex data
            o+="VT"
            for i in v:
                o+="\t%6.4f" % i
            if debug:
                o+='\t# %d' % index
            o+="\n"
            index+=1

        if profile:
            profiler.end('XPlaneMesh.writeVertices')

        return o

    # Method: writeIndices
    # Returns the OBJ indices table by itering <indices>.
    #
    # Returns:
    #   string - The OBJ indices table.
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

# Class: XPlaneLights
# Creates OBJ lights.
class XPlaneLights():
    # Property: lights
    # list - All ligths.
    lights = []

    # Property: indices
    # list - All light indices.
    indices = []

    # Property: globalindex
    # int - Current global light index.
    globalindex = 0

    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>
    def __init__(self,file):
        self.lights = []
        self.indices = []
        self.globalindex = 0
        
        for light in file['lights']:
            light.indices[0] = self.globalindex

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
            self.indices.append(self.globalindex)
            self.globalindex+=1

            light.indices[1] = self.globalindex

    # Method: writeLights
    # Returns the OBJ lights table by iterating <lights>.
    #
    # Returns:
    #   string - The OBJ lights table.
    def writeLights(self):
        o=''
        for l in self.lights:
            o+=l+'\n'
        return o

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
    def __init__(self,file):
        self.reseters = {
            'ATTR_light_level':'ATTR_light_level_reset',
            'ATTR_cockpit':'ATTR_no_cockpit',
            'ATTR_cockpit_region':'ATTR_no_cockpit',
            'ATTR_manip_drag_xy':'ATTR_manip_none',
            'ATTR_manip_drag_axis':'ATTR_manip_none',
            'ATTR_manip_command':'ATTR_manip_none',
            'ATTR_manip_command_axis':'ATTR_manip_none',
            'ATTR_manip_push':'ATTR_manip_none',
            'ATTR_manip_radio':'ATTR_manip_none',
            'ATTR_manip_toggle':'ATTR_manip_none',
            'ATTR_manip_delta':'ATTR_manip_none',
            'ATTR_manip_wrap':'ATTR_manip_none',
            'ATTR_draw_disable':'ATTR_draw_enable'
        }
        self.written = {}
        self.staticWritten = []
        self.file = file

    # Method: write
    # Returns the OBJ commands table.
    #
    # Returns:
    #   string - The OBJ commands table.
    def write(self):
        o=''
         
        # write down all objects
        for obj in self.file['objects']:
            o+=self.writeObject(obj,0)

        # write down all lights
        # TODO: write them in writeObjects instead to allow light animation and nesting
#        if len(self.file['lights'])>0:
#            o+="LIGHTS\t0 %d\n" % len(self.file['lights'])
            
        return o

    # Method: writeObject
    # Returns the commands for one <XPlaneObject>.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>.
    #   int animLevel - Level of animation.
    #
    # Returns:
    #   string - OBJ Commands for the "obj".
    def writeObject(self,obj,animLevel):
        if profile:
            profiler.start("XPlaneCommands.writeObject")
            
        o = ''
        
        animationStarted = False
        tabs = self.getAnimTabs(animLevel)

        if debug:
            o+="%s# %s: %s\n" % (tabs,obj.type,obj.name)

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

        if hasattr(obj,'attributes'):
            o+=self.writeReseters(obj,tabs)
            o+=self.writeCustomAttributes(obj,tabs)

        if hasattr(obj,'material'):
            o+=self.writeMaterial(obj,tabs)            

        # write cockpit attributes
        if self.file['parent'].cockpit and hasattr(obj,'cockpitAttributes'):
            o+=self.writeCockpitAttributes(obj,tabs)

        # rendering
        if hasattr(obj,'indices'):
            offset = obj.indices[0]
            count = obj.indices[1]-obj.indices[0]
            if obj.type=='PRIMITIVE':
                o+="%sTRIS\t%d %d\n" % (tabs,offset,count)
            elif obj.type=='LIGHT':
                o+="%sLIGHTS\t%d %d\n" % (tabs,offset,count)

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
    #
    # Returns:
    #   string or None if the command must not be written.
    def writeAttribute(self,attr,value):
        if value!=None:
            if value==True:
                o = '%s\n' % attr
            else:
                o = '%s\t%s\n' % (attr,value)
                
            if self.canWrite(attr,value):
                self.written[attr] = value
                return o
            else:
                return None
        else:
            return None

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

    # Method: writeMaterials
    # Returns the commands for a <XPlaneObject> material.
    #
    # Parameters:
    #   XPlaneObject obj - A <XPlaneObject>.
    #   string tabs - The indentation tabs.
    #
    # Returns:
    #   string - Commands
    def writeMaterial(self,obj,tabs):
        o = ''
        for attr in obj.material.attributes:
            line = self.writeAttribute(attr,obj.material.attributes[attr])
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
            line = self.writeAttribute(attr,obj.attributes[attr])

            # add reseter to own resters list
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
            line = self.writeAttribute(attr,obj.cockpitAttributes[attr])
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
        o = ''
        for attr in self.reseters:
            # only reset attributes that wont be written with this object again
            if attr not in obj.attributes and attr in self.written:
                o+=tabs+self.reseters[attr]+"\n"
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
            for value in obj.animAttributes[attr]:
                line = self.writeAttribute(attr,value)
            
                if line!=None:
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

#        print(obj.vectors)
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
                debugger.debug("%s keyframe %s@%d %s" % (keyframe.object.name,keyframe.index,keyframe.frame,keyframe.dataref))
            
        trans+="%sANIM_trans_end\n" % tabs
        rot[0]+="%sANIM_rotate_end\n" % tabs
        rot[1]+="%sANIM_rotate_end\n" % tabs
        rot[2]+="%sANIM_rotate_end\n" % tabs

        # ignore high precision changes that won't be written anyway
        totalTrans[0] = round(totalTrans[0],4)
        totalTrans[1] = round(totalTrans[1],4)
        totalTrans[2] = round(totalTrans[2],4)

        
        if obj.id not in self.staticWritten:
            o+=static['trans'][0]
            o+=static['rot'][0]
            o+=static['rot'][1]
            o+=static['rot'][2]
            self.staticWritten.append(obj.id)

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

# Class: XPlaneData
# Collects Blender data relevant for export and converts it to Classes from <xplane_types.py>.
# It handles multi-file export.
class XPlaneData():
    # Property: files
    # dict - Contains all files to be exported.
    files = {}

    # Constructor: __init__
    def __init__(self):
        self.files = {}

    # Method: getXPlaneLayer
    # Returns the corresponding <XPlaneLayer> for a Blender layer index.
    #
    # Parameters:
    #   int layer - The Blender layer index.
    #
    # Returns:
    #   XPlaneLayer - The <XPlaneLayer>.
    def getXPlaneLayer(self,layer):
        if len(bpy.context.scene.xplane.layers)>0:
            return bpy.context.scene.xplane.layers[layer]
        else:
            return None

    # Method: getFilenameFromXPlaneLayer
    # Returns the filename for a <XPlaneLayer>.
    # If no name was given by the user it will be generated by the following pattern: "layer_[index]".
    #
    # Paramters:
    #   XPlaneLayer xplaneLayer - A <XPlaneLayer>.
    #
    # Returns:
    #   string - The filename.
    def getFilenameFromXPlaneLayer(self,xplaneLayer):
        if xplaneLayer.name == "":
            filename = "layer_%s" % (str(xplaneLayer.index+1).zfill(2))
        else:
            filename = xplaneLayer.name

#        if xplaneLayer.cockpit:
#            filename +="_cockpit"

        return filename

    # Method: getActiveLayers
    # Returns indices of all active Blender layers.
    #
    # Returns:
    #   list - Indices of all active blender layers.
    def getActiveLayers(self):
        layers = []
        for i in range(0,len(bpy.context.scene.layers)):
            if bpy.context.scene.layers[i] and bpy.context.scene.xplane.layers[i].export:
                layers.append(i)

        return layers


    # Method: getObjectsByLayer
    # Returns all first level Objects of a Blender layer.
    #
    # Parameters:
    #   int layer - The Blender layer index.
    #
    # Returns:
    #   list - Blender Oobjects.
    def getObjectsByLayer(self,layer):
        objects = []
        for object in bpy.context.scene.objects:
            #only add top level objects that have no parents
            if (object.parent==None):
                for i in range(len(object.layers)):
                    if object.layers[i]==True and i == layer:
                        objects.append(object)

        return objects

    # Method: getEmptyFile
    # Returns an empty OBJ-file dict.
    #
    # Paramters:
    #   XPlaneLayer parent - The <XPlaneLayer> this file will be generated from.
    def getEmptyFile(self,parent):
        return {'objects':[],'lights':[],'lines':[],'primitives':[],'parent':parent}

    # Method: getChildObjects
    # Returns exportable Blender child objects.
    # If those are nested within bones or something else it will look recursive for objects.
    #
    # Parameters:
    #   parent - A Blender object to look for children in.
    #   list found - Used internally. Contains all already found objects.
    #
    # Returns:
    #   list - All found child objects.
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

    # Method: collect
    # Collects all exportable Blender objects from the scene in <files>.
    def collect(self):
        if profile:
            profiler.start("XPlaneData.collect")
        
        for layer in self.getActiveLayers():
            xplaneLayer = self.getXPlaneLayer(layer)
            if xplaneLayer:
                filename = self.getFilenameFromXPlaneLayer(xplaneLayer)
                self.files[filename] = self.getEmptyFile(xplaneLayer)
                self.collectObjects(self.getObjectsByLayer(layer),filename)
                #self.splitFileByTexture(xplaneLayer)
                
        if profile:
            profiler.end("XPlaneData.collect")

    # Method: collectBones
    # Generates and collects <XPlaneBones> from Blender bones.
    # Uses <collectBoneObjects>.
    #
    # Parameters:
    #   list bones - Blender bones.
    #   string filename - OBJ filename in <files>.
    #   parent - Blender object the bones are children of.
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

    # Method: collectBoneObjects
    # Collects all Childobjects of an <XPlaneBone>.
    #
    # Parameters:
    #   XPlaneBone xplaneBone - A <XPlaneBone>.
    #   string filename - OBJ filename in <files>.
    def collectBoneObjects(self,xplaneBone,filename):
        if xplaneBone.armature != None:
            for obj in xplaneBone.armature.object.children:
                if obj.parent_bone == xplaneBone.name:
                    self.collectObjects([obj],filename,xplaneBone)

    # Method: collectObjects
    # Generates and collects <XPlaneObjects> from Blender objects.
    #
    # Parameters:
    #   list - Blender objects
    #   string filename - OBJ filename in <files>.
    #   parent - None or the parent <XPlaneObject>.
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
                elif obj.type in ['EMPTY','CAMERA','SURFACE','CURVE','FONT','META','LATTICE'] and len(children)>0:
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

    # Method: getBone
    # Returns a bone from an armature.
    #
    # Parameters:
    #   armature - Blender armature.
    #   string name - Bone name.
    #
    # Returns:
    #   None, if bone could not be found or Blender bone.
    def getBone(self,armature,name):
        for bone in armature.bones:
            if bone.name == name:
                return bone
        return None

    # Method: splitFileByTexture
    # Splits <files> by textures. This is depricated as files/textures are now defined per layer.
    #
    # Todos:
    #   - not working with new nested export. Propably XPlane Layers must hold texture info?
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
    
# Class: XPlaneHeader
# Create an OBJ header.
class XPlaneHeader():
    # Property: version
    # OBJ format version

    # Property: mode
    # The OBJ file mode. ("default" or "cockpit"). This is currently not in use, I think.

    # Property: attributes
    # OrderedDict - Key value pairs of all Header attributes

    # Constructor: __init__
    #
    # Parameters:
    #   dict file - A file dict coming from <XPlaneData>.
    #   XPlaneMesh mesh - A <XPlaneMesh>.
    #   XPlaneLights lights - <XPlaneLights>
    #   int version - OBJ format version.
    def __init__(self,file,mesh,lights,version):
        import os
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
            self.attributes['TEXTURE'] = os.path.basename(file['parent'].texture)
        if file['parent'].texture_lit!='':
            self.attributes['TEXTURE_LIT'] = os.path.basename(file['parent'].texture_lit)
        if file['parent'].texture_normal!='':
            self.attributes['TEXTURE_NORMAL'] = os.path.basename(file['parent'].texture_normal)

        # get point counts
        tris = len(mesh.vertices)
        lines = 0
        lights = len(lights.lights)
        indices = len(mesh.indices)
        
        self.attributes['POINT_COUNTS'] = "%d\t%d\t%d\t%d" % (tris,lines,lights,indices)

        # add custom attributes
        for attr in file['parent'].customAttributes:
            self.attributes[attr.name] = attr.value

    # Method: write
    # Returns the OBJ header.
    #
    # Returns:
    #   string - OBJ header
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
        
# Class: ExportXPlane9
# Main Export class. Brings all parts together and creates the OBJ files.
class ExportXPlane9(bpy.types.Operator, ExportHelper):
    '''Export to XPlane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export XPlane Object'
    
    filepath = StringProperty(name="File Path", description="Filepath used for exporting the XPlane file(s)", maxlen= 1024, default= "")
    filename_ext = ''
    #check_existing = BoolProperty(name="Check Existing", description="Check and warn on overwriting existing files", default=True, options={'HIDDEN'})

    # Method: execute
    # Used from Blender when user invokes export.
    # Invokes the exporting.
    #
    # Parameters:
    #   context - Blender context object.
    def execute(self, context):
        global debug
        global profile
        global log
        global errors
        
        errors = False

        if context.scene.xplane.debug:
            debug = True
            if context.scene.xplane.profile:
                profile = True
            else:
                profile = False

            if context.scene.xplane.log:
                log = True
            else:
                log = False
        else:
            debug = False
            profile = False
            log = False

        if debug:
            debugger.start(log)

        if profile:
            profiler.start("ExportXPlane9")

        filepath = self.properties.filepath
        if filepath=='':
            filepath = bpy.context.blend_data.filepath

        filepath = os.path.dirname(filepath)
        #filepath = bpy.path.ensure_ext(filepath, ".obj")

        # check if X-Plane layers have been created
        if len(bpy.context.scene.xplane.layers) == 0:
            errors = True
            showError('You must create X-Plane layers first.')
            return {'FINISHED'}            

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
            showProgress(0.0,'Writing XPlane Object file(s) ...')
            if debug:
                debugger.debug("Writing XPlane Object file(s) ...")

            i = 0
            for file in data.files:
                o=''
                if (len(data.files[file]['objects'])>0 or len(data.files[file]['lights'])>0 or len(data.files[file]['lines'])>0):
                    showProgress((1/len(data.files))*i,'Writing %s' % file)

                    if profile:
                        profiler.start("ExportXPlane9 %s" % file)

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
                    errors=True
                    showError('No objects to export, aborting ...')
                    if debug:
                        debugger.debug("No objects to export, aborting ...")
                i+=1
        else:
            errors=True
            showError('No files to export, aborting ...')
            if debug:
                debugger.debug("No files to export, aborting ...")

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

        if errors==False:
            showProgress(1.0,'Done!')
        
        return {'FINISHED'}

    # Method: invoke
    # Used from Blender when user hits the Export-Entry in the File>Export menu.
    # Creates a file select window.
    #
    # Todos:
    #   - window does not seem to work on Mac OS. Is there something different in the py API?
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}