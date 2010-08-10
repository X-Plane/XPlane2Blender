#------------------------------------------------------------------------
# X-Plane import/output utility classes for blender 2.43 or above
#
# Copyright (c) 2005,2006,2007 Jonathan Harris
#
# Mail: <x-plane@marginal.org.uk>
# Web:  http://marginal.org.uk/x-planescenery/
#
# See XPlane2Blender.html for usage.
#
# This software is licensed under a Creative Commons License
#   Attribution-Noncommercial-Share Alike 3.0:
#
#   You are free:
#    * to Share - to copy, distribute and transmit the work
#    * to Remix - to adapt the work
#
#   Under the following conditions:
#    * Attribution. You must attribute the work in the manner specified
#      by the author or licensor (but not in any way that suggests that
#      they endorse you or your use of the work).
#    * Noncommercial. You may not use this work for commercial purposes.
#    * Share Alike. If you alter, transform, or build upon this work,
#      you may distribute the resulting work only under the same or
#      similar license to this one.
#
#   For any reuse or distribution, you must make clear to others the
#   license terms of this work.
#
# This is a human-readable summary of the Legal Code (the full license):
#   http://creativecommons.org/licenses/by-nc-sa/3.0/
#
#
# 2005-03-01 v2.00
#  - New file split out from other XPlane*.py scripts.
#
# 2006-07-11 v2.25
#  - Fix for comparing lines and lights.
#  - Increased output precision to 4 decimals for really small objects.
#  - Reduced duplicate vertex limit to 0.0001 for really small objects.
#  - Reduced duplicate UV limit to 4 pixels in 1024.
#
# 2007-12-02 v3.00
#  - Support for DDS textures.
#  - Support for v9 datarefs
#  - Ignore muliplayer to reduce number of ambiguous datarefs.
#  - Fix for zero-scaled objects.
#
# 2007-12-21 v3.05
#  - Support for cockpit panel regions.
#  - Reduced duplicate UV limit to 0.0004 = 1 pixel in 2048.
#
# 2008-04-08 v3.09
#  - Don't regenerate panel region images on load, pack them instead.
#
# 2010-03-21 v3.10
#  - Support manipulator functionality

import sys
from math import sqrt, sin, cos
from os.path import exists, join
import Blender
from Blender import Registry, Types, Image, Mesh, Object, Scene, Text, Window
from Blender.Mathutils import Matrix, Vector, Euler

class Vertex:
    LIMIT=0.0001	# max distance between vertices for them to be merged
    ROUND=4	# Precision

    def __init__ (self, x, y=None, z=None, mm=None):
        self.faces=[]	# indices into face array

        if isinstance(x, Types.vectorType) or isinstance(x, Types.eulerType):
            mm=y
            z=x.z
            y=x.y
            x=x.x
        elif isinstance(x, Types.NMVertType):
            mm=y
            z=x.co[2]
            y=x.co[1]
            x=x.co[0]
        elif isinstance(x, list):
            mm=y
            z=x[2]
            y=x[1]
            x=x[0]
	elif y==None or z==None:
            raise TypeError

        if not mm:
            self.x=x
            self.y=y
            self.z=z
        else:	# apply scale, translate and swap y and z axes
            self.x=round(mm[0][0]*x + mm[1][0]*y + mm[2][0]*z + mm[3][0],
                         Vertex.ROUND)
            self.y=round(mm[0][2]*x + mm[1][2]*y + mm[2][2]*z + mm[3][2],
                         Vertex.ROUND)
            self.z=-round(mm[0][1]*x + mm[1][1]*y + mm[2][1]*z + mm[3][1],
                          Vertex.ROUND)

    def __str__ (self):
        return "%9.4f %9.4f %9.4f" % (self.x, self.y, self.z)

    def __add__ (self, right):
        return Vertex(self.x+right.x, self.y+right.y, self.z+right.z)

    def __sub__ (self, right):
        return Vertex(self.x-right.x, self.y-right.y, self.z-right.z)

    def __mul__ (self, right):
        return Vertex(self.x*right, self.y*right, self.z*right)

    def __rmul__ (self, left):
        return Vertex(self.x*left, self.y*left, self.z*left)

    def __div__ (self, right):
        return Vertex(self.x/right, self.y/right, self.z/right)

    def __neg__ (self):
        return Vertex(-self.x, -self.y, -self.z)

    def equals (self, v, fudge=LIMIT):
        if ((abs(self.x-v.x) <= fudge) and
            (abs(self.y-v.y) <= fudge) and
            (abs(self.z-v.z) <= fudge)):
            return True
        else:
            return False

    def toVector (self, n):
        v=[self.x, self.y]
        if n==3:
            v.append(self.z)
        elif n==4:
            v.extend([self.z, 1.0])
        else:
            raise AttributeError
        return Vector(v)

    def toEuler (self, n):
        v=[self.x, self.y]
        if n==3:
            v.append(self.z)
        elif n==4:
            v.extend([self.z, 1.0])
        else:
            raise AttributeError
        return Euler(v)

    def normalize (self):
        hyp=sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        return self/hyp

    def addFace (self, v):
        self.faces.append(v)

    def totuple(self):
        return (round(self.x,Vertex.ROUND), round(self.y,Vertex.ROUND), round(self.z,Vertex.ROUND))


