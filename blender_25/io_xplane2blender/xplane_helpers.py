# File: xplane_helpers.py
# Defines Helpers

import math
from mathutils import Matrix,Vector,Euler
from io_xplane2blender.xplane_config import *

# Class: XPlaneDebugger
# Prints debugging information and optionally logs them to a file.
class XPlaneDebugger():
    # Property: log
    # bool - Set to True to enable logfile. Default is False.
    log = False
    
    # Constructor: __init__
    def __init__(self):
        pass

    # Method: start
    # Starts the debugger and creates a log file, if logging is enabled.
    #
    # Parameters:
    #   bool log - Set True if log file should be written, else False
    def start(self,log):
        import time
        import os
        import bpy
#        import sys
#        import logging

        self.log = log

        if self.log:
            (name,ext) = os.path.splitext(bpy.context.blend_data.filepath)
            dir = os.path.dirname(bpy.context.blend_data.filepath)
            self.logfile = os.path.join(dir,name+'_'+time.strftime("%y-%m-%d-%H-%M-%S")+'_xplane2blender.log')

            # touch the file
            file = open(self.logfile,"w");
            file.close()

#            self.excepthook = sys.excepthook
#            sys.excepthook = self.exception
#            self.logger = logging.getLogger()
#            self.streamHandler = logging.StreamHandler()
#            self.fileHandler = logging.FileHandler(self.logfile)
#            self.logger.addHandler(self.streamHandler)

    # Method: write
    # Writes a message to the logfile.
    #
    # Parameters:
    #   string msg - The message to write.
    def write(self,msg):
        file = open(self.logfile,"a")
        #file.seek(1,os.SEEK_END)
        file.write(msg)
        file.close()

    # Method: debug
    # Prints out a message and also writes it to the logfile if logging is enabled.
    #
    # Parameters:
    #   string msg - The message to output.
    def debug(self,msg):
        print(msg)
        if self.log:
            self.write(msg+"\n")

    # Method: exception
    # Experimental exception handler. Not working yet.
    def exception(self,type,value,traceback):
        o = "Exception: "+type+"\n"
        o += "\t"+value+"\n"
        o += "\tTraceback: "+str(traceback)+"\n"
        self.write(o)

    # Method: end
    # Ends the debugging session.
    def end(self):
        self.log = False
#        sys.excepthook = self.excepthook


# Class: XPlaneProfiler
# Stores profiling information of processes.
class XPlaneProfiler():
    # Property: times
    # dict of stored times used internally.
    times = {}

    # Constructor: __init__
    def __init__(self):
        self.times = {}

    # Method: def
    # Starts profiling of a process. If the process has already started profiling, the process counter will be increased.
    #
    # Parameters:
    #   string name - Name of the process.
    def start(self,name):
        from time import time
        
        if name in self.times:
            if self.times[name][3]:
                self.times[name][0] = time()
                self.times[name][3] = False

            self.times[name][2]+=1
        else:
            self.times[name] = [time(),0.0,1,False]

    # Method: end
    # Ends profiling of a process.
    #
    # Parameters:
    #   string name - Name of the process.
    def end(self,name):
        from time import time

        if name in self.times:
            self.times[name][1]+=time()-self.times[name][0]
            self.times[name][3] = True

    # Method: getTime
    # Returns the time and call number for a process.
    #
    # Parameters:
    #   string name - Name of the process.
    #
    # Returns:
    #   string - Information about the the process.
    def getTime(self,name):
        return '%s: %6.4f sec (calls: %d)' % (name,self.times[name][1],self.times[name][2])

    # Method: getTimes
    # Returns the times and call numbers of all processes. Uses <getTime> internally.
    #
    # Returns:
    #   string - Information about the processes.
    def getTimes(self):
        _times = ''
        for name in self.times:
            _times+=self.getTime(name)+"\n"

        return _times

