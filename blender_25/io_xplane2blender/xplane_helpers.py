import math
from mathutils import Matrix,Vector,Euler
from io_xplane2blender.xplane_config import *

class XPlaneDebugger():
    def __init__(self):
        self.log = False

    def start(self,log):
        import time
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

    def write(self,msg):
        file = open(self.logfile,"a")
        #file.seek(1,os.SEEK_END)
        file.write(msg)
        file.close()

    def debug(self,msg):
        print(msg)
        if self.log:
            self.write(msg+"\n")

    def exception(self,type,value,traceback):
        o = "Exception: "+type+"\n"
        o += "\t"+value+"\n"
        o += "\tTraceback: "+str(traceback)+"\n"
        self.write(o)

    def end(self):
        self.log = False
#        sys.excepthook = self.excepthook

class XPlaneProfiler():
    def __init__(self):
        self.times = {}

    def start(self,name):
        from time import time
        self.times = {}
        
        if name in self.times:
            if self.times[name][3]:
                self.times[name][0] = time()
                self.times[name][3] = False

            self.times[name][2]+=1
        else:
            self.times[name] = [time(),0.0,1,False]

    def end(self,name):
        from time import time

        if name in self.times:
            self.times[name][1]+=time()-self.times[name][0]
            self.times[name][3] = True

    def getTime(self,name):
        return '%s: %6.4f sec (calls: %d)' % (name,self.times[name][1],self.times[name][2])

    def getTimes(self):
        _times = ''
        for name in self.times:
            _times+=self.getTime(name)+"\n"

        return _times


class XPlaneCoords():
    def __init__(self):
        pass

    @staticmethod
    def world(child,invert = False):
        matrix = XPlaneCoords.convertMatrix(child.matrix_world,invert)
        return XPlaneCoords.fromMatrix(matrix)

    @staticmethod
    def local(child,parent = None,invert = False):
        if parent!=None:
            matrix = XPlaneCoords.relativeConvertedMatrix(child,parent,invert)
        else:
            matrix = XPlaneCoords.convertMatrix(child.matrix_local,invert)
        return XPlaneCoords.fromMatrix(matrix)

    @staticmethod
    def angle(rot):
        return [math.degrees(rot[0]),math.degrees(rot[1]),math.degrees(rot[2])]

    @staticmethod
    def convert(co,scale = False):
        if (scale):
            return [co[0],co[2],co[1]]
        else:
            return [-co[0],co[2],co[1]]

    @staticmethod
    def relativeMatrix(child,parent):
        return child.matrix_world * parent.matrix_world.copy().invert()

    def relativeConvertedMatrix(child_matrix,parent_matrix, invert = False):
        return XPlaneCoords.convertMatrix(parent_matrix.copy().invert()*child_matrix,invert)

    @staticmethod
    def conversionMatrix(invert = False):
        if invert:
            return Matrix.Rotation(math.radians(-90),4,'X').invert()
        else:
            return Matrix.Rotation(math.radians(-90),4,'X')

    @staticmethod
    def convertMatrix(matrix,invert = False):
        return XPlaneCoords.conversionMatrix(invert)*matrix

    @staticmethod
    def fromMatrix(matrix):
        loc = matrix.translation_part()
        rot = matrix.rotation_part().to_euler("XZY")
        # re-add 90° to X
        rot.x=math.radians(math.degrees(rot.x)+90)
        scale = matrix.scale_part()
        coords = {'location':loc,'rotation':rot,'scale':scale,'angle':XPlaneCoords.angle(rot)}
        return coords

    @staticmethod
    def vectorsFromMatrix(matrix):
        rot = matrix.rotation_part().to_euler("XZY")
        # re-add 90° on x-axis
        rot.x=math.radians(math.degrees(rot.x)+90)

        vx = Vector((1.0,0.0,0.0)).rotate(Vector((1,0,0)),rot.x).rotate(Vector((0,1,0)),rot.y).rotate(Vector((0,0,1)),rot.z)
        vy = Vector((0.0,1.0,0.0)).rotate(Vector((1,0,0)),rot.x).rotate(Vector((0,1,0)),rot.y).rotate(Vector((0,0,1)),rot.z)
        vz = Vector((0.0,0.0,1.0)).rotate(Vector((1,0,0)),rot.x).rotate(Vector((0,1,0)),rot.y).rotate(Vector((0,0,1)),rot.z)
        vectors = (vx,vy,vz)
        return vectors