class UV:
    LIMIT=0.0004	# <= 1 pixel in 2048
    ROUND=4

    def __init__(self, s, t=None):
        if isinstance(s, Types.vectorType):
            self.s=s.x
            self.t=s.y
        elif isinstance(s, list):
            self.s=s[0]
            self.t=s[1]
        elif isinstance(s, tuple):
            (self.s,self.t)=s
        elif t!=None:
            self.s=s
            self.t=t
        else:
            raise TypeError

    def __str__(self):
        return "%-6s %-6s" % (round(self.s,UV.ROUND), round(self.t,UV.ROUND))

    def __add__ (self, right):
        return UV(self.s+right.s, self.t+right.t)

    def __sub__ (self, right):
        return UV(self.s-right.s, self.t-right.t)

    def __mul__ (self, right):
        return UV(self.s*right.s, self.t*right.t)

    def __div__ (self, right):
        if isinstance(right, int):
            return UV(self.s/right, self.t/right)
        else:
            return UV(self.s/right.s, self.t/right.t)

    def equals (self, uv):
        if ((abs(self.s-uv.s) <= UV.LIMIT) and
            (abs(self.t-uv.t) <= UV.LIMIT)):
            return 1
        else:
            return 0


class Face:
    # Flags in v7 sort order
    HARD=1
    TWOSIDE=2
    FLAT=4
    ALPHA=8	# Must be 2nd last
    PANEL=16	# Must be last
    NPOLY=32	# Must really be last
    BUCKET=HARD|TWOSIDE|FLAT|ALPHA|PANEL|NPOLY	# For v7 export

    def __init__ (self):
        self.v=[]
        self.uv=[]
        self.flags=0
        self.kosher=0		# Hack! True iff panel and within 1024x768
        self.region=None	# for import

    # for debug only
    def __str__ (self):
        s="<"
        for v in self.v:
            s=s+("[%s]" % v)
        return s+">"

    def addVertex (self, v):
        self.v.append(v)

    def addUV (self, uv):
        self.uv.append(uv)

    def removeDuplicateVertices(self):
        i=0
        while i < len(self.v)-1:
            j=i+1
            while j < len(self.v):
                if self.v[i].equals(self.v[j]) and self.uv[i].equals(self.uv[j]):
                    self.v[i].x=round((self.v[i].x+self.v[j].x)/2,Vertex.ROUND)
                    self.v[i].y=round((self.v[i].y+self.v[j].y)/2,Vertex.ROUND)
                    self.v[i].z=round((self.v[i].z+self.v[j].z)/2,Vertex.ROUND)
                    del self.v[j]
                    self.uv[i].s=round((self.uv[i].s+self.uv[j].s)/2,UV.ROUND)
                    self.uv[i].t=round((self.uv[i].t+self.uv[j].t)/2,UV.ROUND)
                    del self.uv[j]
                else:
                    j=j+1
            i=i+1
        return len(self.v)