# Class: XPlaneCoords
# Converts Blender coordinates into X-Plane coordinates.
class XPlaneCoords():
    # Constructor: __init__
    def __init__(self):
        pass

    # Method: world
    # Returns converted object world coordinates.
    #
    # Parameters:
    #   child - A Blender object
    #   bool invert - (default=False) True if the internaly used matrix should be inverted.
    #
    # Returns:
    #   dict - {'location','rotation','scale','angle'} With world X-Plane coordinates.
    @staticmethod
    def world(child,invert = False):
        matrix = XPlaneCoords.convertMatrix(child.matrix_world,invert)
        return XPlaneCoords.fromMatrix(matrix)

    # Method: local
    # Returns converted object local coordinates.
    #
    # Parameters:
    #   child - Blender object, the child object.
    #   parent - Blender object, the parent object or None. If this is set, coordinates will be calculated relative to the parent.
    #   bool invert - (default=False) True if the internaly used matrix should be inverted.
    #
    # Returns:
    #   dict - {'location':[x,y,z],'rotation':[x,y,z],'scale':[x,y,z],'angle':[x,y,z]} With world X-Plane coordinates.
    @staticmethod
    def local(child,parent = None,invert = False):
        if parent!=None:
            matrix = XPlaneCoords.relativeConvertedMatrix(child,parent,invert)
        else:
            matrix = XPlaneCoords.convertMatrix(child.matrix_local,invert)
        return XPlaneCoords.fromMatrix(matrix)

    # Method: angle
    # Returns angles of a rotation.
    #
    # Parameters:
    #   Euler rot - Euler rotation.
    #
    # Returns:
    #   list - [x,y,z] With angles.
    @staticmethod
    def angle(rot):
        return [math.degrees(rot[0]),math.degrees(rot[1]),math.degrees(rot[2])]

    # Method: convert
    # Converts Blender Vector (x,y,z) into X-Plane Vector
    #
    # Parameters:
    #   Vector co - Blender Vector
    #   bool scale - (default=False) Don't know anymore.
    #
    # Returns:
    #   list - [x,y,z] With converted "co".
    @staticmethod
    def convert(co,scale = False):
        if (scale):
            return [co[0],co[2],co[1]]
        else:
            return [-co[0],co[2],co[1]]

    # Method: relativeMatrix
    # Get's the relative matrix between a child and a parent objects matrixes.
    #
    # Parameters:
    #   Matrix child - Child matrix.
    #   Matrix parent - Parent matrix.
    #
    # Returns:
    #   Matrix - Relative matrix.
    @staticmethod
    def relativeMatrix(child,parent):
        return child.matrix_world * parent.matrix_world.copy().invert()

    # Method: relativeConvertedMatrix
    # Get's the relative and converted matrix between a child and a parent objects matrixes. This is not used anymore, as it was producing wrong results.
    #
    # Parameters:
    #   Matrix child_matrix - Child matrix.
    #   Matrix parent_matrix - Parent matrix.
    #   bool invert - (default=False) True if the internaly used matrix should be inverted.
    #
    # Returns:
    #   Matrix - A relative converted matrix.
    def relativeConvertedMatrix(child_matrix,parent_matrix, invert = False):
        return XPlaneCoords.convertMatrix(parent_matrix.copy().inverted()*child_matrix,invert)

    # Method: conversionMatrix
    # Returns the conversion matrix used to convert Blender matrixes to X-Plane matrixes. Basically this matrix contains a rotation of -90° along the x-axis.
    #
    # Parameters:
    #   bool invert - (default=False) True if the internaly used matrix should be inverted.
    #
    # Returns:
    #   Matrix - Conversion matrix.
    @staticmethod
    def conversionMatrix(invert = False):
        if invert:
            return Matrix.Rotation(math.radians(-90),4,'X').inverted()
        else:
            return Matrix.Rotation(math.radians(-90),4,'X')

    # Method: convertMatrix
    # Converts a matrix using <conversionMatrix>.
    #
    # Parameters:
    #   Matrix matrix - The matrix to convert.
    #   bool invert - (default=False) True if the internaly used matrix should be inverted.
    #
    # Returns:
    #   Matrix - The converted matrix.
    @staticmethod
    def convertMatrix(matrix,invert = False):
        return XPlaneCoords.conversionMatrix(invert)*matrix

    # Method: fromMatrix
    # Returns coordinates for a matrix.
    #
    # Parameters:
    #   Matrix matrix - The matrix.
    #
    # Returns:
    #   dict - {'location':[x,y,z],'rotation':[x,y,z],'scale':[x,y,z],'angle':[x,y,z]} With world X-Plane coordinates.
    @staticmethod
    def fromMatrix(matrix,scaleLoc = False):
        loc = matrix.to_translation()
        rot = matrix.to_euler("XZY")
        # re-add 90° to X
        rot.x=math.radians(math.degrees(rot.x)+90)
        scale = matrix.to_scale()

        # apply scale to location
        if scaleLoc:
            loc.x = loc.x * scale.x
            loc.y = loc.y * scale.y
            loc.z = loc.z * scale.z
        coords = {'location':loc,'rotation':rot,'scale':scale,'angle':XPlaneCoords.angle(rot)}
        return coords

    # Method: vectorsFromMatrix
    # Returns directional vectors from a given matrix.
    #
    # Parameters:
    #   Matrix matrix - The matrix.
    #
    # Returns:
    #   Vector of vectors - (vx,vy,vz)
    @staticmethod
    def vectorsFromMatrix(matrix):
        rot = matrix.to_euler("XYZ")
        # re-add 90° on x-axis
        rot.x=math.radians(math.degrees(rot.x)+90)
        
        vx = Vector((1.0,0.0,0.0))
        vy = Vector((0.0,1.0,0.0))
        vz = Vector((0.0,0.0,1.0))
        vx.rotate(rot)
        vy.rotate(rot)
        vz.rotate(rot)
        vectors = (vx,vy,vz)
        return vectors

    @staticmethod
    def convertVector(v):
        rot = XPlaneCoords.conversionMatrix().to_euler('XYZ')
        # re-add 90° on x-axis
        rot.x=math.radians(math.degrees(rot.x)+90)

        vrot = v.copy()
        vrot.rotate(rot)
        return vrot

    # Method: getScaleMatrix
    # Returns a matrix with the global scale of a given object
    #
    # Paremters:
    #   object - A <XPlaneObject>
    #
    # Returns:
    #   matrix - Matrix with global object scale or None if the object is at root level.
    @staticmethod
    def scaleMatrix(object,convert = False, noParent = True):
        import mathutils
        if noParent:
            if object.parent:
                if convert:
                    scale = XPlaneCoords.convertMatrix(object.getMatrix(True)).to_scale()
                else:
                    scale = object.getMatrix(True).to_scale()
                matrix = Matrix()
                matrix[0][0] = scale.x
                matrix[1][1] = scale.y
                matrix[2][2] = scale.z

                # FIXME: armature scale is not taken into account so add it, however this could be a Blender bug or a misunderstanding
                if object.parent and object.parent.type=='BONE':
                    if convert:
                        scale = XPlaneCoords.convertMatrix(object.parent.armature.getMatrix(True)).to_scale()
                    else:
                        scale = object.parent.armature.getMatrix(True).to_scale()
                    matrix[0][0]*=scale.x
                    matrix[1][1]*=scale.y
                    matrix[2][2]*=scale.z
                return matrix
            else:
                return Matrix.Scale(1,4,Vector((1,1,1)))
        else:
            if convert:
                scale = XPlaneCoords.convertMatrix(object.getMatrix(True)).to_scale()
            else:
                scale = object.getMatrix(True).to_scale()
            matrix = Matrix()
            matrix[0][0] = scale.x
            matrix[1][1] = scale.y
            matrix[2][2] = scale.z
            return matrix
