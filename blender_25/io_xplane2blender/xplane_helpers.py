import math
from mathutils import Matrix
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
        rot = matrix.rotation_part().to_euler("XZY")
        scale = matrix.scale_part()
        return {'location':loc,'rotation':rot,'scale':scale,'angle':self.angle(rot)}

    def localLocation(self,parent):
        matrix = self.relativeConvertedMatrix(parent)
        loc = matrix.translation_part()
        return loc #self.convert([loc[0],loc[1],loc[2]])

    def localRotation(self,parent):
        matrix = self.relativeConvertedMatrix(parent)
        rot = matrix.rotation_part().to_euler("XYZ")
        return rot #self.convert([rot[0],rot[1],rot[2]])

    def localAngle(self,parent):
        return self.angle(self.localRotation())

    def localScale(self,parent):
        matrix = self.relativeConvertedMatrix(parent)
        scale = matrix.scale_part()
        return scale #self.convert([scale[0],scale[1],scale[2]],True)

    def local(self,parent = None):
        if parent!=None:
            matrix = self.relativeConvertedMatrix(parent)
        else:
            matrix = self.convertMatrix(self.object.matrix_local)
        loc = matrix.translation_part()
        rot = matrix.rotation_part().to_euler("XYZ")
        scale = matrix.scale_part()
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

    def relativeConvertedMatrix(self,parent):
        return XPlaneCoords.convertMatrix(self.object.matrix_world) * XPlaneCoords.convertMatrix(parent.matrix_world.copy().invert())

    @staticmethod
    def convertMatrix(matrix):
        import mathutils
        rmatrix = Matrix.Rotation(math.radians(-90),4,'X')
        return rmatrix*matrix