class PanelRegionHandler:
    NAME='PanelRegionHandler'
    REGIONCOUNT=4	# X-Plane 9.00 allows up to 4 panel regions

    def __init__(self):
        self.obj=None
        try:
            self.obj=Object.Get(PanelRegionHandler.NAME)
            # Suppress regeneration of panels in v3.0x
            Scene.GetCurrent().clearScriptLinks(PanelRegionHandler.NAME)
        except:
            pass

    def New(self, panelimage):
        if self.obj:
            mesh=self.obj.getData(mesh=True)
            for n in range(1,len(mesh.faces)):
                if mesh.faces[n].image!=mesh.faces[0].image:
                    self.delRegion(mesh.faces[n].image)
            self.obj.removeAllProperties()
        else:
            mesh=Mesh.New(PanelRegionHandler.NAME)
            self.obj=Mesh.New(PanelRegionHandler.NAME)
            self.obj=Object.New('Mesh', PanelRegionHandler.NAME)
            self.obj.link(mesh)
            Scene.GetCurrent().link(self.obj)
            self.obj.layers=[]	# invisible

        # (re)build faces and assign panel texture
        for n in range(len(mesh.faces),PanelRegionHandler.REGIONCOUNT+1):
            v=len(mesh.verts)
            mesh.verts.extend([[0,0,-n],[1,0,-n],[0,1,-n]])
            mesh.faces.extend([[v,v+1,v+2]])
        for n in range(PanelRegionHandler.REGIONCOUNT+1):
            mesh.faces[n].image=panelimage

        return self


    def addRegion(self, xoff, yoff, width, height):
        mesh=self.obj.getData(mesh=True)
        panelimage=mesh.faces[0].image
        name='PanelRegion'
        for img in Image.get():
            # try to re-use existing deleted panel region
            if img.size==[width,height] and img.source==Image.Sources.GENERATED and img.filename==name and not self.isRegion(img):
                break
        else:
            img=Image.New(name, width, height, 24)
        for y in range(height):
            for x in range(width):
                rgba=panelimage.getPixelI(xoff+x,yoff+y)
                if not rgba[3]:
                    img.setPixelI(x,y, (102,102,255,255))	# hilite transparent
                else:
                    img.setPixelI(x,y, rgba[:3]+[255])
        img.pack()

        for n in range(1,PanelRegionHandler.REGIONCOUNT+1):
            if mesh.faces[n].image==panelimage:
                mesh.faces[n].image=img
                self.obj.addProperty('x%d' % n, xoff)
                self.obj.addProperty('y%d' % n, yoff)
                (width,height)=img.size
                (pwidth,pheight)=panelimage.size
                xoff=float(xoff)/pwidth
                yoff=float(yoff)/pheight
                xscale=float(pwidth)/width
                yscale=float(pheight)/height
                # Assign UV mappings from panel image
                for obj in Scene.GetCurrent().objects:
                    if obj!=self.obj and obj.getType()=="Mesh":
                        mesh2 = obj.getData(mesh=True)
                        if mesh2.faceUV:
                            for face in mesh2.faces:
                                if face.image==panelimage:
                                    uv=[]
                                    for v in face.uv:
                                        x=(v.x-xoff)*xscale
                                        y=(v.y-yoff)*yscale
                                        if not -UV.LIMIT<=x<=1+UV.LIMIT or not -UV.LIMIT<=y<=1+UV.LIMIT:
                                            break
                                        uv.append(Vector(min(max(x,0),1), min(max(y,0),1)))
                                    else:
                                        face.uv=uv
                                        face.image=img
                            mesh2.update()
                break
        return img

    def panelimage(self):
        if not self.obj: return None
        mesh=self.obj.getData(mesh=True)
        return mesh.faces[0].image

    def isHandlerObj(self, obj):
        return self.obj==obj

    def isPanel(self, img):
        return (self.panelimage()==img)

    def isRegion(self, img):
        if not self.obj: return False
        mesh=self.obj.getData(mesh=True)
        if mesh.faces[0].image==img: return False	# is panel
        for n in range(1,PanelRegionHandler.REGIONCOUNT+1):
            if mesh.faces[n].image==img:
                try:
                    x=self.obj.getProperty('x%d' % n).data
                    y=self.obj.getProperty('y%d' % n).data
                    return (n,x,y,img.size[0],img.size[1])
                except:
                    return False
        else:
            return False

    def countRegions(self):
        if not self.obj: return 0
        mesh=self.obj.getData(mesh=True)
        count=0
        for n in range(1,PanelRegionHandler.REGIONCOUNT+1):
            if mesh.faces[n].image!=mesh.faces[0].image:
                count+=1
        return count

    def delRegion(self, img):
        r=self.isRegion(img)
        if not r: return False
        (n,x1,y1,width,height)=r
        mesh=self.obj.getData(mesh=True)
        panelimage=mesh.faces[0].image
        try:
            (pwidth,pheight)=panelimage.size
            xoff=float(x1)/pwidth
            yoff=float(y1)/pheight
            xscale=float(width)/pwidth
            yscale=float(height)/pheight
        except:
            xoff=yoff=0
            xscale=yscale=1
        # Reassign UV mappings back to panel image
        for obj in Scene.GetCurrent().objects:
            if obj!=self.obj and obj.getType()=="Mesh":
                mesh2 = obj.getData(mesh=True)
                if mesh2.faceUV:
                    for face in mesh2.faces:
                        if face.image==img:
                            face.image=panelimage
                            face.uv=[Vector([xoff+v.x*xscale, yoff+v.y*yscale]) for v in face.uv]
                mesh2.update()
        mesh.faces[n].image=panelimage
        img.reload()	# blank old region
        self.obj.removeProperty('x%d' % n)
        self.obj.removeProperty('y%d' % n)
        return True

    def regenerate(self):
        if not self.obj: return
        mesh=self.obj.getData(mesh=True)
        panelimage=mesh.faces[0].image
        panelimage.getSize()	# force load
        Window.WaitCursor(1)
        Window.DrawProgressBar(0, 'Panel regions')
        for n in range(1,PanelRegionHandler.REGIONCOUNT+1):
            Window.DrawProgressBar(n/6.0, 'Panel regions')
            img=mesh.faces[n].image
            if img!=panelimage:
                (width,height)=img.size
                xoff=self.obj.getProperty('x%d' % n).data
                yoff=self.obj.getProperty('y%d' % n).data
                for y in range(height):
                    for x in range(width):
                        rgba=panelimage.getPixelI(xoff+x,yoff+y)
                        if not rgba[3]:
                            img.setPixelI(x,y, (102,102,255,255))	# hilite transparent
                        else:
                            img.setPixelI(x,y, rgba[:3]+[255])
                img.glFree()	# force reload
                img.pack()	# repack
        mesh.update()
        Window.RedrawAll(0)
        Window.DrawProgressBar(1, 'Finished')
        Window.WaitCursor(0)


def findTex(basefile, texture, subdirs):
    texdir=basefile
    for l in range(PanelRegionHandler.REGIONCOUNT+1):
        q=texdir[:-1].rfind(Blender.sys.dirsep)
        if q==-1:
            return
        texdir=texdir[:q+1]

        for subdir in subdirs:
            # Handle empty subdir
            if subdir:
                sd=subdir+Blender.sys.dirsep
            for extension in ['.dds', '.DDS', '.png', '.PNG', '.bmp', '.BMP']:
                try:
                    return Image.Load(texdir+sd+texture+extension)
                except IOError:
                    pass
    return None


# Matrix.rotationPart() scaled to be unit size for normals and axis
def MatrixrotationOnly(mm, object):
    try:
        sx=1/abs(object.SizeX)
        sy=1/abs(object.SizeY)
        sz=1/abs(object.SizeZ)
        return Matrix([mm[0][0]*sx, mm[0][1]*sx, mm[0][2]*sx, 0],
                      [mm[1][0]*sy, mm[1][1]*sy, mm[1][2]*sy, 0],
                      [mm[2][0]*sz, mm[2][1]*sz, mm[2][2]*sz, 0],
                      [0,0,0,1])
    except:
        # Normals are screwed by zero scale - just return anything
        return Matrix().identity().resize4x4()

def remove_vowels(s):
    for eachLetter in s:
        if eachLetter in ['a','e','i','o','u','A','E','I','O','U','_']:
            s = s.replace(eachLetter, '')
    return s

def make_short_name(full_path):
    ref=full_path.split('/')
    short=""
    for comp in ref:
        if comp == ref[-1]:
            short=short+"_"
            if len(comp) > 15:
                short=short+remove_vowels(comp)
            else:
                short=short+comp
        else:
            short=short+comp[0]
            if comp[-1] == '2':
                short=short+"2"
    return short

# Read in datarefs
def getDatarefs():
    counts={'engines':8,
            'wings':56,	# including props and pylons?
            'doors':20,
            'gear':10}
    datarefs={}
    hierarchy={}
    err=IOError(0, "Corrupt DataRefs.txt file. Please re-install.")
    for sdir in ['uscriptsdir', 'scriptsdir']:
        if (Blender.Get(sdir) and
            exists(join(Blender.Get(sdir), 'DataRefs.txt'))):
            f=file(join(Blender.Get(sdir), 'DataRefs.txt'), 'rU')
            d=f.readline().split()
            if len(d)!=7 or d[0]!='2': raise err    # wtf?
            for line in f:
                d=line.split()
                if not d: continue
                if len(d)<3: raise err
                sname=make_short_name(d[0])
                ref=d[0].split('/')

                if ref[1] in ['test', 'version']:
                    continue            # hack: no usable datarefs

                n=1                    # scalar by default
                for c in ['int', 'float', 'double']:
                    if d[1].lower().startswith(c):
                        if len(d[1])>len(c):        # is array
                            n=int(d[1][len(c)+1:-1])
                        break
                else:
                    n=0                    # not a usable dataref

                if n>99:
                    if len(sname) > 23:
                        print 'WARNING - dataref ' + d[0] + ' is too long for key frame table'
                if n>9:
                    if len(sname) > 24:
                        print 'WARNING - dataref ' + d[0] + ' is too long for key frame table'
                elif n > 1:
                    if len(sname) > 25:
                        print 'WARNING - dataref ' + d[0] + ' is too long for key frame table'
                else:
                    if len(sname) > 28:
                        print 'WARNING - dataref ' + d[0] + ' is too long for key frame table'
#                elif len(sname) > 17:
#                   print 'WARNING - dataref ' + d[0] + ' is too long for show/hide'


                this=hierarchy
                for i in range(len(ref)-1):
                    if not ref[i] in this:
                        this[ref[i]]={}
                    this=this[ref[i]]
                this[ref[-1]]=n

                if ref[1]!=('multiplayer'):    # too many ambiguous datarefs
                    if sname in datarefs:
                        print 'WARNING - ambiguous short name '+ sname + ' for dataref ' + d[0]
                    else:
                        datarefs[sname]=(d[0], n)
                    if ref[-1] in datarefs:
                        datarefs[ref[-1]]=None        # ambiguous
                    else:
                        datarefs[ref[-1]]=(d[0], n)
            break
    else:
        raise IOError(0, "Missing DataRefs.txt file. Please re-install.")
    return (datarefs, hierarchy)

def getManipulators():
    """Returns data defining x-plane manipulators
    This method currently hard-codes the data definitions for manipulators and
    the associated cursors. Descriptions for manipulators can be found at:
    http://wiki.x-plane.com/Manipulators
    http://scenery.x-plane.com/library.php?doc=obj8spec.php

    Return values:
    manipulators -- A data dictionary defining all manipulators
    cursors -- An array of strings of all possible cursors

    """
    manipulators={}
    cursors=['four_arrows','hand','button','rotate_small','rotate_small_left','rotate_small_right','rotate_medium','rotate_medium_left','rotate_medium_right','rotate_large','rotate_large_left','rotate_large_right','up_down','down','up','left_right','right','left','arrow']

    manipulators['ATTR_manip_none']= {'00@NULL':0}
    manipulators['ATTR_manip_drag_xy'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@v1min':0.0, '04@v1max':0.0, '05@v2min':0.0, '06@v2max':0.0, '07@dref1':'', '08@dref2':'', '09@tooltip':''}
    manipulators['ATTR_manip_drag_axis'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@dz':0.0, '04@v1':0.0, '05@v2':0.0, '06@dataref':'', '07@tooltip':''}
    manipulators['ATTR_manip_command'] = {'00@cursor': '', '02@command':'', '03@tooltip':''}
    manipulators['ATTR_manip_command_axis'] = {'00@cursor': '', '01@dx':0.0, '02@dy':0.0, '03@dz':0.0, '04@pos-command':'', '05@neg-command':'', '06@tooltip':''}
    manipulators['ATTR_manip_noop']= {'00@NULL':0}
    manipulators['ATTR_manip_push'] = {'00@cursor': '', '01@v-down':0.0, '02@v-up':0.0, '03@dataref':'', '04@tooltip':''}
    manipulators['ATTR_manip_radio'] = {'00@cursor': '', '01@v-down':0.0, '02@dataref':'', '03@tooltip':''}
    manipulators['ATTR_manip_toggle'] = {'00@cursor': '', '01@v-on':0.0, '02@v-off':0.0, '03@dataref':'', '04@tooltip':''}
    manipulators['ATTR_manip_delta'] = {'00@cursor': '', '01@v-down':0.0, '02@v-hold':0.0, '03@v-min':0.0, '04@v-max':0.0, '05@dataref':'', '06@tooltip':''}
    manipulators['ATTR_manip_wrap'] = {'00@cursor': '', '01@v-down':0.0, '02@v-hold':0.0, '03@v-min':0.0, '04@v-max':0.0, '05@dataref':'', '06@tooltip':''}

    return (manipulators, cursors)

