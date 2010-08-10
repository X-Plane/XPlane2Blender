#!BPY
""" Registration info for Blender menus:
Name: 'X-Plane Plane or Weapon (.acf, .wpn)...'
Blender: 243
Group: 'Import'
Tooltip: 'Import an X-Plane airplane (.acf) or weapon (.wpn)'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script imports X-Plane v7 and v8 airplanes and weapons into Blender,
so that they can be exported as X-Plane scenery objects.

Planes are imported with three levels of detail to maximise rendering
speed in X-Plane.

Limitations:<br>
  * Planes made with PlaneMaker 7.30 or earlier are not supported.<br>
  * Wings are simplified to reduce polygon count.<br>
    Any wing curvature is ignored.<br>
  * Adjacent wing segments may not be exactly joined-up.<br>
  * Cockpit objects are ignored.<br>
  * Imported planes usually use two or more textures.<br>
    All faces must be made to share a single texture before export.<br>
  * Can't work out which faces are partially or wholly transparent.<br>
"""

#------------------------------------------------------------------------
# X-Plane importer for blender 2.43 or above
#
# Copyright (c) 2004,2005,2006,2007 Jonathan Harris
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
# 2004-02-01 v1.00
#  - First public version
#
# 2004-08-22 v1.10
#  - Requires XPlane2Blender 1.50 since DYNAMIC flag has been reversed
#  - Support for 7.40 format planes
#  - Improved texture placement (thanks to Austin for sharing his code).
#  - Fixed bug where VTOL vector was ignored on engines
#  - Misc Bodies 3-8 now imported, but using texture from Misc Bodies 1&2
#
# 2004-08-28 v1.11
#  - Fix for changed layer semantics in Blender 234 (fix to Blender bug #1212)
#  - Add single-letter suffix to mesh names to denote layer
#
# 2004-08-28 v1.12
#  - Requires Blender 234 due to changed layer semantics of Blender fix #1212
#
# 2004-08-28 v1.13
#
# 2004-12-31 v1.14
#  - Fixed bug with zero length bodies
#  - Truncate pre-730 planes at fuselage location 12 - improves smoothing.
#
# 2005-03-01 v1.15
#  - Fixed parsing bug with non-zero values of is_hm or is_ga.
#
# 2005-04-24 v2.00
#  - Added support for v8 planes and weapons.
#  - All bodies and weapons imported using correct texture.
#  - Airfoil width read from .afl file.
#
# 2005-05-10 v2.02
#  - Add '*' to mesh names for parts that use secondary texture.
#
# 2005-05-14 v2.05
#  - Add support for v8.15 format planes.
#
# 2006-02-01 v2.17
#  - Add support for v8.30 format planes.
#
# 2006-02-28 v2.18
#  - Add support for v8.40 format planes (Misc Objects).
#  - Add thrust vectoring to props and nacelles.
#  - PNG takes precedence over BMP.
#
# 2006-04-18 v2.20
#  - Add light attachment to gear.
#  - Add wingtip strobe lights. All lights now present in all layers.
#  - Fixes for misc objs, wpns and objs attached to gear and wheels
#
# 2006-04-22 v2.21
#  - Re-use meshes for duplicate wings, bodies, weapons and objects
#
# 2006-05-02 v2.22
#  - Fix for fairing rotation.
#
# 2006-06-12 v2.24
#  - Fix for zero-length bodies.
#
# 2006-07-19 v2.25
#  - Use v8.50 named lights. Lights back to shared between layers.
#  - Fix for wings in layer 3 (broken in 2.21).
#  - Fix for adjoining wings small enough to be root and tip.
#
# 2006-09-29 v2.31
#  - Hack for v8 weapons.
#
# 2006-10-16 v2.33
#  - Support for importing planes centred at the plane's centre of
#    gravity (for making CSLs for use with recent versions of X-IvAp).
#
# 2006-12-21 v2.34
#  - Add support for v8.60 format planes (no visible changes).
#  - Handle wing incidence.
#
# 2006-03-16 v2.35
#  - Fix for weapon fins.
#
# 2006-03-18 v2.36
#  - Fixes for importing planes on Mac & Linux.
#
# 2006-09-17 v2.42
#  - Landing gear and flat wings imported as flat.
#
# 2007-12-02 v3.00
#  - Support for v9.00 planes.
#  - Support for DDS textures.
#
# 2008-01-20 v3.07
#  - Support for 9b18 planes.
#

import sys
import Blender
from Blender import Object, NMesh, Lamp, Image, Material, Window, Mathutils
from Blender.Mathutils import Vector, Matrix, RotationMatrix, ScaleMatrix, TranslationMatrix, Quaternion
from struct import unpack
from math import hypot, pi, sin, cos, atan, radians
from os import listdir
from os.path import basename, dirname, join, splitext

from XPlaneUtils import Vertex, UV, findTex
from XPlaneImport import OBJimport

class ParseError(Exception):
    def __init__(self, msg):
        self.msg=msg


#------------------------------------------------------------------------
#-- ACFimport --
#------------------------------------------------------------------------
class ACFimport:
    LAYER1=1
    LAYER2=2
    LAYER3=4
    LAYERS=[LAYER1,LAYER2,LAYER3]
    LAYER1MKR=' H'
    LAYER2MKR=' M'
    LAYER3MKR=' L'
    MARKERS=[LAYER1MKR,LAYER2MKR,LAYER3MKR]
    IMAGE2MKR='*'	# Marker for parts with non-primary texture

    # bodies smaller than this [m] skipped
    THRESH1=1.0
    THRESH2=2.5
    THRESH3=7.0

    #------------------------------------------------------------------------
    def __init__(self, filename, isscenery, relocate=False):
        self.debug=0	# 1: extra debug info in console. 2: also dump txt file
        self.isscenery=isscenery
        if self.isscenery:
            self.scale=0.3048		# foot->metre constant
        else:
            self.scale=1.0
        if Blender.sys.dirsep=='\\':
            # Lowercase Windows drive lettter
            self.filename=filename[0].lower()+filename[1:]
        else:
            self.filename=filename
        self.acf=ACF(self.filename, self.debug)
        self.scene = Blender.Scene.GetCurrent()
        self.navloc = Vertex(0.0, 0.0, 0.0)
        self.tailloc = Vertex(0.0, 0.0, 0.0)
        self.wingc = {}
        self.image=0
        self.image2=0
        self.mm=Matrix([ self.scale, 0.0, 0.0, 0.0],
                       [0.0, -self.scale, 0.0, 0.0],
                       [0.0, 0.0, -self.scale, 0.0],
                       [0.0, 0.0, 0.0,         1.0])
        self.meshcache={}

        cur=Window.GetCursorPos()
        self.offset=Vertex(cur[0], cur[1], cur[2])
        if self.acf.HEADER_version in [1,800]:
            # Importing weapon
            if relocate:
                self.offset+=Vertex(0, -self.acf.cgY, -self.acf.cgZ, self.mm)
            return	# Texture handled elsewhere
        else:
            if relocate:
                self.offset+=Vertex(0, -self.acf.WB_cgY, -self.acf.WB_cgZ, self.mm)

        texfilename=self.filename[:self.filename.rindex('.')]+'_paint'
        for extension in ['.dds', '.DDS', '.png', '.PNG', '.bmp', '.BMP']:
            try:
                file = open(texfilename+extension, "rb")
            except IOError:
                pass
            else:
                for extension2 in ['.dds', '.DDS', '.png', '.PNG', '.bmp', '.BMP']:
                    try:
                        self.image2 = Image.Load(texfilename+'2'+extension2)
                    except IOError:
                        pass

                # Handle spaces in primary texture filename
                if 0:	#Blender.sys.basename(texfilename).find(" ") != -1:
                    basefilename=Blender.sys.basename(texfilename)
                    newfilename=""
                    for i in range(len(basefilename)):
                        if basefilename[i]==" ":
                            newfilename+="_"
                        else:
                            newfilename+=basefilename[i]
                    print "Info:\tCreated new texture file \"%s\"" % (
                        newfilename+extension)
                    newfilename=(Blender.sys.dirname(texfilename)+
                                 Blender.sys.dirsep+newfilename)
                    newfile=open(newfilename+extension, "wb")
                    newfile.write(file.read())
                    newfile.close()
                    texfilename=newfilename
                file.close()
                self.image = Image.Load(texfilename+extension)
                return
        print "Warn:\tNo texture file found"
        

    #------------------------------------------------------------------------
    def doImport(self):

        layers=self.scene.layers
        self.scene.layers=[1,2,3]	# otherwise object centres not updated
        
        # Hack! Just importing weapon
        if self.acf.HEADER_version in [1,800]:
            Window.DrawProgressBar(0.5, "Importing weapon ...")
            self.doBody(basename(self.filename), 0)
            self.scene.layers=layers
            return
        
        if self.isscenery:
            n=(DEFfmt.partDIM+DEFfmt.wattDIM+DEFfmt.gearDIM+DEFfmt.doorDIM+
               DEFfmt.objsDIM+len(DEFfmt.lites)+1)
        else:
            n=DEFfmt.partDIM
        i=0

        for (name, p) in DEFfmt.parts:
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing bodies ...")
            self.doBody(name, p)

        if not self.isscenery:
            self.scene.layers=layers
            return

        for p in range(DEFfmt.engnDIM):
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing props ...")
            self.doProp(p)

        # Need to do wings in two passes
        for (name, p) in DEFfmt.wings:
            self.doWing1(name, p)

        for (name, p) in DEFfmt.wings:
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing wings ...")
            self.doWing2(name, p)
                
        for p in range(DEFfmt.gearDIM):
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing gear ...")
            self.doGear(p)

        for p in range(DEFfmt.wattDIM):
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing weapons ...")
            self.doBody(None, p)

        for p in range(DEFfmt.doorDIM):		# Skip speedbrakes
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing doors ...")
            self.doDoor(p)

        if 'objs' in dir(self.acf):	# New in 8.40
            for p in range(DEFfmt.objsDIM):
                i=i+1
                Window.DrawProgressBar(0.25+0.75*i/n, "Importing OBJs ...")
                self.doObjs(p)
                     
        for p in range(len(DEFfmt.lites)):
            i=i+1
            Window.DrawProgressBar(0.25+0.75*i/n, "Importing lights ...")
            self.doLight(p)

        if self.acf.VIEW_has_navlites:
            # uses values computed during wings
            self.addLamp("airplane_nav_left",  1.0, 0.0, 0.0, # was Nav Left
                         self.offset+Vertex(-(self.navloc.x+0.05),
                                            self.navloc.y, self.navloc.z))
            self.addLamp("airplane_strobe",  1.0, 1.0, 1.0,   # was Strobe Left
                         self.offset+Vertex(-(self.navloc.x+0.05),
                                            self.navloc.y-0.1, self.navloc.z))
            self.addLamp("airplane_nav_right", 0.0, 1.0, 0.0, # was Nav Right
                         self.offset+Vertex(self.navloc.x + 0.05,
                                            self.navloc.y, self.navloc.z))
            self.addLamp("airplane_strobe",  1.0, 1.0, 1.0,   # wasStrobe Right
                         self.offset+Vertex(self.navloc.x + 0.05,
                                            self.navloc.y-0.1, self.navloc.z))
            if self.acf.HEADER_version<800:    # v7
                self.addLamp("airplane_beacon", 1.0, 0.0, 0.0,# was Tail pulse or Nav Pulse
                             self.offset+Vertex(self.tailloc.x, self.tailloc.y,
                                                self.tailloc.z + 0.05))

        self.scene.layers=layers
                
    #------------------------------------------------------------------------
    def doProp(self, p):

        # Arbitrary constant
        twist=pi*(30.0/180.0)
        
        engn=self.acf.engn[p]
        part=self.acf.part[p]
        wing=self.acf.wing[p]
            
        if (p>=self.acf.ENGINE_num_thrustpoints or
            engn.engn_type not in [0,1,2,8] or
            not engn.num_blades or
            not wing.semilen_SEG):
            return
            
        # texture
        if part.part_tex==0:
            imagemkr=ACFimport.LAYER1MKR
            image=self.image
        else:
            imagemkr=ACFimport.LAYER1MKR+ACFimport.IMAGE2MKR
            image=self.image2

        mesh=NMesh.New("Prop %s%s" % ((p+1), imagemkr))
        mm=TranslationMatrix((Vertex(part.part_x,
                                     part.part_y+self.acf.VTOL_vectarmY,
                                     part.part_z+self.acf.VTOL_vectarmZ,
                                     self.mm)+self.offset).toVector(4))
        mm=RotationMatrix(engn.vert_init, 4, 'x')*mm
        mm=RotationMatrix(-engn.side_init, 4, 'z')*mm
        if self.acf.VTOL_vect_EQ and wing.inc_vect[0]:	# bizarre
            mm=RotationMatrix(self.acf.VTOL_vect_min_disc, 4, 'x')*mm

        v=[Vertex(0,
                  sin(twist)*
                  wing.Croot*self.scale/4,
                  -cos(twist)*engn.prop_dir*
                  wing.Croot*self.scale/4),
           Vertex(0,
                  -sin(twist)*
                  wing.Croot*self.scale*3/4,
                  cos(twist)*engn.prop_dir*
                  wing.Croot*self.scale*3/4),
           Vertex(wing.semilen_SEG*self.scale,
                  0,
                  engn.prop_dir*
                  wing.Ctip*self.scale*3/4),
           Vertex(wing.semilen_SEG*self.scale,
                  0,
                  -engn.prop_dir*
                  wing.Ctip*self.scale/4)]
        
        ruv=[UV(part.top_s1,part.top_t1),
             UV(part.top_s2,part.top_t1),
             UV(part.top_s2,part.top_t2),
             UV(part.top_s1,part.top_t2)]
        luv=[UV(part.bot_s1,part.bot_t2),
             UV(part.bot_s2,part.bot_t2),
             UV(part.bot_s2,part.bot_t1),
             UV(part.bot_s1,part.bot_t1)]
        
        for i in range(int(engn.num_blades)):
            a=(1+i*2)*pi/engn.num_blades
            fv=[]
            for v1 in v:
                fv.append(Vertex(cos(a)*v1.x - sin(a)*v1.z,
                                 v1.y,
                                 sin(a)*v1.x + cos(a)*v1.z))
            self.addFace(mesh, fv, ruv, image)
            self.addFace(mesh,
                         [fv[3], fv[2], fv[1], fv[0]],
                         luv, image)

        self.addMesh(mesh.name, mesh, ACFimport.LAYER1, mm)

    #------------------------------------------------------------------------
    def doWing1(self, name, p):

        part=self.acf.part[p]
        wing=self.acf.wing[p]
        if not (part.part_eq and wing.semilen_SEG):
            return
        
        centre=Vertex(part.part_x, part.part_y, part.part_z, self.mm)
        
        tip=centre+Vertex(RotationMatrix(wing.lat_sign*wing.dihed1, 3, 'y') *
                          (RotationMatrix(wing.lat_sign*wing.sweep1, 3, 'z') *
                           Vector([wing.lat_sign*wing.semilen_SEG*self.scale,0,0])))

        # Maybe nav light location - at least in 8.40 only main wings count
        if p in DEFfmt.partMainWings:
            if tip.x>self.navloc.x:
                self.navloc=tip
            if tip.z>self.tailloc.z:
                self.tailloc=tip

        self.wingc[p]=((centre, tip))
        if self.debug:
            print "%s \t[%s] [%s]" % (name, centre, tip)
        
    #------------------------------------------------------------------------
    def doWing2(self, name, p):

        part=self.acf.part[p]
        wing=self.acf.wing[p]
        if not (part.part_eq and wing.semilen_SEG):
            return

        # Arbitrary constants for symmetrical and lifting wings
        sym_width=0.09
        lift_width=0.10
        chord1=0.125
        chord2=0.450
        max_dihed=20.0		# Wings with d greater than this treated as Sym
        tip_fudge=0.2		# wings considered joined if closer [ft]

        if self.debug:
            print "%s \t" % name,

        # Is this a wing tip?
        istip=True
        (centre, tip) = self.wingc[p]
        for p2, (c2, t2) in self.wingc.iteritems():
            if (p2 != p and
                tip.equals(c2, tip_fudge) and
                abs(wing.Ctip-self.acf.wing[p2].Croot) < tip_fudge and
                abs(wing.dihed1-self.acf.wing[p2].dihed1) < max_dihed):
                istip=False
                child=p2
                break
        if self.debug:
            if istip:
                print "Tip",
            else:
                print "child=%s" % child,

        # Find parent in segment and root of segment
        rootp=p		# part number of root
        c=centre	# centre of root
        considered=[rootp]
        if not istip: considered.append(child)
        while 1:
            for p2, (c2, t2) in self.wingc.iteritems():
                if (p2 not in considered and
                    c.equals(t2, tip_fudge) and
                    abs(self.acf.wing[p2].Ctip-
                        self.acf.wing[rootp].Croot) < tip_fudge and
                    abs(self.acf.wing[p2].dihed1-
                        self.acf.wing[rootp].dihed1) < max_dihed):
                    rootp=p2
                    c=c2
                    considered.append(rootp)
                    break
            else:
                break
        if self.debug:
            if p==rootp:
                print "Root"
            else:
                print "Root=%s" % rootp

        # texture
        if part.part_tex==0:
            imagemkr=''
            image=self.image
        else:
            imagemkr=ACFimport.IMAGE2MKR
            image=self.image2

        mm=TranslationMatrix((self.offset+centre).toVector(4))
        mm=RotationMatrix(-wing.lat_sign*wing.dihed1, 4, 'y')*mm

        # Re-use existing meshes
        crs=[DEFfmt.partMainWings,DEFfmt.partMiscWings,DEFfmt.partPylons]
        for cr in crs:
            if not p in cr: continue
            for p2 in cr:
                part2=self.acf.part[p2]
                wing2=self.acf.wing[p2]
                if (p2>=p or not part2.part_eq or
                    part.part_tex!=part2.part_tex or
                    part.top_s1!=part2.top_s1 or
                    part.top_s2!=part2.top_s2 or
                    part.top_t1!=part2.top_t1 or
                    part.top_t2!=part2.top_t2 or
                    wing.semilen_SEG!=wing2.semilen_SEG or
                    wing.Ctip!=wing2.Ctip or
                    wing.Croot!=wing2.Croot or
                    wing.dihed1!=wing2.dihed1 or
                    wing.sweep1!=wing2.sweep1 or
                    wing.Rafl0!=wing2.Rafl0 or
                    wing.Tafl0!=wing2.Tafl0): continue
                meshes=self.meshcache[p2]
                if wing.lat_sign*self.acf.wing[p2].lat_sign<0:
                    mm=ScaleMatrix(-1, 4, Vector(1, 0, 0))*mm
                for i in range(len(meshes)):
                    if i==2:	# layer 3
                        if not istip: continue
                        if p!=rootp:
                            (root, foo) = self.wingc[rootp]
                            mm=TranslationMatrix((self.offset + root).toVector(4))
                            if wing.lat_sign*self.acf.wing[p2].lat_sign<0:
                                mm=ScaleMatrix(-1, 4, Vector(1, 0, 0))*mm
                    ob=self.addMesh(name+ACFimport.MARKERS[i]+imagemkr,
                                    meshes[i], ACFimport.LAYERS[i], mm)
                return
        # No matching wing
        self.meshcache[p]=[]

        # Find four points - leading root & tip, trailing tip & root
        rootinc=RotationMatrix(wing.incidence[0]*wing.lat_sign, 3, 'x')
        if istip:
            # Don't want to rotate to find wing sweep. So find tip manually.
            tip=Vertex(RotationMatrix(wing.lat_sign*wing.sweep1, 3, 'z') *
                       Vector([wing.lat_sign*wing.semilen_SEG*self.scale,0,0]))
            tiplen=wing.Ctip
            tipinc=RotationMatrix(wing.incidence[wing.els-1]*wing.lat_sign, 3, 'x')
            v=[Vertex(rootinc*Vector([0.0,  wing.Croot*self.scale/4,   0.0])),
               Vertex( tipinc*Vector([0.0,  wing.Ctip *self.scale/4,   0.0]))+tip,
               Vertex( tipinc*Vector([0.0, -wing.Ctip *self.scale*3/4, 0.0]))+tip,
               Vertex(rootinc*Vector([0.0, -wing.Croot*self.scale*3/4, 0.0]))]
        else:
            # Get tip from child's root so segments line-up exactly
            # XXX Todo: Make mid-chord vertices line-up also
            (tip,t2)=self.wingc[child]
            tip=(tip-centre).toVector(4) * RotationMatrix(wing.lat_sign*
                                                          wing.dihed1, 4, 'y')
            tiplen=self.acf.wing[child].Croot
            tipinc=RotationMatrix(self.acf.wing[child].incidence[0]*self.acf.wing[child].lat_sign, 3, 'x')
            v=[Vertex(rootinc*Vector([0.0,  wing.Croot*self.scale/4,                   0.0])),
               Vertex( tipinc*Vector([0.0,  self.acf.wing[child].Croot*self.scale/4,   0.0]))+tip,
               Vertex( tipinc*Vector([0.0, -self.acf.wing[child].Croot*self.scale*3/4, 0.0]))+tip,
               Vertex(rootinc*Vector([0.0, -wing.Croot*self.scale*3/4,                 0.0]))]

        rv=v
        lv=[v[3], v[2], v[1], v[0]]
        
        if self.debug:
            for q in v:
                print "[%5.1f %5.1f %5.1f]" % (q.x, q.y, q.z),

        # Corresponding texture points
        miny=max(v[0].y,v[1].y)	# leading edge
        maxy=min(v[2].y,v[3].y)	# trailing edge
        
        if wing.is_left:
            rys=(part.top_s2-part.top_s1)/(miny-maxy)
            ruv=[UV(part.top_s1+(miny-v[0].y)*rys, part.top_t1),
                 UV(part.top_s1+(miny-v[1].y)*rys, part.top_t2),
                 UV(part.top_s1+(miny-v[2].y)*rys, part.top_t2),
                 UV(part.top_s1+(miny-v[3].y)*rys, part.top_t1)]
            lys=(part.bot_s2-part.bot_s1)/(miny-maxy)
            luv=[UV(part.bot_s1+(miny-v[3].y)*lys, part.bot_t1),
                 UV(part.bot_s1+(miny-v[2].y)*lys, part.bot_t2),
                 UV(part.bot_s1+(miny-v[1].y)*lys, part.bot_t2),
                 UV(part.bot_s1+(miny-v[0].y)*lys, part.bot_t1)]
        else:
            rys=(part.bot_s2-part.bot_s1)/(miny-maxy)
            ruv=[UV(part.bot_s1+(miny-v[0].y)*rys, part.bot_t1),
                 UV(part.bot_s1+(miny-v[1].y)*rys, part.bot_t2),
                 UV(part.bot_s1+(miny-v[2].y)*rys, part.bot_t2),
                 UV(part.bot_s1+(miny-v[3].y)*rys, part.bot_t1)]
            lys=(part.top_s2-part.top_s1)/(miny-maxy)
            luv=[UV(part.top_s1+(miny-v[3].y)*lys, part.top_t1),
                 UV(part.top_s1+(miny-v[2].y)*lys, part.top_t2),
                 UV(part.top_s1+(miny-v[1].y)*lys, part.top_t2),
                 UV(part.top_s1+(miny-v[0].y)*lys, part.top_t1)]

        # Type of wing to draw
        if (wing.semilen_SEG*self.scale < ACFimport.THRESH1 and
            wing.Croot*self.scale < ACFimport.THRESH1/2 and
            istip and p==rootp):
            # Small and not part of a segment - draw as thin
            iscrappy=True
        else:
            iscrappy=False
                        
            # Orientation
            if abs(wing.dihed1) >= max_dihed:
                orient=0	# Verticalish
                rwidth=sym_width/2
                twidth=sym_width/2
            else:
                if ((wing.dihed1+90)*wing.lat_sign < 0):
                    orient=-1	# Left side
                else:
                    orient=1	# Right side
                rwidth=lift_width/2
                twidth=lift_width/2

            w=self.afl(wing.Rafl0)
            if w:
                rwidth=w/2
                twidth=w/2
            w=self.afl(wing.Tafl0)
            if w:
                twidth=w/2

            rwidth=wing.lat_sign*rwidth
            twidth=wing.lat_sign*twidth

        # Layer 1
        mesh=NMesh.New(name+ACFimport.LAYER1MKR+imagemkr)

        if iscrappy:
            # Not worth toggling culling just for this, so repeat the face
            self.addFace(mesh, rv, ruv, image, False)
            self.addFace(mesh, lv, luv, image, False)
        else:
            self.addFacePart(mesh, rv, ruv, 0,        chord1,   rwidth, twidth,
                             image)
            self.addFacePart(mesh, rv, ruv, chord1,   chord2,   rwidth, twidth,
                             image)
            self.addFacePart(mesh, rv, ruv, chord2,   1,        rwidth, twidth,
                             image)
            self.addFacePart(mesh, lv, luv, 0,        1-chord2, rwidth, twidth,
                             image, False)	# sharp edge required
            self.addFacePart(mesh, lv, luv, 1-chord2, 1-chord1, rwidth, twidth,
                             image)
            self.addFacePart(mesh, lv, luv, 1-chord1, 1,        rwidth, twidth,
                             image)
            if istip:
                # Add end cap
                ctip=rv[2].y-rv[1].y
                ntip=ctip*twidth
                self.addFace(mesh,
                             [rv[1],
                              rv[1]+Vertex(0, ctip*chord1, -ntip),
                              rv[1]+Vertex(0, ctip*chord1,  ntip)],
                             [ruv[1],
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord1,ruv[1].t),
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord1,ruv[1].t)],
                             image)
                self.addFace(mesh,
                             [rv[1]+Vertex(0, ctip*chord1,  ntip),
                              rv[1]+Vertex(0, ctip*chord1, -ntip),
                              rv[1]+Vertex(0, ctip*chord2, -ntip),
                              rv[1]+Vertex(0, ctip*chord2,  ntip)],
                             [UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord1,ruv[1].t),
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord1,ruv[1].t),
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord2,ruv[1].t),
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord2,ruv[1].t)],
                             image)
                self.addFace(mesh,
                             [rv[2],
                              rv[1]+Vertex(0, ctip*chord2,  ntip),
                              rv[1]+Vertex(0, ctip*chord2, -ntip)],
                             [ruv[2],
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord2,ruv[1].t),
                              UV(ruv[1].s+(ruv[2].s-ruv[1].s)*chord2,ruv[1].t)],
                             image)

        self.meshcache[p].append(mesh)
        self.addMesh(mesh.name, mesh, ACFimport.LAYER1, mm)

        # Layer 2
        if iscrappy:
            return
        
        mesh=NMesh.New(name+ACFimport.LAYER2MKR+imagemkr)
        self.addFace(mesh, rv, ruv, image, False)
        self.addFace(mesh, lv, luv, image, False)
        self.meshcache[p].append(mesh)
        self.addMesh(mesh.name, mesh, ACFimport.LAYER2, mm)


        # Layer 3
        if not istip:
            return	# Only do wing tips

        if p==rootp:
            if wing.semilen_SEG*self.scale < ACFimport.THRESH3:
                return
        else:
            (foo, tip) = self.wingc[p]
            (root, foo) = self.wingc[rootp]
            tip=tip-root	# tip relative to root

            if (tip.x*tip.x + tip.y*tip.y + tip.z*tip.z < 
                ACFimport.THRESH3 * ACFimport.THRESH3):
                return

            rootwing=self.acf.wing[rootp]
            rootinc=RotationMatrix(rootwing.incidence[0]*rootwing.lat_sign, 3, 'x')
            tipinc=RotationMatrix(wing.incidence[wing.els-1]*wing.lat_sign, 3, 'x')
            rv=[Vertex(rootinc*Vector([0.0,  rootwing.Croot*self.scale/4,   0.0])),
                Vertex( tipinc*Vector([0.0,  wing.Ctip     *self.scale/4,   0.0]))+tip,
                Vertex( tipinc*Vector([0.0, -wing.Ctip     *self.scale*3/4, 0.0]))+tip,
                Vertex(rootinc*Vector([0.0, -rootwing.Croot*self.scale*3/4, 0.0]))]
            lv=[rv[3], rv[2], rv[1], rv[0]]
            mm=TranslationMatrix((self.offset + root).toVector(4))

        mesh=NMesh.New(name+ACFimport.LAYER3MKR+imagemkr)
        self.addFace(mesh, rv, ruv, image, False)
        self.addFace(mesh, lv, luv, image, False)
        self.meshcache[p].append(mesh)
        self.addMesh(mesh.name, mesh, ACFimport.LAYER3, mm)

    
    #------------------------------------------------------------------------
    def doBody(self, name, p):
        
        is_wpn=(p<=DEFfmt.wattDIM)

        if is_wpn:
            # Weapon locations are special
            if name:	# Importing stand-alone weapon
                watt=None
                wpnname=name
                (obname,foo)=splitext(wpnname)
                meshname=obname
            else:	# Get weapon details from weapon attach structure
                watt=self.acf.watt[p]
                wpnname=watt.watt_name
                if not wpnname: return
                (meshname,foo)=splitext(wpnname)
                obname="W%02d %s" % (p+1, meshname)
            wpn=self.wpn(wpnname)
            if not wpn: return
            part=wpn.part
            (texname,foo)=splitext(wpnname)
            image=findTex(self.filename, texname, ['Weapons'])
            imagemkr=''

            if watt:
                mm=TranslationMatrix((Vertex(watt.watt_x, watt.watt_y, watt.watt_z, self.mm)+
                                      self.offset).toVector(4))
                mm=self.rotate(watt.watt_con, False,
                               watt.watt_psi, watt.watt_the, watt.watt_phi)*mm
            else:
                mm=TranslationMatrix(self.offset.toVector(4))
            mm=TranslationMatrix(Vertex(-part.part_x, -part.part_y, -part.part_z, self.mm).toVector(4))*mm
            # Re-use existing meshes
            if wpnname in self.meshcache:
                meshes=self.meshcache[wpnname]
                for i in range(len(meshes)):
                    self.addMesh(obname+ACFimport.MARKERS[i],
                                 meshes[i], ACFimport.LAYERS[i], mm)
                return
            else:
                self.meshcache[wpnname]=[]
                
        else:
            # Normal bodies
            obname=meshname=name
            part=self.acf.part[p]
            if not part.part_eq:
                return
            if part.part_tex==0:
                imagemkr=''
                image=self.image
            else:
                imagemkr=ACFimport.IMAGE2MKR
                image=self.image2
            
            if p in DEFfmt.partFairings:
                # Fairings take location but not rotation from wheels
                part.patt_con=0	# appears to be random in acf
                gear=self.acf.gear[p-DEFfmt.partFair1]
                a=RotationMatrix(gear.latE, 3, 'y')
                a=RotationMatrix(-gear.lonE, 3, 'x')*a
                mm=TranslationMatrix((Vertex(gear.gear_x,
                                             gear.gear_y, 
                                             gear.gear_z,
                                             self.mm)+
                                      Vertex(a * Vector([0,0,-gear.leg_len*self.scale]))+
                                      self.offset).toVector(4))
            else:
                mm=TranslationMatrix((Vertex(part.part_x,
                                             part.part_y,
                                             part.part_z,
                                             self.mm)+self.offset).toVector(4))
            mm=self.rotate(part.patt_con, True,
                           part.part_psi, part.part_the, part.part_phi)*mm

            if p in DEFfmt.partNacelles:
                # Nacelles also affected by engine cant and vector
                engn=self.acf.engn[p-DEFfmt.partNace1]
                wing=self.acf.wing[p-DEFfmt.partNace1]
                mm=RotationMatrix(engn.vert_init, 4, 'x')*mm
                mm=RotationMatrix(-engn.side_init, 4, 'z')*mm
                if self.acf.VTOL_vect_EQ and wing.inc_vect[0]:	# bizarre
                    mm=RotationMatrix(self.acf.VTOL_vect_min_nace, 4, 'x')*mm

            # Re-use existing meshes
            crs=[DEFfmt.partMisc,DEFfmt.partNacelles,DEFfmt.partFairings]
            for cr in crs:
                if not p in cr: continue
                for p2 in cr:
                    part2=self.acf.part[p2]
                    if (p2>=p or not part2.part_eq or
                        part.s_dim!=part2.s_dim or
                        part.r_dim!=part2.r_dim or
                        part.part_tex!=part2.part_tex or
                        part.top_s1!=part2.top_s1 or
                        part.top_s2!=part2.top_s2 or
                        part.top_t1!=part2.top_t1 or
                        part.top_t2!=part2.top_t2): continue
                    for i in range(part.s_dim):
                        # Assume symmetrical
                        for j in range(int((1+part.r_dim)/2)):
                            if part.geo_xyz[i][j]!=part2.geo_xyz[i][j]:
                                break
                        else:
                            continue
                        break
                    else:
                        # Matching part
                        meshes=self.meshcache[p2]
                        for i in range(len(meshes)):
                            self.addMesh(obname+ACFimport.MARKERS[i]+imagemkr,
                                         meshes[i], ACFimport.LAYERS[i], mm)
                        return
            # No matching part
            self.meshcache[p]=[]
                            
        
        if self.debug: print obname

        # Get vertex data in 2D array
        v=[]

        # locate the data in the array and skip duplicates
        rdim=int(part.r_dim/2)*2-2	# Must be even
        seq=range(rdim/2)
        seq.extend(range((rdim+2)/2,rdim+1))

        for i in range(part.s_dim):
            if (i==12 and
                Vertex(part.geo_xyz[i][0]).equals(Vertex(0.0, 0.0, 0.0))):
                # Special case: Plane-Maker<7.30 leaves these parts as 0
                if self.debug: print "Stopping at 12"
                break
                
            # Special case: Plane-Maker>=7.30 replicates part 11 offset 0.001'
            if i==12:	# was >11
                for j in seq:
                    if not Vertex(part.geo_xyz[i][j]).equals(
                        Vertex(part.geo_xyz[i-1][j]), 0.001):
                        break
                else:
                    if self.debug: print "Stopping at %s" % i
                    break

            if self.debug: print i
            w=[]
            for j in seq:
                q=Vertex(part.geo_xyz[i][j], self.mm)
                w.append(q)
                if self.debug: print "[%5.1f %5.1f %5.1f]" % (q.x, q.y, q.z),
            if self.debug: print
            
            v.append(w)

        
        sdim=len(v)	# We now have up to 20 segments (maybe 12 or 8 or less)
        rdim=len(v[0])	# with 16 or fewer (but even) vertices/segment


        # Seriously fucked up algorithm for determining textures for
        # half (rdim/2+1) the body from load_plane_geo(), hl_drplane.cpp.
        rsem=rdim/2+1

        y_ctr=0.0
        for r in range(rdim):
            # Hack: Only use the first 12 stations for the fuse centreline
            # to keep the same centreline loc before and after 730, where
            # the number of fuselage stations changed from 12 to 20.
            for s in range (min(sdim,12)):
                y_ctr+=v[s][r].z/(rdim*sdim)

        uv=[]
        for s in range(sdim):
            uv.append([])
            for R in range(rsem):
                # R is the point we are finding the s/t coordinate for
                uv[s].append(UV(0,0))
                point_above_ctr=(v[s][R].z>y_ctr)
                point_below_ctr=not point_above_ctr

                if point_above_ctr:
                    r1=R
                    r2=rsem
                else:
                    r1=0
                    r2=R

                for r in range(r1,r2):	# remember we go to r+1!
                    # r is simply a counter to build up the coordinate for R
                    tlen=hypot(v[s][r+1].x-v[s][r].x, v[s][r+1].z-v[s][r].z)
                    if (point_above_ctr and v[s][r].z>y_ctr and
                        v[s][r+1].z>y_ctr):
                        uv[s][R].t+=tlen
                    if (point_below_ctr and v[s][r].z<y_ctr and
                        v[s][r+1].z<y_ctr):
                        uv[s][R].t-=tlen
                    if (point_above_ctr and v[s][r].z!=v[s][r+1].z and
                        v[s][r].z>=y_ctr and v[s][r+1].z<=y_ctr):
                        uv[s][R].t+=tlen*(v[s][r  ].z-y_ctr)/(v[s][r].z-v[s][r+1].z)
                    if (point_below_ctr and v[s][r].z!=v[s][r+1].z and
                        v[s][r].z>=y_ctr and v[s][r+1].z<=y_ctr):
                        uv[s][R].t-=tlen*(y_ctr-v[s][r+1].z)/(v[s][r].z-v[s][r+1].z)

                if v[s][rsem].z>=y_ctr:
                    uv[s][R].t+=(v[s][rsem].z-y_ctr)
                if v[s][0   ].z<=y_ctr:
                    uv[s][R].t+=(v[s][0   ].z-y_ctr)

        lo_y= 99999.0
        lo_z= 99999.0
        hi_y=-99999.0
        hi_z=-99999.0

        # find extreme points for scale
        for s in range(sdim):
            for r in range(rsem):
                if uv[s][r].t>hi_y:
                    hi_y=uv[s][r].t			
                if uv[s][r].t<lo_y:
                    lo_y=uv[s][r].t			
                if v[s][r].y>hi_z:
                    hi_z=v[s][r].y
                if v[s][r].y<lo_z:
                    lo_z=v[s][r].y
                
        # scale all data 0-1
        for s in range(sdim):
            for r in range(rsem):
                uv[s][r].t=(uv[s][r].t-lo_y)/(hi_y-lo_y)

        if (is_wpn or
            ((p in DEFfmt.partNacelles) and
             (self.acf.engn[p-DEFfmt.partNace1].engn_type in [4,5]))):
            # do LINE-LENGTH for the nacelles and weapons
            line_length_now =0.0
            line_length_tot =0.0
            for s in range(sdim-1):
                line_length_tot+=hypot(v[s+1][0].z-v[s][0].z,
                                       v[s+1][0].y-v[s][0].y)
            for s in range(sdim):
                for r in range(rsem):
                    uv[s][r].s=line_length_now/line_length_tot
                if s<sdim-1:
                    line_length_now+=hypot(v[s+1][0].z-v[s][0].z,
                                           v[s+1][0].y-v[s][0].y)
        elif hi_z!=lo_z:
            # do long-location
            for s in range(sdim):
                for r in range(rsem):
                    uv[s][r].s=(hi_z-v[s][r].y)/(hi_z-lo_z)
        else:
            for s in range(sdim):
                for r in range(rsem):
                    uv[s][r].s=0

        # Scale
        r=UV(part.top_s1,part.top_t1)
        l=UV(part.bot_s1,part.bot_t1)
        rs=UV(part.top_s2-part.top_s1,part.top_t2-part.top_t1)
        ls=UV(part.bot_s2-part.bot_s1,part.bot_t2-part.bot_t1)
        ruv=[]
        luv=[]
        for i in range(sdim):
            ruv.append([])
            luv.append([])
            for j in range(rsem):
                ruv[i].append(r+rs*uv[i][j])
                luv[i].append(l+ls*uv[i][j])


        # Dodgy LOD heuristics

        # offsets less than this (or neg) make body blunt
        blunt_front=0.1
        
        isblunt=0
        point1=0
        miny=99999
        maxy=-99999
        for i in range(sdim):
            if v[i][0].y > maxy: maxy=v[i][0].y
            if v[i][0].y < miny: miny=v[i][0].y
        length=maxy-miny

        for i in range(sdim/2,0,-1):
            if v[i][0].y>=v[i-1][0].y-blunt_front:
                isblunt=1
                point1=i
                break

        if isblunt:
            if self.debug: print "Blunt front %s," % point1,
            body_pt2=0.33
            body_pt3=0.50
        else:
            if self.debug: print "Sharp front,",
            body_pt2=0.30
            body_pt3=0.67
            
        # Find front of cabin
        point2=point1+1
        for i in range(point1,sdim-1):
            if v[i][0].y<=v[0][0].y-length*body_pt2:
                point2=i
                break
        point2=point2-1

        # Find ends of main body
        point3=point2+1
        for i in range(point3,sdim-1):
            if v[i][0].y<=v[0][0].y-length*body_pt3:
                point3=i
                break
        for i in range(point3,sdim-1):
            if v[i][0].y<v[i+1][0].y:
                point3=i
                if self.debug: print "Blunt end %s" % point3
                break
        else:
            if self.debug: print "Sharp end %s" % point3

        # Finally...
        for layer in [ACFimport.LAYER1, ACFimport.LAYER2, ACFimport.LAYER3]:

            # More dodgy LOD heuristics
            if layer==ACFimport.LAYER1:
                # Max detail
                jstep=1
                seq=range(sdim)
                if self.isscenery:
                    mkr=ACFimport.LAYER1MKR+imagemkr
                else:
                    mkr=""

            elif layer==ACFimport.LAYER2:
                if length<ACFimport.THRESH2 or not self.isscenery:
                    break	# Don't do small bodies
                elif p in DEFfmt.partFairings:
                    break	# Don't do fairings since we don't do gear
                elif (is_wpn and watt and
                      watt.watt_con in DEFfmt.conGear+DEFfmt.conWheel):
                    break	# Don't do weapons attached to gear
                elif (not is_wpn and
                      part.patt_con in DEFfmt.conGear+DEFfmt.conWheel):
                    break	# Don't do bodies attached to gear
                elif (p==DEFfmt.partFuse or
                      length>ACFimport.THRESH3 or
                      rdim<=8):
                    jstep=2		# octagon
                else:
                    # Make other bodies simple
                    jstep=rdim/4	# squareoid

                if isblunt:
                    seq=[0,point1,point2,point3,sdim-1]
                else:
                    seq=[0,point2,point3,sdim-1]
                mkr=ACFimport.LAYER2MKR+imagemkr
                
            else:     # ACFimport.LAYER3
                # Don't do small bodies
                if length<ACFimport.THRESH3:
                    break
                elif rdim<=8:
                    jstep=2		# octagon
                else:
                    jstep=rdim/4	# squareoid
                if isblunt:
                    seq=[0,point1,point2,point3,sdim-1]
                else:
                    seq=[0,point2,point3,sdim-1]
                mkr=ACFimport.LAYER3MKR+imagemkr

            mesh=NMesh.New(meshname+mkr)

            # Hack: do body from middle out to help v7 export strip algorithm
            ir=range(len(seq)/2-1,len(seq)-1)
            ir.extend(range(len(seq)/2-2,-1,-1))
            jr=range(int(rdim/4),int(rdim/2)+1-jstep,jstep)
            jr.extend(range(0,int(rdim/4)+1-jstep,jstep))
            jr.extend(range(int(rdim*3/4),rdim+1-jstep,jstep))
            jr.extend(range(int(rdim/2),int(rdim*3/4)+1-jstep,jstep))
            if self.debug: print rdim, jstep, jr

            for i in ir:		# was range(len(seq)-1):
                for j in jr:	# was range(0,n,jstep):
                    fv=[v[seq[i]][j], v[seq[i+1]][j],
                        v[seq[i+1]][(j+jstep)%rdim], v[seq[i]][(j+jstep)%rdim]]
                    if j<rdim/2:
                        fuv=[ruv[seq[i]][j],
                             ruv[seq[i+1]][j],
                             ruv[seq[i+1]][j+jstep],
                             ruv[seq[i]][j+jstep]]
                    else:
                        fuv=[luv[seq[i]][rdim-j],
                             luv[seq[i+1]][rdim-j],
                             luv[seq[i+1]][rdim-jstep-j],
                             luv[seq[i]][rdim-jstep-j]]

                    self.addFace(mesh, fv, fuv, image)

            # Weapon fins
            if is_wpn and layer==ACFimport.LAYER1:
                for fin in range(DEFfmt.wpnfinDIM):
                    if not wpn.mis_fin_semilen[fin]:
                        continue
                    wpn.mis_fin_dihed[fin][1]=180-wpn.mis_fin_dihed[fin][1]
                    root=Vertex(0,0,wpn.mis_fin_z[fin],self.mm)
                    s_os=fin*(42.0/512.0)
                    for side in [0,1]:
                        tip=Vertex(RotationMatrix(wpn.mis_fin_dihed[fin][side], 3, 'y') *
                                   RotationMatrix(wpn.mis_fin_sweep[fin], 3, 'z') *
                                   Vector([wpn.mis_fin_semilen[fin]*self.scale,0,0]))
                        # leading root & tip, trailing tip & root
                        vf=[root+Vertex(0.0,    wpn.mis_fin_cr[fin]*self.scale/4,         0.0),
                            root+Vertex(tip.x,  wpn.mis_fin_ct[fin]*self.scale/4  +tip.y, tip.z),
                            root+Vertex(tip.x, -wpn.mis_fin_ct[fin]*self.scale*3/4+tip.y, tip.z),
                            root+Vertex(0.0,   -wpn.mis_fin_cr[fin]*self.scale*3/4,       0.0)]

                        uvf=[UV(0.5137+s_os, 0.5), UV(0.5137+s_os, 0.0),
                             UV(0.5898+s_os, 0.0), UV(0.5898+s_os, 0.5)]
                        self.addFace(mesh, vf, uvf, image)
                        vf.reverse()
                        uvf=[UV(0.5898+s_os, 0.5), UV(0.5898+s_os, 1.0),
                             UV(0.5137+s_os, 1.0), UV(0.5137+s_os, 0.5)]
                        self.addFace(mesh, vf, uvf, image)

            if is_wpn:
                self.meshcache[wpnname].append(mesh)
            else:
                self.meshcache[p].append(mesh)
            self.addMesh(obname+mkr, mesh, layer, mm)


    #------------------------------------------------------------------------
    def doGear(self, p):

        gear=self.acf.gear[p]
        if not gear.gear_type:
            return
        elif gear.gear_type==DEFfmt.GR_skid:
            strutratio=1	# skid
        else:
            strutratio=0.2

        name="Gear %s" % (p+1)
        if self.debug: print name
        
        mm=TranslationMatrix((Vertex(gear.gear_x,
                                     gear.gear_y,
                                     gear.gear_z,
                                     self.mm)+self.offset).toVector(4))
        mm=RotationMatrix(-gear.latE, 4, 'y')*mm
        mm=RotationMatrix(gear.lonE, 4, 'x')*mm

        
        # Strut
        mesh=NMesh.New("%s strut%s" % (name, ACFimport.LAYER1MKR))
        strutradius=strutratio*gear.tire_radius*self.scale
        strutlen=gear.leg_len*self.scale

        if (self.acf.GEAR_strut_s1[p]==self.acf.GEAR_strut_t1[p]==
            self.acf.GEAR_strut_s2[p]==self.acf.GEAR_strut_t2[p]==0.0):
            (sps, spt, sptw, spth) = (1, 893, 14, 128)	# Hard-coded pre 8.3ish
            s0=sps/1024.0
            t0=(1023-spt)/1024.0
            sw=sptw/1024.0
            t1=t0+spth/1024.0
        else:
            s0=self.acf.GEAR_strut_s1[p]
            t0=self.acf.GEAR_strut_t1[p]
            sw=self.acf.GEAR_strut_s2[p]-self.acf.GEAR_strut_s1[p]
            t1=self.acf.GEAR_strut_t2[p]
        
        for i in range(0,8,2):
            a=RotationMatrix(90+i*45, 3, 'z')
            b=RotationMatrix((90+(i+1)*45)%360, 3, 'z')
            c=RotationMatrix((90+(i+2)*45)%360, 3, 'z')
            v=[]
            v.append(Vertex(a*Vector([strutradius,0.0,0.0])))
            v.append(Vertex(b*Vector([strutradius,0.0,0.0])))
            v.append(Vertex(b*Vector([strutradius,0.0,-strutlen])))
            v.append(Vertex(a*Vector([strutradius,0.0,-strutlen])))
            self.addFace(mesh, v,
                         [UV(s0+ i   *sw/8.0,t0), UV(s0+(i+1)*sw/8.0, t0),
                          UV(s0+(i+1)*sw/8.0,t1), UV(s0+ i   *sw/8.0, t1)],
                         self.image)
            v=[]
            v.append(Vertex(b*Vector([strutradius,0.0,0.0])))
            v.append(Vertex(c*Vector([strutradius,0.0,0.0])))
            v.append(Vertex(c*Vector([strutradius,0.0,-strutlen])))
            v.append(Vertex(b*Vector([strutradius,0.0,-strutlen])))
            self.addFace(mesh, v,
                         [UV(s0+(i+1)*sw/8.0,t0), UV(s0+(i+2)*sw/8.0, t0),
                          UV(s0+(i+2)*sw/8.0,t1), UV(s0+(i+1)*sw/8.0, t1)],
                         self.image)
            
        self.addMesh(mesh.name, mesh, ACFimport.LAYER1, mm)


        # Tires
        if not gear.tire_swidth:
            return

        # Tire layout - layer 1
        
        w=gear.tire_swidth*self.scale
        r=gear.tire_radius*self.scale
        xsep=1.5*w
        ysep=1.2*r

        if gear.gear_type==DEFfmt.GR_single:
            # single
            seq=[Vertex(0,0,0)]
        elif gear.gear_type==DEFfmt.GR_2lat:
            # 2 lateral
            seq=[Vertex(-xsep, 0, 0),
                 Vertex( xsep, 0, 0)]
        elif gear.gear_type==DEFfmt.GR_2long:
            # 2 long
            seq=[Vertex(0, -ysep, 0),
                 Vertex(0,  ysep, 0)]
        elif gear.gear_type==DEFfmt.GR_4truck:
            # 4 truck
            seq=[Vertex(-xsep, -ysep, 0),
                 Vertex(-xsep,  ysep, 0),
                 Vertex(+xsep, -ysep, 0),
                 Vertex(+xsep,  ysep, 0)]
        elif gear.gear_type==DEFfmt.GR_6truck:
            # 6 truck
            seq=[Vertex(-xsep, -2*r, 0),
                 Vertex(-xsep,  2*r, 0),
                 Vertex(-xsep,  0,   0),
                 Vertex(+xsep,  0,   0),
                 Vertex(+xsep, -2*r, 0),
                 Vertex(+xsep,  2*r, 0)]
        elif gear.gear_type==DEFfmt.GR_4lat:
            # 4 lateral
            seq=[Vertex(-xsep*3, 0, 0),
                 Vertex(-xsep,   0, 0),
                 Vertex(+xsep,   0, 0),
                 Vertex(+xsep*3, 0, 0)]
        elif gear.gear_type==DEFfmt.GR_2f4a:
            # 2/4 truck
            seq=[Vertex(-xsep,   -ysep, 0),
                 Vertex(-xsep,    ysep, 0),
                 Vertex(+xsep,   -ysep, 0),
                 Vertex(+xsep,    ysep, 0),
                 Vertex(-xsep*3, -ysep, 0),
                 Vertex(+xsep*3, -ysep, 0)]
        elif gear.gear_type==DEFfmt.GR_3lat:
            # 3 lateral
            seq=[Vertex(-xsep*2, 0, 0),
                 Vertex(0,       0, 0),
                 Vertex(+xsep+2, 0, 0)]
        else:
            # Dunno
            return

        # Don't want to rotate the tire itself. So find centre manually.
        a=RotationMatrix(gear.latE, 3, 'y')
        a=RotationMatrix(-gear.lonE, 3, 'x')*a
        mm=TranslationMatrix((Vertex(gear.gear_x,
                                     gear.gear_y,
                                     gear.gear_z,
                                     self.mm)+
                              Vertex(a*Vector([0,0,-strutlen]))+
                              self.offset).toVector(4))
        mesh=NMesh.New(name+ACFimport.LAYER1MKR)

        if self.acf.HEADER_version<800:	# v7
            wheel=[UV(self.acf.GEAR_wheel_tire_s1[0],
                      self.acf.GEAR_wheel_tire_t1[0]),
                   UV(self.acf.GEAR_wheel_tire_s2[0],
                      self.acf.GEAR_wheel_tire_t1[0]),
                   UV(self.acf.GEAR_wheel_tire_s2[0],
                      self.acf.GEAR_wheel_tire_t2[0]),
                   UV(self.acf.GEAR_wheel_tire_s1[0],
                      self.acf.GEAR_wheel_tire_t2[0])]
            tread=[UV(self.acf.GEAR_wheel_tire_s1[1],
                      self.acf.GEAR_wheel_tire_t1[1]),
                   UV(self.acf.GEAR_wheel_tire_s2[1],
                      self.acf.GEAR_wheel_tire_t1[1]),
                   UV(self.acf.GEAR_wheel_tire_s2[1],
                      self.acf.GEAR_wheel_tire_t2[1]),
                   UV(self.acf.GEAR_wheel_tire_s1[1],
                      self.acf.GEAR_wheel_tire_t2[1])]

            for o in seq:
                for i in range(0,12,2):
                    # Add in pairs in order to mirror textures
                    a=RotationMatrix( i   *30 - 180, 3, 'x')
                    b=RotationMatrix((i+1)*30 - 180, 3, 'x')
                    c=RotationMatrix((i+2)*30 - 180, 3, 'x')

                    # 1st step
                    v=[]
                    v.append(o+Vertex(w,0.0,0.0))	# centre
                    v.append(o+Vertex(b*Vector([ w,0.0,r])))
                    v.append(o+Vertex(a*Vector([ w,0.0,r])))
                    self.addFace(mesh, v,
                                 [wheel[0], wheel[2], wheel[3]],
                                 self.image)
                    v=[]
                    v.append(o+Vertex(-w,0.0,0.0))	# centre
                    v.append(o+Vertex(a*Vector([-w,0.0,r])))
                    v.append(o+Vertex(b*Vector([-w,0.0,r])))
                    self.addFace(mesh, v,
                                 [wheel[0], wheel[2], wheel[3]],
                                 self.image)
                    v=[]
                    v.append(o+Vertex(a*Vector([ w,0.0,r])))
                    v.append(o+Vertex(b*Vector([ w,0.0,r])))
                    v.append(o+Vertex(b*Vector([-w,0.0,r])))
                    v.append(o+Vertex(a*Vector([-w,0.0,r])))
                    self.addFace(mesh, v, tread, self.image)
                    
                    # 2nd step
                    v=[]
                    v.append(o+Vertex(w,0.0,0.0))	# centre
                    v.append(o+Vertex(c*Vector([ w,0.0,r])))
                    v.append(o+Vertex(b*Vector([ w,0.0,r])))
                    self.addFace(mesh, v,
                                 [wheel[0], wheel[3], wheel[2]],
                                 self.image)
                    v=[]
                    v.append(o+Vertex(-w,0.0,0.0))	# centre
                    v.append(o+Vertex(b*Vector([-w,0.0,r])))
                    v.append(o+Vertex(c*Vector([-w,0.0,r])))
                    self.addFace(mesh, v,
                                 [wheel[0], wheel[3], wheel[2]],
                                 self.image)
                    v=[]
                    v.append(o+Vertex(b*Vector([w,0.0,r])))
                    v.append(o+Vertex(c*Vector([w,0.0,r])))
                    v.append(o+Vertex(c*Vector([-w,0.0,r])))
                    v.append(o+Vertex(b*Vector([-w,0.0,r])))
                    self.addFace(mesh, v,
                                 [tread[1], tread[0], tread[3], tread[2]],
                                 self.image)

        else:	# v8
            hr=0.6*r	# radius of hub part (hub width is w)
            tw=0.7*w	# width of tire (tread radius is r)
            
            hubc=UV((self.acf.GEAR_wheel_tire_s1[0]+
                     self.acf.GEAR_wheel_tire_s2[0])/2,
                    (self.acf.GEAR_wheel_tire_t1[0]+
                     self.acf.GEAR_wheel_tire_t2[0])/2)
            hubw=UV((self.acf.GEAR_wheel_tire_s2[0]-
                     self.acf.GEAR_wheel_tire_s1[0])/2,
                    (self.acf.GEAR_wheel_tire_t2[0]-
                     self.acf.GEAR_wheel_tire_t1[0])/2)
            treadw=(self.acf.GEAR_wheel_tire_s2[1]-
                    self.acf.GEAR_wheel_tire_s1[1])/12.0
            tread=[UV(self.acf.GEAR_wheel_tire_s1[1],
                      self.acf.GEAR_wheel_tire_t1[1]+
                      (self.acf.GEAR_wheel_tire_t2[1]-
                       self.acf.GEAR_wheel_tire_t1[1])*0.9),
                   UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                      self.acf.GEAR_wheel_tire_t1[1]+
                      (self.acf.GEAR_wheel_tire_t2[1]-
                       self.acf.GEAR_wheel_tire_t1[1])*0.9),
                   UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                      self.acf.GEAR_wheel_tire_t1[1]+
                      (self.acf.GEAR_wheel_tire_t2[1]-
                       self.acf.GEAR_wheel_tire_t1[1])*0.1),
                   UV(self.acf.GEAR_wheel_tire_s1[1],
                      self.acf.GEAR_wheel_tire_t1[1]+
                      (self.acf.GEAR_wheel_tire_t2[1]-
                       self.acf.GEAR_wheel_tire_t1[1])*0.1)]
            rim1=[UV(self.acf.GEAR_wheel_tire_s1[1],
                     self.acf.GEAR_wheel_tire_t1[1]+
                     (self.acf.GEAR_wheel_tire_t2[1]-
                      self.acf.GEAR_wheel_tire_t1[1])*0.9),
                  UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                     self.acf.GEAR_wheel_tire_t1[1]+
                     (self.acf.GEAR_wheel_tire_t2[1]-
                      self.acf.GEAR_wheel_tire_t1[1])*0.9),
                  UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                     self.acf.GEAR_wheel_tire_t2[1]),
                  UV(self.acf.GEAR_wheel_tire_s1[1],
                     self.acf.GEAR_wheel_tire_t2[1])]
            rim2=[UV(self.acf.GEAR_wheel_tire_s1[1],
                     self.acf.GEAR_wheel_tire_t1[1]),
                  UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                     self.acf.GEAR_wheel_tire_t1[1]),
                  UV(self.acf.GEAR_wheel_tire_s1[1]+treadw,
                     self.acf.GEAR_wheel_tire_t1[1]+
                     (self.acf.GEAR_wheel_tire_t2[1]-
                      self.acf.GEAR_wheel_tire_t1[1])*0.1),
                  UV(self.acf.GEAR_wheel_tire_s1[1],
                     self.acf.GEAR_wheel_tire_t1[1]+
                     (self.acf.GEAR_wheel_tire_t2[1]-
                      self.acf.GEAR_wheel_tire_t1[1])*0.1)]
            
            for o in seq:
                for i in range(12):
                    a=RotationMatrix( i   *30 - 180, 3, 'x')
                    b=RotationMatrix((i+1)*30 - 180, 3, 'x')
                    ua=UV(sin( i   *pi/6), -cos( i   *pi/6))
                    ub=UV(sin((i+1)*pi/6), -cos((i+1)*pi/6))
                    treadi=UV(treadw*((i+6)%12),0)

                    # Hack: do tread first to help v7 export strip algorithm
                    v=[]
                    v.append(o+Vertex(a*Vector([ tw,0.0,r])))
                    v.append(o+Vertex(b*Vector([ tw,0.0,r])))
                    v.append(o+Vertex(b*Vector([-tw,0.0,r])))
                    v.append(o+Vertex(a*Vector([-tw,0.0,r])))
                    self.addFace(mesh, v,
                                 [tread[0]+treadi, tread[1]+treadi,
                                  tread[2]+treadi, tread[3]+treadi],
                                 self.image)

                    v=[]
                    v.append(o+Vertex(w,0.0,0.0))	# centre
                    v.append(o+Vertex(b*Vector([w,0.0,hr])))
                    v.append(o+Vertex(a*Vector([w,0.0,hr])))
                    uv=[hubc]
                    uv.append(hubc+ub*hubw)
                    uv.append(hubc+ua*hubw)
                    self.addFace(mesh, v, uv, self.image)

                    v=[]
                    v.append(o+Vertex(a*Vector([w,0.0,hr])))
                    v.append(o+Vertex(b*Vector([w,0.0,hr])))
                    v.append(o+Vertex(b*Vector([tw,0.0,r])))
                    v.append(o+Vertex(a*Vector([tw,0.0,r])))
                    self.addFace(mesh, v,
                                 [rim1[0]+treadi, rim1[1]+treadi,
                                  rim1[2]+treadi, rim1[3]+treadi],
                                 self.image)

                    v=[]
                    v.append(o+Vertex(-w,0.0,0.0))	# centre
                    v.append(o+Vertex(a*Vector([-w,0.0,hr])))
                    v.append(o+Vertex(b*Vector([-w,0.0,hr])))
                    uv=[hubc]
                    uv.append(hubc+ua*hubw)
                    uv.append(hubc+ub*hubw)
                    self.addFace(mesh, v, uv, self.image)

                    v=[]
                    v.append(o+Vertex(a*Vector([-tw,0.0,r])))
                    v.append(o+Vertex(b*Vector([-tw,0.0,r])))
                    v.append(o+Vertex(b*Vector([-w,0.0,hr])))
                    v.append(o+Vertex(a*Vector([-w,0.0,hr])))
                    self.addFace(mesh, v,
                                 [rim2[0]+treadi, rim2[1]+treadi,
                                  rim2[2]+treadi, rim2[3]+treadi],
                                 self.image)
            
        self.addMesh(mesh.name, mesh, ACFimport.LAYER1, mm)


    #------------------------------------------------------------------------
    def doDoor(self, p):

        door=self.acf.door[p]
        if not door.type in [DEFfmt.gear_door_standard,
                             DEFfmt.gear_door_attached]:
            return

        mm=TranslationMatrix((Vertex(door.xyz, self.mm)+self.offset).toVector(4))
        if p<DEFfmt.doorDIM:
            name="Door %s" % (p+1)
            mm=RotationMatrix(-door.axi_rot, 4, 'z')*mm
        else:		# Speedbrake - roll not heading
            name="Speedbrake %s" % (p+1)
            mm=RotationMatrix(-door.axi_rot, 4, 'y')*mm
        if self.acf.HEADER_version<800:	# v7
            mm=RotationMatrix(-door.ext_ang, 4, 'y')*mm
        else:
            mm=RotationMatrix(door.ext_ang, 4, 'x')*mm
            
        # just use 4 corners - XXX should adjust UVs for non-rectangular
        v=[]
        for j in [door.geo[0][0],door.geo[0][3],door.geo[3][3],door.geo[3][0]]:
            v.append(Vertex(j, self.mm))

        mesh=NMesh.New(name+ACFimport.LAYER1MKR)
        self.addFace(mesh, v,
                     [UV(door.inn_s1,door.inn_t2),
                      UV(door.inn_s1,door.inn_t1),
                      UV(door.inn_s2,door.inn_t1),
                      UV(door.inn_s2,door.inn_t2)], self.image, False)
        v.reverse()
        self.addFace(mesh, v,
                     [UV(door.out_s2,door.out_t2),
                      UV(door.out_s2,door.out_t1),
                      UV(door.out_s1,door.out_t1),
                      UV(door.out_s1,door.out_t2)], self.image, False)
        self.addMesh(mesh.name, mesh, ACFimport.LAYER1, mm)


    #------------------------------------------------------------------------
    def doObjs(self, p):

        obj=self.acf.objs[p]
        if not obj.obj_name: return
        (name,ext)=splitext(basename(obj.obj_name))
        obname="O%02d %s" % (p+1, name)

        if obj.obj_con in DEFfmt.conWheel:
            # Take location from wheels
            gear=self.acf.gear[obj.obj_con-DEFfmt.conWheel1]
            a=RotationMatrix(gear.latE, 3, 'y')
            a=RotationMatrix(-gear.lonE, 3, 'x')*a
            mm=TranslationMatrix((Vertex(obj.obj_x,
                                         obj.obj_y,
                                         obj.obj_z,
                                         self.mm)+self.offset+
                                  Vertex(a * Vector([0,0,-gear.leg_len*self.scale]))).toVector(4))
        else:
            mm=TranslationMatrix((Vertex(obj.obj_x,
                                         obj.obj_y,
                                         obj.obj_z,
                                         self.mm)+self.offset).toVector(4))
        mm=self.rotate(obj.obj_con, False,
                       obj.obj_psi, obj.obj_the, obj.obj_phi)*mm

        try:
            OBJimport(join(dirname(self.filename), 'objects', obj.obj_name), mm).doimport()
        except:
            print "Warn:\tCouldn't read object \"%s\"" % obj.obj_name
            return
        # Should create armature when linked to a control surface?


    #------------------------------------------------------------------------
    def doLight(self, p):
        (name, part, r, g, b, hasattach)=DEFfmt.lites[p]
        if not eval("self.acf.VIEW_has_%s" % part):
            return

        if hasattach:
            con=eval("self.acf.VIEW_%s_con" % part)
        else:
            con=0

        if con:
            gear=self.acf.gear[con-1]
            a=RotationMatrix(gear.latE, 3, 'y')
            a=RotationMatrix(-gear.lonE, 3, 'x')*a
            centre=(Vertex(gear.gear_x,
                           gear.gear_y,
                           gear.gear_z, self.mm)+self.offset+
                    Vertex(a * Vector(eval("self.acf.VIEW_%s_xyz" % part)),
                           self.mm))
        else:
            centre=(self.offset +
                    Vertex(eval("self.acf.VIEW_%s_xyz" % part), self.mm))
            
        self.addLamp(name, r, g, b, centre)


    #------------------------------------------------------------------------
    def rotate(self, con, pre, heading, pitch, roll):
        # Use quaternions to prevent gimbal lock
        # Sigh, Quaternion multiplication appears screwed in 2.41

        if con in DEFfmt.conGear:	# gear
            gear=self.acf.gear[con-DEFfmt.conGear1]
        elif con in DEFfmt.conWheel:	# wheel
            gear=self.acf.gear[con-DEFfmt.conWheel1]
        else:				# something else
            h=Quaternion(-heading, [0,0,1])
            p=Quaternion(pitch, [1,0,0])
            r=Quaternion(roll, [0,1,0])
            rot=quatmult(quatmult(h,p),r)    # Roll applies first
            return rot.toMatrix().resize4x4()

        if pre:
            # Gear rotation is applied before Misc body rotation!
            mm=RotationMatrix(-heading, 4, 'z')
            mm=RotationMatrix(gear.lonE-90+pitch, 4, 'x')*mm	# from upright
            mm=RotationMatrix(-gear.latE+roll, 4, 'z')*mm
            if gear.latE>0:
                mm=RotationMatrix(90 -180*atan(gear.lonE/gear.latE)/pi, 4, 'y')*mm
            elif gear.latE<0:
                mm=RotationMatrix(270-180*atan(gear.lonE/gear.latE)/pi, 4, 'y')*mm
            else:
                mm=RotationMatrix(180, 4, 'y')*mm
        else:
            # Wpn and Obj rotation applied before gear rotation
            mm=RotationMatrix(gear.lonE-90, 4, 'x')	# from upright
            mm=RotationMatrix(-gear.latE, 4, 'z')*mm
            if gear.latE>0:
                mm=RotationMatrix(90 -180*atan(gear.lonE/gear.latE)/pi, 4, 'y')*mm
            elif gear.latE<0:
                mm=RotationMatrix(270-180*atan(gear.lonE/gear.latE)/pi, 4, 'y')*mm
            else:
                mm=RotationMatrix(180, 4, 'y')*mm
            mm=RotationMatrix(-heading, 4, 'z')*mm
            mm=RotationMatrix(pitch, 4, 'x')*mm
            mm=RotationMatrix(roll, 4, 'y')*mm

        return mm

    
    #------------------------------------------------------------------------
    def addLamp(self, name, r, g, b, centre):
        lamp=Lamp.New("Lamp", name)
        lamp.col=[r,g,b]
        lamp.dist = 4.0	# arbitrary - stop colouring whole plane
        #lamp.mode |= Lamp.Modes.Sphere
        ob = Object.New("Lamp", lamp.name)
        ob.link(lamp)
        self.scene.objects.link(ob)
        ob.Layer=ACFimport.LAYER1|ACFimport.LAYER2|ACFimport.LAYER3
        ob.setLocation(centre.x, centre.y, centre.z)


    #------------------------------------------------------------------------
    def addMesh(self, name, mesh, layer, mm):
        mesh.mode &= ~(NMesh.Modes.TWOSIDED|NMesh.Modes.AUTOSMOOTH)
        mesh.mode |= NMesh.Modes.NOVNORMALSFLIP
        mesh.update(1)	# recalc normals
        ob = Object.New("Mesh", name)
        ob.link(mesh)
        self.scene.objects.link(ob)
        ob.Layer=layer
        ob.setMatrix(mm)	# no longer sets rot/scale in 2.43
        ob.setLocation(*mm.translationPart())
        v=mm.toEuler()
        ob.rot=((radians(v.x), radians(v.y), radians(v.z)))	# for 2.43
        ob.getMatrix()		# force recalc in 2.43 - see Blender bug #5111
        return ob


    #------------------------------------------------------------------------
    def addFace(self, mesh, fv, fuv, image, remdbl=True):

        # Remove any duplicate vertices
        v=[]
        uv=[]
        for i in range(len(fv)):
            for j in v:
                if j.equals(fv[i]):
                    break
            else:
                v.append(fv[i])
                uv.append(fuv[i])
        if len(v)<3:
            return
    
        face=NMesh.Face()
        face.mode |= NMesh.FaceModes.TEX|NMesh.FaceModes.DYNAMIC
        face.mode &= ~(NMesh.FaceModes.TWOSIDE|NMesh.FaceModes.TILES)
        if remdbl:
            face.smooth=1
        else:
            face.smooth=0
        
        for rv in v:
            for nmv in mesh.verts:
                if remdbl and rv.equals(Vertex(nmv.co[0],nmv.co[1],nmv.co[2])):
                    nmv.co[0]=(nmv.co[0]+rv.x)/2
                    nmv.co[1]=(nmv.co[1]+rv.y)/2
                    nmv.co[2]=(nmv.co[2]+rv.z)/2
                    face.v.append(nmv)
                    break
            else:
                nmv=NMesh.Vert(rv.x,rv.y,rv.z)
                mesh.verts.append(nmv)
                face.v.append(nmv)
                            
        # Have to add them even if no texture
        for rv in uv:
            face.uv.append((rv.s, rv.t))

        if image:
            face.image = image
    
        mesh.faces.append(face)
    

    #------------------------------------------------------------------------
    def addFacePart(self, mesh, v, uv, c1, c2, rw, tw, image, remdbl=True):

        if c1==0 or c1==1:
            nr1=0
            nt1=0
        else:
            nr1=rw
            nt1=tw

        if c2==0 or c2==1:
            nr2=0
            nt2=0
        else:
            nr2=rw
            nt2=tw

        vr=v[3]-v[0]
        vt=v[2]-v[1]
        croot=v[3].y-v[0].y
        ctip=v[2].y-v[1].y
        
        # assumes normal is up (ie no incidence) for simplicity
        nv=[v[0] + vr*c1 + Vertex(0, 0, croot*nr1),
            v[1] + vt*c1 + Vertex(0, 0, ctip *nt1),
            v[1] + vt*c2 + Vertex(0, 0, ctip *nt2),
            v[0] + vr*c2 + Vertex(0, 0, croot*nr2)]

        nuv=[UV(uv[0].s+(uv[3].s-uv[0].s)*c1, uv[0].t),
             UV(uv[1].s+(uv[2].s-uv[1].s)*c1, uv[1].t),
             UV(uv[1].s+(uv[2].s-uv[1].s)*c2, uv[1].t),
             UV(uv[0].s+(uv[3].s-uv[0].s)*c2, uv[0].t)]
            
        self.addFace(mesh, nv, nuv, image, remdbl)


    #------------------------------------------------------------------------
    def afl(self, aflname):
        if not aflname:
            return None
        afldir=self.filename
        while True:
            if dirname(afldir)==afldir: break
            afldir=dirname(afldir)
            for d in listdir(afldir):
                if d.lower()=='airfoils':
                    for f in listdir(join(afldir, d)):
                        if f.lower()==aflname.lower():
                            try:
                                file = open(join(afldir,d,f), 'rU')
                                thing=file.readline(1024)
                                if not thing or thing[0] not in ['A', 'I']:
                                    file.close()
                                    continue
                                thing=file.readline(1024).split()
                                if not thing or thing[0] not in ['700','900']:
                                    file.close()
                                    continue
                                thing=file.readline(1024)	# device type
                                thing=file.readline(1024).split()
                                file.close()
                                return float(thing[1])		# thickness
                            except:
                                pass

        print "Warn:\tCouldn't read airfoil \"%s\"" % aflname
        return None


    #------------------------------------------------------------------------
    def wpn(self, wpnname):
        wpndir=self.filename
        while True:
            if dirname(wpndir)==wpndir: break
            wpndir=dirname(wpndir)
            for d in listdir(wpndir):
                if d.lower()=='weapons':
                    for f in listdir(join(wpndir, d)):
                        if f.lower()==wpnname.lower():
                            try:
                                w=ACF(join(wpndir,d,f), self.debug, None, None, '', None)
                                return w
                            except:
                                pass

        print "Warn:\tCouldn't read weapon \"%s\"" % wpnname
        return None
        

#------------------------------------------------------------------------
#-- DEFfmt --
#------------------------------------------------------------------------
class DEFfmt:
    xchr=0
    xint=1
    xflt=2
    xstruct=3
    
    engnDIM=8		# number of Engines
    wingDIM=56		# number of Wings (incl props)
    partDIM=95		# number of Parts (incl wings)
    gearDIM=10		# number of Gear
    wattDIM=24		# number of Weapons
    doorDIM=20		# number of Doors
    sbrkDIM=4		# number of Speedbrakes
    objsDIM=24		# number of Misc Objects

    partMainWings=range(8,20)	# used for nav light locations
    partRightWings=range(9,19,2)	# used for mirroring
    partMiscWings=range(20,40)
    partPylons=range(40,56)
    partFuse=56			# used in LOD calculation
    partMisc=range(57,77)
    partNace1=77
    partNacelles=range(77,85)	# used in texture mapping
    partFair1=85
    partFairings=range(85,95)

    assert(partFuse>wattDIM)	# differentiate wpns & bodies

    body_sDIM=20	# max number of segments/part
    body_rDIM=18	# max number of vertices/segment
    wpnfinDIM=4		# fins on weapons

    conGear1=14
    conGear=range(14,24)
    conWheel1=25
    conWheel=range(25,35)
    
    # gear
    GR_none  =0
    GR_skid  =1
    GR_single=2
    GR_2lat  =3
    GR_2long =4
    GR_4truck=5
    GR_6truck=6
    GR_4lat  =7
    GR_2f4a  =8
    GR_3lat  =9

    # doors
    gear_door_none=0
    gear_door_standard=1
    gear_door_attached=2
    gear_door_closed=3

    lites=[
        # name          base_value   r    g    b   attach
        ("airplane_landing",  "lanlite1", 1.0, 1.0, 1.0, True),	# was Landing 1
        ("airplane_landing",  "lanlite2", 1.0, 1.0, 1.0, True),	# was Landing 2
        ("airplane_taxi",     "taxilite", 1.0, 1.0, 1.0, True),	# was Taxi
        ("airplane_nav_tail", "taillite", 1.0, 1.0, 1.0, False),# was Tail
        ("airplane_beacon",   "fuserb1",  1.0, 0.0, 0.0, False),# was Rot 1 pulse
        ("airplane_beacon",   "fuserb2",  1.0, 0.0, 0.0, False),# was Rot 2 pulse
        ]

    v7parts={
#v8  v7   s   r tex t_s1 b_s1 t_t1 b_t1 t_s2 b_s2 t_t2 b_t2
 0: ( 0,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 1
 1: ( 1,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 2
 2: ( 2,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 3
 3: ( 3,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 4
 4: ( 4,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 5
 5: ( 5,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 6
 6: ( 6,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 7
 7: ( 7,  0,  0, 0,  16,  16, 262, 262,   0,   0, 389, 389),	# Prop 8
 8: ( 8,  0,  0, 0, 774, 774,   0,   0,1024,1024, 393, 393),	# Wing 1 Left
 9: ( 9,  0,  0, 0, 774, 774,   0,   0,1024,1024, 393, 393),	# Wing 1 Right
10: (10,  0,  0, 0, 522, 522,   0,   0, 772, 772, 259, 259),	# Wing 2 Left
11: (11,  0,  0, 0, 522, 522,   0,   0, 772, 772, 259, 259),	# Wing 2 Right
12: (12,  0,  0, 0, 522, 522, 262, 262, 646, 646, 393, 393),	# Wing 3 Left
13: (13,  0,  0, 0, 522, 522, 262, 262, 646, 646, 393, 393),	# Wing 3 Right
14: (14,  0,  0, 0, 648, 648, 262, 262, 772, 772, 393, 393),	# Wing 4 Left
15: (15,  0,  0, 0, 648, 648, 262, 262, 772, 772, 393, 393),	# Wing 4 Right
16: (16,  0,  0, 0, 774, 774, 522, 522,1024,1024, 772, 772),	# HStab Left
17: (17,  0,  0, 0, 774, 774, 522, 522,1024,1024, 772, 772),	# HStab Right
18: (18,  0,  0, 0,  18, 270,   0,   0, 268, 520, 259, 259),	# VStab 1
19: (19,  0,  0, 0,  18, 270, 261, 261, 268, 520, 520, 520),	# VStab 2
20: (20,  0,  0, 1,   0,   0, 516, 516, 128, 128,1024,1024),	# Misc Wing 1
21: (21,  0,  0, 1, 127, 127, 516, 516, 256, 256,1024,1024),	# Misc Wing 2
22: (22,  0,  0, 1, 255, 255, 516, 516, 384, 384,1024,1024),	# Misc Wing 3
23: (23,  0,  0, 1, 383, 383, 516, 516, 512, 512,1024,1024),	# Misc Wing 4
24: (24,  0,  0, 1, 511, 511, 516, 516, 640, 640,1024,1024),	# Misc Wing 5
25: (25,  0,  0, 1, 639, 639, 516, 516, 768, 768,1024,1024),	# Misc Wing 6
26: (26,  0,  0, 1, 767, 767, 516, 516, 896, 896,1024,1024),	# Misc Wing 7
27: (27,  0,  0, 1, 895, 895, 516, 516,1024,1024,1024,1024),	# Misc Wing 8
40: (28,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 1
41: (29,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 2
42: (30,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 3
43: (31,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 4
44: (32,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 5
45: (33,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 6
46: (34,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 7
47: (35,  0,  0, 0, 774, 774, 458, 458,1024,1024, 520, 520),	# Pylon 1 Egn 8
48: (36,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 1
49: (37,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 2
50: (38,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 3
51: (39,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 4
52: (40,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 5
53: (41,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 6
54: (42,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 7
55: (43,  0,  0, 0, 774, 774, 395, 395,1024,1024, 456, 456),	# Pylon 2 Egn 8
56: (44, 20, 18, 0,   0,   0, 774, 522, 772, 772,1024, 772),	# Fuselage
57: (45, 12, 18, 0, 522, 522, 395, 395, 772, 772, 520, 520),	# Misc Body 1
58: (46, 12, 18, 0, 522, 522, 395, 395, 772, 772, 520, 520),	# Misc Body 2
59: (47, 12, 18, 1, 255, 255,   0,   0, 384, 384, 508, 508),	# Misc Body 3
60: (48, 12, 18, 1, 383, 383,   0,   0, 512, 512, 508, 508),	# Misc Body 4
61: (49, 12, 18, 1, 511, 511,   0,   0, 640, 640, 508, 508),	# Misc Body 5
62: (50, 12, 18, 1, 639, 639,   0,   0, 768, 768, 508, 508),	# Misc Body 6
63: (51, 12, 18, 1, 767, 767,   0,   0, 896, 896, 508, 508),	# Misc Body 7
64: (52, 12, 18, 1, 895, 895,   0,   0,1024,1024, 508, 508),	# Misc Body 8
77: (53, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 1
78: (54, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 2
79: (55, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 3
80: (56, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 4
81: (57, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 5
82: (58, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 6
83: (59, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 7
84: (60, 12, 18, 0, 774, 774, 900, 774,1024,1024,1024, 898),	# Nacelle 8
85: (61,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 1
86: (62,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 2
87: (63,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 3
88: (64,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 4
89: (65,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 5
90: (66,  8, 10, 0,   0,   0, 393, 393,  16,  16, 520, 520),	# Fairing 6
	}

    wings=[
        # name			p
        ("Wing 1 Left",		8),
        ("Wing 1 Right",	9),
        ("Wing 2 Left",		10),
        ("Wing 2 Right",	11),
        ("Wing 3 Left",		12),
        ("Wing 3 Right",	13),
        ("Wing 4 Left",		14),
        ("Wing 4 Right",	15),
        ("HStab Left",		16),
        ("HStab Right",		17),
        ("VStab 1",		18),
        ("VStab 2",		19),
        ("Misc Wing 1",		20),
        ("Misc Wing 2",		21),
        ("Misc Wing 3",		22),
        ("Misc Wing 4",		23),
        ("Misc Wing 5",		24),
        ("Misc Wing 6",		25),
        ("Misc Wing 7",		26),
        ("Misc Wing 8",		27),
        ("Misc Wing 9",		28),
        ("Misc Wing 10",	29),
        ("Misc Wing 11",	30),
        ("Misc Wing 12",	31),
        ("Misc Wing 13",	32),
        ("Misc Wing 14",	33),
        ("Misc Wing 15",	34),
        ("Misc Wing 16",	35),
        ("Misc Wing 17",	36),
        ("Misc Wing 18",	37),
        ("Misc Wing 19",	38),
        ("Misc Wing 20",	39),
        ("Eng 1 Pylon 1",	40),
        ("Eng 2 Pylon 1",	41),
        ("Eng 3 Pylon 1",	42),
        ("Eng 4 Pylon 1",	43),
        ("Eng 5 Pylon 1",	44),
        ("Eng 6 Pylon 1",	45),
        ("Eng 7 Pylon 1",	46),
        ("Eng 8 Pylon 1",	47),
        ("Eng 1 Pylon 2",	48),
        ("Eng 2 Pylon 2",	49),
        ("Eng 3 Pylon 2",	50),
        ("Eng 4 Pylon 2",	51),
        ("Eng 5 Pylon 2",	52),
        ("Eng 6 Pylon 2",	53),
        ("Eng 7 Pylon 2",	54),
        ("Eng 8 Pylon 2",	55),
        ]

    parts=[
        # name 			p
        ("Fuselage",		56),
        ("Misc Body 1",		57),
        ("Misc Body 2",		58),
        ("Misc Body 3",		59),
        ("Misc Body 4",		60),
        ("Misc Body 5",		61),
        ("Misc Body 6",		62),
        ("Misc Body 7",		63),
        ("Misc Body 8",		64),
        ("Misc Body 9",		65),
        ("Misc Body 10",	66),
        ("Misc Body 11",	67),
        ("Misc Body 12",	68),
        ("Misc Body 13",	69),
        ("Misc Body 14",	70),
        ("Misc Body 15",	71),
        ("Misc Body 16",	72),
        ("Misc Body 17",	73),
        ("Misc Body 18",	74),
        ("Misc Body 19",	75),
        ("Misc Body 20",	76),
        ("Nacelle 1",		77),
        ("Nacelle 2",		78),
        ("Nacelle 3",		79),
        ("Nacelle 4",		80),
        ("Nacelle 5",		81),
        ("Nacelle 6",		82),
        ("Nacelle 7",		83),
        ("Nacelle 8",		84),
        ("Fairing 1",		85),
        ("Fairing 2",		86),
        ("Fairing 3",		87),
        ("Fairing 4",		88),
        ("Fairing 5",		89),
        ("Fairing 6",		90),
        ("Fairing 7",		91),
        ("Fairing 8",		92),
        ("Fairing 9",		93),
        ("Fairing 10",		94),
        ]


    #------------------------------------------------------------------------
    # Derived from ACF740.def by Stanislaw Pusep
    #   http://sysd.org/xplane/acftools/ACF740.def
    # and from X-Plane v7 docs
    #   ./Instructions/Manual_Files/X-Plane ACF_format.html
    acf740 = [
#xchr, "HEADER_platform",
#xint, "HEADER_version",
xflt, "HEADER_filler",
xchr, "VIEW_name[500]",
xchr, "VIEW_path[500]",
xchr, "VIEW_tailnum[40]",
xchr, "VIEW_author[500]",
xchr, "VIEW_descrip[500]",
xflt, "VIEW_Vmca_kts",
xflt, "VIEW_Vso_kts",
xflt, "VIEW_Vs_kts",
xflt, "VIEW_Vyse_kts",
xflt, "VIEW_Vfe_kts",
xflt, "VIEW_Vle_kts",
xflt, "VIEW_Vno_kts",
xflt, "VIEW_Vne_kts",
xflt, "VIEW_Mmo",
xflt, "VIEW_Gneg",
xflt, "VIEW_Gpos",
xint, "VIEW_has_navlites",
xflt, "VIEW_pe_xyz[3]",
xint, "VIEW_has_lanlite1",
xflt, "VIEW_lanlite1_xyz[3]",
xint, "VIEW_has_lanlite2",
xflt, "VIEW_lanlite2_xyz[3]",
xint, "VIEW_has_taxilite",
xflt, "VIEW_taxilite_xyz[3]",
xint, "VIEW_has_fuserb1",
xflt, "VIEW_fuserb1_xyz[3]",
xint, "VIEW_has_fuserb2",
xflt, "VIEW_fuserb2_xyz[3]",
xint, "VIEW_has_taillite",
xflt, "VIEW_taillite_xyz[3]",
xint, "VIEW_has_refuel",
xflt, "VIEW_refuel_xyz[3]",
xflt, "VIEW_yawstring_x",
xflt, "VIEW_yawstring_y",
xflt, "VIEW_HUD_ctr_x",
xflt, "VIEW_HUD_ctr_y_OLD",
xflt, "VIEW_HUD_del_x",
xflt, "VIEW_HUD_del_y",
xint, "VIEW_lan_lite_steers",
xflt, "VIEW_lan_lite_power",
xflt, "VIEW_lan_lite_width",
xflt, "VIEW_lan_lite_the_ref",
xflt, "VIEW_stall_warn_aoa",
xflt, "VIEW_tow_hook_Y",
xflt, "VIEW_tow_hook_Z",
xflt, "VIEW_win_hook_Y",
xflt, "VIEW_win_hook_Z",
xint, "VIEW_has_HOOPS_HUD",
xint, "VIEW_cockpit_type",
xint, "VIEW_asi_is_kts",
xint, "VIEW_warn1_EQ",
xint, "VIEW_warn2_EQ",
xint, "VIEW_is_glossy",
xint, "VIEW_draw_geo_frnt_views",
xint, "VIEW_draw_geo_side_views",
xint, "VIEW_ins_type[300]",
xflt, "VIEW_ins_size[300]",
xflt, "VIEW_ins_x[300]",
xflt, "VIEW_ins_y[300]",
xint, "VIEW_cus_rnd_use[50]",
xflt, "VIEW_cus_rnd_lo_val[50]",
xflt, "VIEW_cus_rnd_hi_val[50]",
xflt, "VIEW_cus_rnd_lo_ang[50]",
xflt, "VIEW_cus_rnd_hi_ang[50]",
xint, "VIEW_cus_rnd_mirror[50]",
xint, "VIEW_cus_rnd_label[50]",
xint, "VIEW_cus_dig_use[50]",
xflt, "VIEW_cus_dig_offset[50]",
xflt, "VIEW_cus_dig_scale[50]",
xint, "VIEW_cus_dig_dig[50]",
xint, "VIEW_cus_dig_dec[50]",
xint, "ENGINE_num_engines",
xint, "ENGINE_num_thrustpoints",
xflt, "ENGINE_throt_max_FWD",
xflt, "ENGINE_throt_max_REV",
xflt, "ENGINE_idle_rat[2]",
xint, "ENGINE_linked_prop_EQ",
xint, "ENGINE_beta_prop_EQ",
xint, "ENGINE_auto_feather_EQ",
xint, "ENGINE_rev_thrust_EQ",
xint, "ENGINE_drive_by_wire_EQ",
xflt, "ENGINE_feathered_pitch",
xflt, "ENGINE_reversed_pitch",
xflt, "ENGINE_rotor_mi_rat",
xflt, "ENGINE_tip_weight",
xflt, "ENGINE_tip_mach_des_100",
xflt, "ENGINE_tip_mach_des_50",
xflt, "ENGINE_power_max",
xflt, "ENGINE_crit_alt",
xflt, "ENGINE_MP_max",
xflt, "ENGINE_trq_max_eng",
xflt, "ENGINE_RSC_idlespeed_ENGN",
xflt, "ENGINE_RSC_redline_ENGN",
xflt, "ENGINE_RSC_idlespeed_PROP",
xflt, "ENGINE_RSC_redline_PROP",
xflt, "ENGINE_RSC_mingreen_ENGN",
xflt, "ENGINE_RSC_maxgreen_ENGN",
xflt, "ENGINE_RSC_mingreen_PROP",
xflt, "ENGINE_RSC_maxgreen_PROP",
xint, "AUTO_has_press_controls",
xflt, "ENGINE_throt_time_prop",
xflt, "ENGINE_trans_loss",
xflt, "ENGINE_thrust_max",
xflt, "ENGINE_burner_inc",
xflt, "ENGINE_max_mach_eff",
xflt, "ENGINE_face_jet",
xflt, "ENGINE_throt_time_jet",
xflt, "ENGINE_lift_fan_rat",
xflt, "ENGINE_rock_max_sl",
xflt, "ENGINE_rock_max_opt",
xflt, "ENGINE_rock_max_vac",
xflt, "ENGINE_rock_h_opt",
xflt, "ENGINE_face_rocket",
xint, "PROP_engn_type[8]",
xint, "PROP_prop_type[8]",
xflt, "PROP_engn_mass[8]",
xint, "PROP_prop_clutch_EQ[8]",
xflt, "PROP_prop_gear_rat[8]",
xflt, "PROP_prop_dir[8]",
xflt, "PROP_num_blades[8]",
xflt, "PROP_SFC[8]",
xflt, "PROP_vert_cant_init[8]",
xflt, "PROP_side_cant_init[8]",
xflt, "PROP_min_pitch[8]",
xflt, "PROP_max_pitch[8]",
xflt, "PROP_des_rpm_prp[8]",
xflt, "PROP_des_kts_prp[8]",
xflt, "PROP_des_kts_acf[8]",
xflt, "PROP_prop_mass[8]",
xflt, "PROP_mi_prop_rpm[8]",
xflt, "PROP_mi_engn_rpm[8]",
xflt, "PROP_discarea[8]",
xflt, "PROP_ringarea[8][10]",
xflt, "PROP_bladesweep[8][10]",
xflt, "SYSTEMS_starter_rat",
xflt, "SYSTEMS_battery_rat",
xint, "SYSTEMS_hydraulic_sys",
xint, "SYSTEMS_stickshaker",
xflt, "SYSTEMS_manual_reversion_rat",
xflt, "SYSTEMS_max_press_diff",
xint, "PARTS_part_eq[73]",
xchr, "PARTS_Rafl0[73][40]",
xchr, "PARTS_Rafl1[73][40]",
xchr, "PARTS_Tafl0[73][40]",
xchr, "PARTS_Tafl1[73][40]",
xint, "PARTS_els[73]",
xflt, "PARTS_Xarm[73]",
xflt, "PARTS_Yarm[73]",
xflt, "PARTS_Zarm[73]",
xflt, "PARTS_Croot[73]",
xflt, "PARTS_Ctip[73]",
xflt, "PARTS_semilen_SEG[73]",
xflt, "PARTS_semilen_JND[73]",
xflt, "PARTS_element_len[73]",
xflt, "PARTS_X_body_aero[73]",
xflt, "PARTS_Y_body_aero[73]",
xflt, "PARTS_Z_body_aero[73]",
xflt, "PARTS_dihed1[73]",
xflt, "PARTS_dihed2[73]",
xflt, "PARTS_dihednow[73]",
xint, "PARTS_vardihed[73]",
xint, "CONTROLS_vardihedEQ",
xflt, "PARTS_sweep1[73]",
xflt, "PARTS_sweep2[73]",
xflt, "PARTS_sweepnow[73]",
xint, "PARTS_varsweep[73]",
xint, "CONTROLS_varsweepEQ",
xflt, "PARTS_e[73]",
xflt, "PARTS_AR[73]",
xflt, "PARTS_al_D_al0[73]",
xflt, "PARTS_cl_D_cl0[73]",
xflt, "PARTS_cm_D_cm0[73]",
xflt, "PARTS_delta_fac[73]",
xflt, "PARTS_spec_wash[73]",
xflt, "PARTS_alpha_max[73]",
xflt, "PARTS_slat_effect[73]",
xflt, "PARTS_s[73][10]",
xflt, "PARTS_mac[73][10]",
xflt, "PARTS_incidence[73][10]",
xint, "PARTS_ail1[73][10]",
xflt, "PARTS_ail1_elR[73]",
xflt, "PARTS_ail1_elT[73]",
xflt, "CONTROLS_ail1_cratR",
xflt, "CONTROLS_ail1_cratT",
xflt, "CONTROLS_ail1_up",
xflt, "CONTROLS_ail1_dn",
xint, "PARTS_ail2[73][10]",
xflt, "PARTS_ail2_elR[73]",
xflt, "PARTS_ail2_elT[73]",
xflt, "CONTROLS_ail2_cratR",
xflt, "CONTROLS_ail2_cratT",
xflt, "CONTROLS_ail2_up",
xflt, "CONTROLS_ail2_dn",
xint, "PARTS_elv1[73][10]",
xflt, "PARTS_elv1_elR[73]",
xflt, "PARTS_elv1_elT[73]",
xflt, "CONTROLS_elv1_cratR",
xflt, "CONTROLS_elv1_cratT",
xflt, "CONTROLS_elv1_up",
xflt, "CONTROLS_elv1_dn",
xint, "PARTS_rud1[73][10]",
xflt, "PARTS_rud1_elR[73]",
xflt, "PARTS_rud1_elT[73]",
xflt, "CONTROLS_rud1_cratR",
xflt, "CONTROLS_rud1_cratT",
xflt, "CONTROLS_rud1_lft",
xint, "PARTS_spo1[73][10]",
xflt, "PARTS_spo1_elR[73]",
xflt, "PARTS_spo1_elT[73]",
xflt, "CONTROLS_spo1_cratR",
xflt, "CONTROLS_spo1_cratT",
xflt, "CONTROLS_spo1_up",
xint, "PARTS_yawb[73][10]",
xflt, "PARTS_yawb_elR[73]",
xflt, "PARTS_yawb_elT[73]",
xflt, "CONTROLS_yawb_cratR",
xflt, "CONTROLS_yawb_cratT",
xflt, "CONTROLS_yawb_ud",
xint, "PARTS_sbrk[73][10]",
xflt, "PARTS_sbrk_elR[73]",
xflt, "PARTS_sbrk_elT[73]",
xflt, "CONTROLS_sbrk_cratR",
xflt, "CONTROLS_sbrk_cratT",
xflt, "CONTROLS_sbrk_up",
xint, "CONTROLS_sbrk_EQ",
xint, "PARTS_fla1[73][10]",
xflt, "PARTS_fla1_elR[73]",
xflt, "PARTS_fla1_elT[73]",
xflt, "CONTROLS_fla1_cratR",
xflt, "CONTROLS_fla1_cratT",
xflt, "CONTROLS_fla1_dn[8]",
xint, "CONTROLS_flap_EQ",
xint, "PARTS_slat[73][10]",
xflt, "CONTROLS_slat_inc",
xint, "CONTROLS_slat_EQ",
xint, "PARTS_inc_ail1[73][10]",
xint, "PARTS_inc_ail2[73][10]",
xint, "PARTS_inc_elev[73][10]",
xint, "PARTS_inc_rudd[73][10]",
xint, "PARTS_inc_vect[73][10]",
xint, "PARTS_inc_trim[73][10]",
xint, "CONTROLS_in_downwash[73][73][10]",
xflt, "PARTS_body_r[73]",
xflt, "PARTS_body_X[73][20][18]",
xflt, "PARTS_body_Y[73][20][18]",
xflt, "PARTS_body_Z[73][20][18]",
xint, "PARTS_gear_type[73]",
xflt, "PARTS_gear_latE[73]",
xflt, "PARTS_gear_lonE[73]",
xflt, "PARTS_gear_axiE[73]",
xflt, "PARTS_gear_latR[73]",
xflt, "PARTS_gear_lonR[73]",
xflt, "PARTS_gear_axiR[73]",
xflt, "PARTS_gear_latN[73]",
xflt, "PARTS_gear_lonN[73]",
xflt, "PARTS_gear_axiN[73]",
xflt, "PARTS_gear_xnodef[73]",
xflt, "PARTS_gear_ynodef[73]",
xflt, "PARTS_gear_znodef[73]",
xflt, "PARTS_gear_leglen[73]",
xflt, "PARTS_tire_radius[73]",
xflt, "PARTS_tire_swidth[73]",
xflt, "PARTS_gearcon[73]",
xflt, "PARTS_geardmp[73]",
xflt, "PARTS_gear_deploy[73]",
xflt, "PARTS_gearstatdef[73]",
xflt, "PARTS_dummy[73]",
xint, "PARTS_gear_steers[73]",
xflt, "PARTS_gear_cyctim[73]",
xflt, "BODIES_fuse_cd",
xflt, "CONTROLS_hstb_trim_up",
xflt, "CONTROLS_hstb_trim_dn",
xint, "CONTROLS_flap_type",
xint, "CONTROLS_con_smooth",
xint, "CONTROLS_flap_detents",
xflt, "CONTROLS_flap_deftime",
xflt, "CONTROLS_flap_cl",
xflt, "CONTROLS_flap_cd",
xflt, "CONTROLS_flap_cm",
xflt, "CONTROLS_blown_flap_add_speed",
xflt, "CONTROLS_blown_flap_throt_red",
xflt, "CONTROLS_blown_flap_min_engag",
xint, "CONTROLS_blow_all_controls",
xint, "GEAR_gear_retract",
xflt, "GEAR_nw_steerdeg1",
xflt, "GEAR_nw_steerdeg2",
xflt, "GEAR_nw_cutoff_omega",
xflt, "GEAR_nw_side_k",
xflt, "GEAR_gear_door_size",
xflt, "GEAR_water_rud_Z",
xflt, "GEAR_water_rud_area",
xflt, "GEAR_water_rud_maxdef",
xflt, "GEAR_roll_co",
xflt, "GEAR_brake_co",
xint, "GEAR_gear_door_typ[10]",
xflt, "GEAR_gear_door_loc[10][3]",
xflt, "GEAR_gear_door_geo[10][4][3]",
xflt, "GEAR_gear_door_axi_rot[10]",
xflt, "GEAR_gear_door_ext_ang[10]",
xflt, "GEAR_gear_door_ret_ang[10]",
xflt, "GEAR_gear_door_ang_now[10]",
xflt, "WB_cgY",
xflt, "WB_cgZ",
xflt, "WB_cgZ_fwd",
xflt, "WB_cgZ_aft",
xflt, "WB_m_empty",
xflt, "WB_m_fuel_tot",
xflt, "WB_m_jettison",
xflt, "WB_m_max",
xflt, "WB_m_displaced",
xflt, "WB_Jxx_unitmass",
xflt, "WB_Jyy_unitmass",
xflt, "WB_Jzz_unitmass",
xint, "WB_num_tanks",
xflt, "WB_tank_rat[3]",
xflt, "WB_tank_X[3]",
xflt, "WB_tank_Y[3]",
xflt, "WB_tank_Z[3]",
xint, "WB_jett_is_slung",
xint, "WB_jett_is_water",
xflt, "WB_jett_len",
xflt, "WB_jett_xyz[3]",
xflt, "SPECIAL_flap1_roll",
xflt, "SPECIAL_flap1_ptch",
xflt, "SPECIAL_m_shift",
xflt, "SPECIAL_m_shift_dx",
xflt, "SPECIAL_m_shift_dz",
xflt, "SPECIAL_wing_tilt_ptch",
xflt, "SPECIAL_wing_tilt_roll",
xflt, "SPECIAL_tvec_ptch",
xflt, "SPECIAL_tvec_roll",
xflt, "SPECIAL_tvec_hdng",
xflt, "SPECIAL_jato_Y",
xflt, "SPECIAL_jato_Z",
xflt, "SPECIAL_jato_theta",
xflt, "SPECIAL_jato_thrust",
xflt, "SPECIAL_jato_dur",
xflt, "SPECIAL_jato_sfc",
xflt, "SPECIAL_stab_roll",
xflt, "SPECIAL_stab_hdng",
xflt, "SPECIAL_elev_with_flap_rat",
xflt, "SPECIAL_ail1_pitch",
xflt, "SPECIAL_ail1_flaps",
xflt, "SPECIAL_ail2_pitch",
xflt, "SPECIAL_ail2_flaps",
xflt, "SPECIAL_ail2_vmax",
xflt, "SPECIAL_diff_thro_hdng",
xint, "SPECIAL_phase_ptch_tvect_in_at_90",
xint, "SPECIAL_phase_ptch_tvect_in_at_00",
xint, "SPECIAL_sbrk_on_td_EQ",
xint, "SPECIAL_fbrk_on_td_EQ",
xint, "SPECIAL_sweep_with_flaps_EQ",
xint, "SPECIAL_flaps_with_gear_EQ",
xint, "SPECIAL_slat_with_stall_EQ",
xint, "SPECIAL_anti_ice_EQ",
xint, "SPECIAL_arresting_EQ",
xint, "SPECIAL_revt_on_td_EQ",
xint, "SPECIAL_warn_gear_EQ",
xint, "SPECIAL_warn_lorot_EQ",
xint, "SPECIAL_auto_trim_EQ",
xint, "SPECIAL_flaps_with_vec_EQ",
xflt, "SPECIAL_brake_area",
xflt, "SPECIAL_brake_Y",
xflt, "SPECIAL_brake_Z",
xflt, "SPECIAL_chute_area",
xflt, "SPECIAL_chute_Y",
xflt, "SPECIAL_chute_Z",
xint, "VTOL_vect_EQ",
xint, "VTOL_auto_rpm_with_tvec",
xint, "VTOL_hide_prop_at_90_vect",
xflt, "VTOL_vect_rate",
xflt, "VTOL_vect_min_disc",
xflt, "VTOL_vect_max_disc",
xflt, "VTOL_vectarmY",
xflt, "VTOL_vectarmZ",
xflt, "VTOL_cyclic_def_elev",
xflt, "VTOL_cyclic_def_ailn",
xflt, "VTOL_flap_arm",
xflt, "VTOL_delta3",
xflt, "VTOL_puff_LMN[3]",
xflt, "VTOL_puff_xyz[3]",
xflt, "VTOL_stab_delinc_to_Vne",
xflt, "VTOL_tail_with_coll",
xflt, "VTOL_diff_coll_with_roll",
xflt, "VTOL_diff_coll_with_hdng",
xflt, "VTOL_diff_coll_with_ptch",
xflt, "VTOL_diff_cycl_with_hdng_lon",
xflt, "VTOL_diff_cycl_with_hdng_lat",
xflt, "VTOL_rotor_trim_max_fwd",
xflt, "VTOL_rotor_trim_max_aft",
xflt, "ASTAB_AShiV_old_all",
xflt, "ASTAB_ASloV_old_all",
xflt, "ASTAB_ASlo_max_thedot",
xflt, "ASTAB_ASlo_thedot_k",
xflt, "ASTAB_ASlo_max_psidot",
xflt, "ASTAB_ASlo_psidot_k",
xflt, "ASTAB_ASlo_max_phidot",
xflt, "ASTAB_ASlo_phidot_k",
xflt, "ASTAB_AShi_max_G",
xflt, "ASTAB_AShi_G_k",
xflt, "ASTAB_AShi_Gdot_k",
xflt, "ASTAB_AShi_max_alpha",
xflt, "ASTAB_AShi_alpha_k",
xflt, "ASTAB_AShi_alphadot_k",
xflt, "ASTAB_AShi_max_beta",
xflt, "ASTAB_AShi_beta_k",
xflt, "ASTAB_AShi_betadot_k",
xflt, "ASTAB_AShi_max_phidot",
xflt, "ASTAB_AShi_phidot_k",
xchr, "WEAPONS_wpn_name[24][500]",
xflt, "WEAPONS_x_wpn_att[24]",
xflt, "WEAPONS_y_wpn_att[24]",
xflt, "WEAPONS_z_wpn_att[24]",
xflt, "AUTO_est_Vs_msc",
xflt, "AUTO_size_x",
xflt, "AUTO_size_z",
xflt, "AUTO_tire_s_contact",
xflt, "WB_m_displaced_y",
xflt, "AUTO_h_eqlbm",
xflt, "AUTO_the_eqlbm",
xint, "AUTO_gear_steer_EN",
xint, "AUTO_skid_EQ",
xint, "AUTO_dummy3[7]",
xint, "AUTO_has_radar",
xint, "AUTO_has_SC_fd",
xint, "AUTO_has_DC_fd",
xint, "AUTO_has_stallwarn",
xint, "AUTO_has_clutch_switch",
xint, "AUTO_has_pre_rotate",
xint, "AUTO_has_idlespeed",
xint, "AUTO_has_FADEC_switch",
xint, "AUTO_has_litemap_tex_1",
xint, "CONTROLS_tailrotor_EQ",
xint, "CONTROLS_collective_EQ",
xflt, "ENGINE_snd_kias",
xflt, "ENGINE_snd_rpm_prp",
xflt, "ENGINE_snd_rpm_eng",
xflt, "ENGINE_snd_n1",
xflt, "VAR_INCIDENCE_inc2[73]",
xflt, "VAR_INCIDENCE_incnow[73]",
xint, "VAR_INCIDENCE_varinc[73]",
xint, "CONTROLS_varincEQ",
xflt, "SPECIAL_rudd_with_ailn_rat",
xflt, "OVERFLOW_strut_comp[73]",
xint, "OVERFLOW_is_left[73]",
xflt, "OVERFLOW_lat_sign[73]",
xint, "VTOL_jett_is_acf",
xint, "CONTROLS_collective_en",
xint, "CONTROLS_flying_stab_EQ",
xflt, "OVERFLOW_dummy4[7]",
xflt, "SPECIAL_diff_thro_ptch",
xflt, "SPECIAL_diff_thro_roll",
xint, "SPECIAL_phase_roll_tvect_in_at_90",
xint, "SPECIAL_phase_roll_tvect_in_at_00",
xint, "SPECIAL_phase_hdng_tvect_in_at_90",
xint, "SPECIAL_phase_hdng_tvect_in_at_00",
xint, "AUTO_has_asi_set",
xint, "AUTO_has_hdg_set",
xint, "AUTO_has_alt_set",
xflt, "ASTAB_ASlo_the_V",
xflt, "ASTAB_ASlo_psi_V",
xflt, "ASTAB_ASlo_phi_V",
xflt, "ASTAB_AShi_the_V",
xflt, "ASTAB_AShi_psi_V",
xflt, "ASTAB_AShi_phi_V",
xflt, "SPECIAL_spo1_vmax",
xflt, "ENGINE_max_boost_pas",
xflt, "CONTROLS_min_trim_elev",
xflt, "CONTROLS_max_trim_elev",
xflt, "CONTROLS_min_trim_ailn",
xflt, "CONTROLS_max_trim_ailn",
xflt, "CONTROLS_min_trim_rudd",
xflt, "CONTROLS_max_trim_rudd",
xflt, "VIEW_lan_lite_psi_ref",
xint, "AUTO_has_mixture",
xflt, "OVERFLOW_TR[73]",
xint, "AUTO_gear_EQ",
xint, "VIEW_cus_non_lin[50]",
xint, "VIEW_cus_doub_val[50]",
xint, "AUTO_beacon_EQ",
xint, "AUTO_has_kts_mac",
xflt, "CONTROLS_elev_trim_speedrat",
xflt, "CONTROLS_ailn_trim_speedrat",
xflt, "CONTROLS_rudd_trim_speedrat",
xflt, "WB_disp_rat",
xflt, "ENGINE_exhaust_rat",
xint, "ASTAB_lo_speed_is_position",
xflt, "ASTAB_ASlo_max_the",
xflt, "ASTAB_ASlo_the_k",
xflt, "ASTAB_ASlo_max_phi",
xflt, "ASTAB_ASlo_phi_k",
xint, "OVERFLOW_is_ducted[8]",
xflt, "WEAPONS_the_wpn_att[24]",
xflt, "WEAPONS_psi_wpn_att[24]",
xflt, "VIEW_big_panel_pix_default",
xflt, "VIEW_HUD_ctr_y[9]",
xint, "PARTS_spo2[73][10]",
xflt, "PARTS_spo2_elR[73]",
xflt, "PARTS_spo2_elT[73]",
xflt, "CONTROLS_spo2_cratR",
xflt, "CONTROLS_spo2_cratT",
xflt, "CONTROLS_spo2_up",
xflt, "SPECIAL_spo2_vmax",
xflt, "SPECIAL_ail1_vmax",
xflt, "CONTROLS_roll_to_eng_spo1",
xflt, "CONTROLS_roll_to_eng_spo2",
xflt, "OVERFLOW_dummy2[73]",
xflt, "ENGINE_EPR_max",
xint, "SPECIAL_sweep_with_vect_EQ",
xint, "HEADER_old_cus_layers",
xint, "AUTO_has_litemap_tex_2",
xflt, "VTOL_disc_tilt_elev",
xflt, "VTOL_disc_tilt_ailn",
xflt, "VIEW_lan_lite_psi_off",
xflt, "VIEW_lan_lite_the_off",
xflt, "ENGINE_inertia_rat_prop",
xflt, "ENGINE_fuel_intro_time_jet",
xflt, "OVERFLOW_tire_mi[73]",
xflt, "VTOL_vect_min_nace",
xflt, "VTOL_vect_max_nace",
xint, "WB_manual_rad_gyr",
xflt, "ENGINE_max_ITT",
xflt, "ENGINE_max_EGT",
xflt, "ENGINE_fuel_intro_time_prop",
xflt, "ENGINE_spool_time_jet",
xflt, "CONTROLS_takeoff_trim",
xflt, "AUTO_average_mac_acf",
xint, "OTTO_custom_autopilot",
xflt, "OTTO_ott_asi_ratio",
xflt, "OTTO_ott_asi_sec_into_future",
xflt, "OTTO_ott_asi_kts_off_for_full_def",
xflt, "OTTO_ott_phi_ratio",
xflt, "OTTO_ott_phi_sec_into_future",
xflt, "OTTO_ott_phi_deg_off_for_full_def",
xflt, "OTTO_ott_phi_sec_to_tune",
xflt, "OTTO_ott_def_sec_into_future",
xflt, "OTTO_ott_def_dot_off_for_full_def",
xflt, "OTTO_ott_def_sec_to_tune",
xflt, "OTTO_ott_the_ratio",
xflt, "OTTO_ott_the_sec_into_future",
xflt, "OTTO_ott_the_deg_off_for_full_def",
xflt, "OTTO_ott_the_sec_to_tune",
xflt, "OVERFLOW_xflt_overflow1[2]",
xflt, "VIEW_cockpit_xyz[3]",
xflt, "WEAPONS_roll_wpn_att[24]",
xflt, "OVERFLOW_xflt_overflow2[177]",
xchr, "HEADER_is_hm",
xchr, "HEADER_is_ga",
xchr, "VIEW_ICAO[40]",
xchr, "OVERFLOW_xchr_overflow[2]",
xflt, "OVERFLOW_heading[73]",
xflt, "OVERFLOW_pitch[73]",
xflt, "OVERFLOW_roll[73]",
xflt, "OVERFLOW_xflt_overflow3[20]",
    ]

    #------------------------------------------------------------------------
    # Derived from hl_acf_structs.h
    # with help from Michael Ista
    acf8000 = [	# Note that v8 weapons have HEADER_version==800
#xchr, "HEADER_platform",
#xint, "HEADER_version",
xint, "HEADER_is_hm",
xint, "HEADER_is_ga",
xint, "HEADER_old_cus_layers",

xchr, "VIEW_name[500]",
xchr, "VIEW_path[500]",
xchr, "VIEW_tailnum[40]",
xchr, "VIEW_author[500]",
xchr, "VIEW_descrip[500]",
xchr, "VIEW_ICAO[40]",
xflt, "VIEW_Vmca_kts",
xflt, "VIEW_Vso_kts",
xflt, "VIEW_Vs_kts",
xflt, "VIEW_Vyse_kts",
xflt, "VIEW_Vfe_kts",
xflt, "VIEW_Vle_kts",
xflt, "VIEW_Vno_kts",
xflt, "VIEW_Vne_kts",
xflt, "VIEW_Mmo",
xflt, "VIEW_Gneg",
xflt, "VIEW_Gpos",
xint, "VIEW_has_lanlite1",
xflt, "VIEW_lanlite1_xyz[3]",
xint, "VIEW_has_lanlite2",
xflt, "VIEW_lanlite2_xyz[3]",
xint, "VIEW_has_taxilite",
xflt, "VIEW_taxilite_xyz[3]",
xint, "VIEW_has_fuserb1",
xflt, "VIEW_fuserb1_xyz[3]",
xint, "VIEW_has_fuserb2",
xflt, "VIEW_fuserb2_xyz[3]",
xint, "VIEW_has_taillite",
xflt, "VIEW_taillite_xyz[3]",
xint, "VIEW_has_refuel",
xflt, "VIEW_refuel_xyz[3]",
xint, "VIEW_has_navlites",
xflt, "VIEW_pe_xyz[3]",
xint, "VIEW_cockpit_M_inn",
xflt, "VIEW_cockpit_xyz[3]",
xflt, "VIEW_lanliteC_xyz[3]",
xint, "VIEW_plot_OBJ7_cock[3]",
xint, "VIEW_plot_outer_acf[3]",
xint, "VIEW_plot_inner_acf[3]",
xflt, "VIEW_yawstring_x",
xflt, "VIEW_yawstring_y",
xflt, "VIEW_HUD_ctr_x",
xflt, "VIEW_HUD_ctr_y[9]",
xflt, "VIEW_HUD_del_x",
xflt, "VIEW_HUD_del_y",
xflt, "VIEW_big_panel_pix_default",
xflt, "VIEW_stall_warn_aoa",
xint, "VIEW_lan_lite_steers",
xflt, "VIEW_lan_lite_power",
xflt, "VIEW_lan_lite_width",
xflt, "VIEW_lan_lite_psi_ref",
xflt, "VIEW_lan_lite_psi_off",
xflt, "VIEW_lan_lite_the_ref",
xflt, "VIEW_lan_lite_psi_off",
xflt, "VIEW_tow_hook_Y",
xflt, "VIEW_tow_hook_Z",
xflt, "VIEW_win_hook_Y",
xflt, "VIEW_win_hook_Z",
xint, "VIEW_has_HOOPS_HUD",
xint, "VIEW_asi_is_kts",
xint, "VIEW_cockpit_type",
xint, "VIEW_warn1_EQ",
xint, "VIEW_warn2_EQ",
xint, "VIEW_is_glossy",

xint, "VIEW_cus_rnd_use[50]",
xflt, "VIEW_cus_rnd_lo_val[50]",
xflt, "VIEW_cus_rnd_hi_val[50]",
xflt, "VIEW_cus_rnd_lo_ang[50]",
xflt, "VIEW_cus_rnd_hi_ang[50]",
xint, "VIEW_cus_rnd_mirror[50]",
xint, "VIEW_cus_non_lin[50]",
xint, "VIEW_cus_doub_val[50]",
xint, "VIEW_cus_rnd_label[50]",
xint, "VIEW_cus_dig_use[50]",
xflt, "VIEW_cus_dig_offset[50]",
xflt, "VIEW_cus_dig_scale[50]",
xint, "VIEW_cus_dig_dig[50]",
xint, "VIEW_cus_dig_dec[50]",
xint, "VIEW_ins_type[300]",
xflt, "VIEW_ins_size[300]",
xflt, "VIEW_ins_x[300]",
xflt, "VIEW_ins_y[300]",

xint, "ENGINE_num_engines",
xint, "ENGINE_num_thrustpoints",
xflt, "ENGINE_throt_max_FWD",
xflt, "ENGINE_throt_max_REV",
xflt, "ENGINE_idle_rat[2]",
xint, "ENGINE_linked_prop_EQ",
xint, "ENGINE_drive_by_wire_EQ",
xint, "ENGINE_beta_prop_EQ",
xint, "ENGINE_rev_thrust_EQ",
xint, "ENGINE_auto_feather_EQ",
xint, "ENGINE_feather_with_prop_EQ",
xint, "ENGINE_auto_rpm_EQ",
xflt, "ENGINE_feathered_pitch",
xflt, "ENGINE_reversed_pitch",
xflt, "ENGINE_rotor_mi_rat",
xflt, "ENGINE_tip_weight",
xflt, "ENGINE_tip_mach_des_100",
xflt, "ENGINE_tip_mach_des_50",
xflt, "ENGINE_power_max",
xflt, "ENGINE_crit_alt_prop",
xflt, "ENGINE_trans_loss",
xflt, "ENGINE_MP_max",
xflt, "ENGINE_trq_max_eng",
xflt, "ENGINE_max_boost_pas_prop",
xflt, "ENGINE_RSC_idlespeed_ENGN",
xflt, "ENGINE_RSC_redline_ENGN",
xflt, "ENGINE_RSC_idlespeed_PROP",
xflt, "ENGINE_RSC_redline_PROP",
xflt, "ENGINE_RSC_mingreen_ENGN",
xflt, "ENGINE_RSC_maxgreen_ENGN",
xflt, "ENGINE_RSC_mingreen_PROP",
xflt, "ENGINE_RSC_maxgreen_PROP",
xflt, "ENGINE_auto_omega_idle",
xflt, "ENGINE_auto_omega_open",
xflt, "ENGINE_auto_omega_fire",
xflt, "ENGINE_thrust_max",
xflt, "ENGINE_burner_inc",
xflt, "ENGINE_max_mach_eff",
xflt, "ENGINE_crit_alt_jet",
xflt, "ENGINE_face_jet",
xflt, "ENGINE_dummy_was_lift_fan_rat",
xflt, "ENGINE_EPR_max",
xflt, "ENGINE_max_boost_pas_jet",
xflt, "ENGINE_rock_max_sl",
xflt, "ENGINE_rock_max_opt",
xflt, "ENGINE_rock_max_vac",
xflt, "ENGINE_rock_h_opt",
xflt, "ENGINE_face_rocket",
xflt, "ENGINE_fuel_intro_time_prop",
xflt, "ENGINE_throt_time_prop",
xflt, "ENGINE_inertia_rat_prop",
xflt, "ENGINE_fuel_intro_time_jet",
xflt, "ENGINE_throt_time_jet",
xflt, "ENGINE_spool_time_jet",

xflt, "ENGINE_max_ITT",
xflt, "ENGINE_max_EGT",
xflt, "ENGINE_max_CHT",
xflt, "ENGINE_max_OILP",
xflt, "ENGINE_max_OILT",
xflt, "ENGINE_max_FUELP",
xflt, "ENGINE_snd_kias",
xflt, "ENGINE_snd_rpm_prp",
xflt, "ENGINE_snd_rpm_eng",
xflt, "ENGINE_snd_N1",
xflt, "ENGINE_exhaust_os_xyz[3]",
xflt, "ENGINE_exhaust_rat",

xflt, "SYSTEMS_starter_rat",
xflt, "SYSTEMS_battery_rat",
xint, "SYSTEMS_hydraulic_sys",
xint, "SYSTEMS_stickshaker",
xflt, "SYSTEMS_manual_reversion_rat",
xflt, "SYSTEMS_max_press_diff",

xflt, "CONTROLS_ail1_up",
xflt, "CONTROLS_ail1_dn",
xflt, "CONTROLS_ail1_cratR",
xflt, "CONTROLS_ail1_cratT",
xflt, "CONTROLS_ail2_up",
xflt, "CONTROLS_ail2_dn",
xflt, "CONTROLS_ail2_cratR",
xflt, "CONTROLS_ail2_cratT",
xflt, "CONTROLS_spo1_up", 
xflt, "CONTROLS_spo1_cratR",
xflt, "CONTROLS_spo1_cratT",
xflt, "CONTROLS_roll_to_eng_spo1",
xflt, "CONTROLS_spo2_up",
xflt, "CONTROLS_spo2_cratR",
xflt, "CONTROLS_spo2_cratT",
xflt, "CONTROLS_roll_to_eng_spo2",
xflt, "CONTROLS_yawb_ud",
xflt, "CONTROLS_yawb_cratR",
xflt, "CONTROLS_yawb_cratT",
xflt, "CONTROLS_elv1_up",
xflt, "CONTROLS_elv1_dn",
xflt, "CONTROLS_elv1_cratR",
xflt, "CONTROLS_elv1_cratT",
xflt, "CONTROLS_rud1_lft", 
xflt, "CONTROLS_rud1_cratR",
xflt, "CONTROLS_rud1_cratT",
xflt, "CONTROLS_rud2_lft", 
xflt, "CONTROLS_rud2_cratR",
xflt, "CONTROLS_rud2_cratT",
xflt, "CONTROLS_fla1_cratR",
xflt, "CONTROLS_fla1_cratT",
xflt, "CONTROLS_fla2_cratR",
xflt, "CONTROLS_fla2_cratT",
xflt, "CONTROLS_sbrk_cratR",
xflt, "CONTROLS_sbrk_cratT",
xint, "CONTROLS_con_smooth",
xflt, "CONTROLS_sbrk_up",
xflt, "CONTROLS_takeoff_trim",
xflt, "CONTROLS_hstb_trim_up",
xflt, "CONTROLS_hstb_trim_dn",
xflt, "CONTROLS_min_trim_elev",
xflt, "CONTROLS_max_trim_elev",
xflt, "CONTROLS_elev_trim_speedrat",
xflt, "CONTROLS_elev_tab",
xflt, "CONTROLS_min_trim_ailn",
xflt, "CONTROLS_max_trim_ailn",
xflt, "CONTROLS_ailn_trim_speedrat",
xflt, "CONTROLS_ailn_tab",
xflt, "CONTROLS_min_trim_rudd",
xflt, "CONTROLS_max_trim_rudd",
xflt, "CONTROLS_rudd_trim_speedrat",
xflt, "CONTROLS_rudd_tab",
xint, "CONTROLS_flap_detents",
xflt, "CONTROLS_flap_deftime",
xint, "CONTROLS_slat_type",
xflt, "CONTROLS_slat_inc",
xflt, "CONTROLS_slat_dn[10]",
xint, "CONTROLS_fla1_type",
xflt, "CONTROLS_fla1_cl",
xflt, "CONTROLS_fla1_cd",
xflt, "CONTROLS_fla1_cm",
xflt, "CONTROLS_fla1_dn[10]",
xint, "CONTROLS_fla2_type",
xflt, "CONTROLS_fla2_cl",
xflt, "CONTROLS_fla2_cd",
xflt, "CONTROLS_fla2_cm",
xflt, "CONTROLS_fla2_dn[10]",
xflt, "CONTROLS_blown_flap_add_speed",
xflt, "CONTROLS_blown_flap_throt_red",
xflt, "CONTROLS_blown_flap_min_engag",
xint, "CONTROLS_blow_all_controls",
xint, "CONTROLS_flap_EQ",
xint, "CONTROLS_slat_EQ",
xint, "CONTROLS_sbrk_EQ",
xint, "CONTROLS_vardihed_EQ",
xint, "CONTROLS_varsweep_EQ",
xint, "CONTROLS_varinc_EQ",
xint, "CONTROLS_tailrotor_EQ",
xint, "CONTROLS_collective_EQ",
xint, "CONTROLS_collective_en",
xint, "CONTROLS_flying_stab_EQ",
xint, "CONTROLS_in_downwash[56][56][10]",

xint, "GEAR_gear_retract",
xflt, "GEAR_gear_door_size",
xflt, "GEAR_nw_steerdeg1",
xflt, "GEAR_nw_steerdeg2",
xflt, "GEAR_nw_cutoff_omega",
xflt, "GEAR_nw_side_k",
xflt, "GEAR_roll_co",
xflt, "GEAR_brake_co",
xflt, "GEAR_wheel_tire_s1[2]",
xflt, "GEAR_wheel_tire_t1[2]",
xflt, "GEAR_wheel_tire_s2[2]",
xflt, "GEAR_wheel_tire_t2[2]",
xflt, "GEAR_water_rud_Z",
xflt, "GEAR_water_rud_area",
xflt, "GEAR_water_rud_maxdef",
xflt, "GEAR_anchor_xyz[3]",

xflt, "WB_cgY",
xflt, "WB_cgZ",
xflt, "WB_cgZ_fwd",
xflt, "WB_cgZ_aft",
xflt, "WB_m_empty",
xflt, "WB_m_fuel_tot",
xflt, "WB_m_jettison",
xflt, "WB_m_max",
xflt, "WB_m_displaced",
xflt, "WB_Jxx_unitmass",
xflt, "WB_Jyy_unitmass",
xflt, "WB_Jzz_unitmass",
xint, "WB_num_tanks",
xflt, "WB_tank_rat[3]",
xflt, "WB_tank_xyz[3][3]",
xflt, "WB_jett_len",
xint, "WB_jett_is_slung",
xint, "WB_jett_is_water",
xint, "WB_jett_is_acf",
xflt, "WB_jett_xyz[3]",
xint, "WB_manual_rad_gyr",
xflt, "WB_disp_rat",
xflt, "WB_m_displaced_Y",

xint, "VTOL_vect_EQ",
xint, "VTOL_auto_rpm_with_tvec",
xint, "VTOL_hide_prop_at_90_vect",
xflt, "VTOL_vect_min_nace",
xflt, "VTOL_vect_max_nace",
xflt, "VTOL_vect_min_disc",
xflt, "VTOL_vect_max_disc",
xflt, "VTOL_cyclic_def_elev",
xflt, "VTOL_cyclic_def_ailn",
xflt, "VTOL_disc_tilt_elev",
xflt, "VTOL_disc_tilt_ailn",
xflt, "VTOL_vectarmY",
xflt, "VTOL_vectarmZ",
xflt, "VTOL_flap_arm",
xflt, "VTOL_delta3",
xflt, "VTOL_vect_rate",
xflt, "VTOL_stab_delinc_to_Vne",
xflt, "VTOL_tail_with_coll",
xflt, "VTOL_puff_LMN[3]",
xflt, "VTOL_puff_xyz[3]",
xflt, "VTOL_diff_coll_with_roll",
xflt, "VTOL_diff_coll_with_hdng",
xflt, "VTOL_diff_coll_with_ptch",
xflt, "VTOL_diff_cycl_with_hdng_lon",
xflt, "VTOL_diff_cycl_with_hdng_lat",
xflt, "VTOL_rotor_trim_max_fwd",
xflt, "VTOL_rotor_trim_max_aft",

xflt, "SPECIAL_m_shift",
xflt, "SPECIAL_m_shift_dx",
xflt, "SPECIAL_m_shift_dz",
xflt, "SPECIAL_wing_tilt_ptch",
xflt, "SPECIAL_wing_tilt_roll",
xflt, "SPECIAL_jato_Y",
xflt, "SPECIAL_jato_Z",
xflt, "SPECIAL_jato_theta",
xflt, "SPECIAL_jato_thrust",
xflt, "SPECIAL_jato_dur",
xflt, "SPECIAL_jato_sfc",
xflt, "SPECIAL_stab_roll",
xflt, "SPECIAL_rudd_with_ailn_rat",
xflt, "SPECIAL_stab_hdng",
xflt, "SPECIAL_elev_with_flap_rat",
xflt, "SPECIAL_ail1_pitch",
xflt, "SPECIAL_ail1_vmax",
xflt, "SPECIAL_ail2_pitch",
xflt, "SPECIAL_ail2_vmax",
xflt, "SPECIAL_ail1_flaps",
xflt, "SPECIAL_spo1_vmax",
xflt, "SPECIAL_ail2_flaps",
xflt, "SPECIAL_spo2_vmax",
xflt, "SPECIAL_tvec_ptch",
xflt, "SPECIAL_diff_thro_ptch",
xflt, "SPECIAL_tvec_roll",
xflt, "SPECIAL_diff_thro_roll",
xflt, "SPECIAL_tvec_hdng",
xflt, "SPECIAL_diff_thro_hdng",
xint, "SPECIAL_phase_ptch_tvect_in_at_90",
xint, "SPECIAL_phase_ptch_tvect_in_at_00",
xint, "SPECIAL_phase_roll_tvect_in_at_90",
xint, "SPECIAL_phase_roll_tvect_in_at_00",
xint, "SPECIAL_phase_hdng_tvect_in_at_90",
xint, "SPECIAL_phase_hdng_tvect_in_at_00",
xflt, "SPECIAL_flap1_roll",
xflt, "SPECIAL_flap1_ptch",
xint, "SPECIAL_sbrk_on_td_EQ",
xint, "SPECIAL_fbrk_on_td_EQ",
xint, "SPECIAL_revt_on_td_EQ",
xint, "SPECIAL_sweep_with_flaps_EQ",
xint, "SPECIAL_sweep_with_vect_EQ",
xint, "SPECIAL_flaps_with_gear_EQ",
xint, "SPECIAL_flaps_with_vec_EQ",
xint, "SPECIAL_slat_with_stall_EQ",
xint, "SPECIAL_auto_trim_EQ",
xint, "SPECIAL_anti_ice_EQ",
xint, "SPECIAL_arresting_EQ",
xint, "SPECIAL_warn_gear_EQ",
xint, "SPECIAL_warn_lorot_EQ",
xflt, "SPECIAL_chute_area",
xflt, "SPECIAL_chute_Y",
xflt, "SPECIAL_chute_Z",

xint, "ASTAB_lo_speed_is_position",
xflt, "ASTAB_ASlo_the_V",
xflt, "ASTAB_ASlo_psi_V",
xflt, "ASTAB_ASlo_phi_V",
xflt, "ASTAB_AShi_the_V",
xflt, "ASTAB_AShi_psi_V",
xflt, "ASTAB_AShi_phi_V",
xflt, "ASTAB_ASlo_max_thedot",
xflt, "ASTAB_ASlo_thedot_k",
xflt, "ASTAB_ASlo_max_psidot",
xflt, "ASTAB_ASlo_psidot_k",
xflt, "ASTAB_ASlo_max_phidot",
xflt, "ASTAB_ASlo_phidot_k",
xflt, "ASTAB_AShi_max_G",
xflt, "ASTAB_AShi_G_k",
xflt, "ASTAB_AShi_Gdot_k",
xflt, "ASTAB_AShi_max_alpha",
xflt, "ASTAB_AShi_alpha_k",
xflt, "ASTAB_AShi_alphadot_k",
xflt, "ASTAB_AShi_max_beta",
xflt, "ASTAB_AShi_beta_k",
xflt, "ASTAB_AShi_betadot_k",
xflt, "ASTAB_AShi_max_phidot",
xflt, "ASTAB_AShi_phidot_k",
xflt, "ASTAB_ASlo_max_the",
xflt, "ASTAB_ASlo_the_k",
xflt, "ASTAB_ASlo_max_phi",
xflt, "ASTAB_ASlo_phi_k",

xint, "OTTO_custom_autopilot",
xflt, "OTTO_ott_asi_ratio",
xflt, "OTTO_ott_asi_sec_into_future",
xflt, "OTTO_ott_asi_kts_off_for_full_def",
xflt, "OTTO_ott_phi_ratio",
xflt, "OTTO_ott_phi_sec_into_future",
xflt, "OTTO_ott_phi_deg_off_for_full_def",
xflt, "OTTO_ott_phi_sec_to_tune",
xflt, "OTTO_ott_def_sec_into_future",
xflt, "OTTO_ott_def_dot_off_for_full_def",
xflt, "OTTO_ott_def_sec_to_tune",
xflt, "OTTO_ott_the_ratio",
xflt, "OTTO_ott_the_sec_into_future",
xflt, "OTTO_ott_the_deg_off_for_full_def",
xflt, "OTTO_ott_the_sec_to_tune",
xflt, "OTTO_ott_the_deg_per_kt",

xflt, "AUTO_size_x",
xflt, "AUTO_size_z",
xflt, "AUTO_size_tot",
xflt, "AUTO_h_eqlbm",
xflt, "AUTO_the_eqlbm",
xflt, "AUTO_thro_x_ctr",
xflt, "AUTO_prop_x_ctr",
xflt, "AUTO_mixt_x_ctr",
xflt, "AUTO_heat_x_ctr",
xflt, "AUTO_cowl_x_ctr",
xflt, "AUTO_V_ref_ms",
xflt, "AUTO_average_mac_acf",
xflt, "AUTO_tire_s_contact",
xint, "AUTO_beacon_EQ",
xint, "AUTO_skid_EQ",
xint, "AUTO_gear_EQ",
xint, "AUTO_gear_steer_EN",
xint, "AUTO_generator_EQ",
xint, "AUTO_inverter_EQ",
xint, "AUTO_fuelpump_EQ",
xint, "AUTO_battery_EQ",
xint, "AUTO_avionics_EQ",
xint, "AUTO_auto_fea_EQ",
xint, "AUTO_has_hsi",
xint, "AUTO_has_radalt",
xint, "AUTO_has_radar",
xint, "AUTO_has_SC_fd",
xint, "AUTO_has_DC_fd",
xint, "AUTO_has_stallwarn",
xint, "AUTO_has_press_controls",
xint, "AUTO_has_igniter",
xint, "AUTO_has_idlespeed",
xint, "AUTO_has_FADEC_switch",
xint, "AUTO_has_clutch_switch",
xint, "AUTO_has_pre_rotate",
xint, "AUTO_has_mixture",
xint, "AUTO_has_kts_mac",
xint, "AUTO_has_asi_set",
xint, "AUTO_has_hdg_set",
xint, "AUTO_has_vvi_set",
xint, "AUTO_has_alt_set",
xint, "AUTO_has_litemap_tex_1",
xint, "AUTO_has_litemap_tex_2",

xint, "OVERFLOW_plot_OBJ7_cock_exact_fwd",
xint, "OVERFLOW_cockpit_M_out",
xint, "OVERFLOW_has_FMS",
xint, "OVERFLOW_has_APU_switch",
xflt, "OVERFLOW_SFC_max[8]",
xint, "OVERFLOW_hydraulic_eng",
xint, "OVERFLOW_hydraulic_eng_sel",
xchr, "OVERFLOW_ins_specs[300]",
xflt, "OVERFLOW_alta_x_ctr",
xint, "OVERFLOW_has_full_bleed_air",
xflt, "OVERFLOW_dump_altitude",
xflt, "SPECIAL_flap2_roll",
xflt, "SPECIAL_flap2_ptch",
xint, "OVERFLOW_flap1_ptch_above_50",
xint, "OVERFLOW_flap2_ptch_above_50",
xint, "OVERFLOW_flap1_roll_above_50",
xint, "OVERFLOW_flap2_roll_above_50",
xint, "SPECIAL_flap_with_stall_EQ",
xint, "OVERFLOW_has_ignition",
xint, "OVERFLOW_randys_magic_mushroom",
xflt, "OVERFLOW_gear_pumps",
xflt, "OVERFLOW_flap_pumps",
xint, "OVERFLOW_has_tail_lock",
xint, "OVERFLOW_start_on_water",
xflt, "OVERFLOW_rud1_rgt",
xflt, "OVERFLOW_rud2_rgt",
xint, "OVERFLOW_rgt_ruds_assigned",
xflt, "CONTROLS_elv2_up",
xflt, "CONTROLS_elv2_dn",
xflt, "CONTROLS_elv2_cratR",
xflt, "CONTROLS_elv2_cratT",
xflt, "OVERFLOW_cgZ_ref_ft",
# v8.15+
xflt, "OVERFLOW_total_S",	
xflt, "OVERFLOW_total_elements",
xint, "OVERFLOW_randy_temp",
xflt, "OVERFLOW_elev_def_time",
xflt, "OVERFLOW_ailn_def_time",
xflt, "OVERFLOW_rudd_def_time",
xint, "OVERFLOW_custom_FADEC",
xflt, "OVERFLOW_fadec_del",
xflt, "OVERFLOW_fadec_dot",
xflt, "OVERFLOW_fadec_jrk",
xflt, "OVERFLOW_pitch_cyc_with_v1_kts",
xflt, "OVERFLOW_pitch_cyc_with_v2_kts",
xflt, "OVERFLOW_pitch_cyc_with_v2_deg",
xint, "OVERFLOW_lock_with_elev",
xint, "OVERFLOW_custom_st_coords",	# set your own s/t mapping
# v8.20+
xflt, "OVERFLOW_xflt_overflow1[5]",

xflt, "GEAR_strut_s1[10]",
xflt, "GEAR_strut_t1[10]",
xflt, "GEAR_strut_s2[10]",
xflt, "GEAR_strut_t2[10]",

xflt, "OVERFLOW_xflt_overflow2[3600]",

xint, "VIEW_lanlite1_con",
xint, "VIEW_lanlite2_con",
xint, "VIEW_taxilite_con",

xflt, "OVERFLOW_xflt_overflow3[1224]",

xstruct, "engn[8]",
xstruct, "wing[56]",
xstruct, "part[95]",
xstruct, "gear[10]",
xstruct, "watt[24]",	# was after sbrk, but is actually here!
xstruct, "door[24]",	# doorstruct used for speedbrakes and doors!
#struct, "objs[24]",	# Misc Objects - >=8.40
# Unknown other stuff here in >=8.60
    ]
    acf810=acf8000
    acf815=acf8000
    acf830=acf8000
    acf840=list(acf8000)
    acf840.extend([
xstruct, "objs[24]",	# Misc Objects
    ])
    acf860=acf840
    acf900=acf840
    acf901=acf840	# v9b5?
    acf902=acf840	# v9b18

    engn8000 = [
xint, "engn_type",
xint, "prop_type",
xflt, "SFC_idle",
xflt, "prop_dir",
xint, "is_ducted",
xflt, "num_blades",
xint, "prop_clutch_EQ",
xflt, "prop_gear_rat",
xflt, "vert_init",
xflt, "side_init",
xflt, "min_pitch",
xflt, "max_pitch",
xflt, "des_rpm_prp",
xflt, "des_kts_prp",
xflt, "des_kts_acf",
xflt, "engn_mass",
xflt, "prop_mass",
xflt, "mi_prop_rpm",
xflt, "mi_engn_rpm",
xflt, "discarea",
xflt, "ringarea[10]",
xflt, "bladesweep[10]",
    ]
    engn810=engn8000
    engn815=engn8000
    engn830=engn8000
    engn840=engn8000
    engn860=engn8000
    engn900=engn8000
    engn901=engn8000
    engn902=engn8000

    wing8000 = [
xint, "is_left",
xflt, "lat_sign",
xint, "manual_mac",
xchr, "Rafl0[40]",
xchr, "Rafl1[40]",
xchr, "Tafl0[40]",
xchr, "Tafl1[40]",
xint, "els",
xflt, "Croot",
xflt, "Ctip",
xflt, "semilen_SEG",
xflt, "semilen_JND",	# semilen of the JOINED wing segments
xflt, "average_mac",
xflt, "element_len",
xflt, "chord_piv",
xflt, "dihed1",
xflt, "dihed2",
xflt, "dihednow",
xint, "vardihed",
xflt, "sweep1",
xflt, "sweep2",
xflt, "sweepnow",
xint, "varsweep",
xflt, "inc2",
xflt, "incnow",
xint, "varinc",
xflt, "e",
xflt, "AR",
xflt, "TR",
xflt, "al_D_al0",
xflt, "cl_D_cl0",
xflt, "cm_D_cm0",
xflt, "delta_fac",
xflt, "alpha_max",
xflt, "slat_effect",
xflt, "spec_wash",
xflt, "rev_con",	# was xchr in .h, but seems to be either xint or xflt
xflt, "el_s[10]",
xflt, "mac[10]",
xflt, "incidence[10]",
xint, "inc_ail1[10]",
xint, "inc_ail2[10]",
xint, "inc_elv1[10]",
xint, "inc_rud1[10]",
xint, "inc_rud2[10]",
xint, "inc_vect[10]",
xint, "inc_trim[10]",
xint, "ail1[10]",
xflt, "ail1_elR",
xflt, "ail1_elT",
xint, "ail2[10]",
xflt, "ail2_elR",
xflt, "ail2_elT",
xint, "spo1[10]",
xflt, "spo1_elR",
xflt, "spo1_elT",
xint, "spo2[10]",
xflt, "spo2_elR",
xflt, "spo2_elT",
xint, "yawb[10]",
xflt, "yawb_elR",
xflt, "yawb_elT",
xint, "elv1[10]",
xflt, "elv1_elR",
xflt, "elv1_elT",
xint, "rud1[10]",
xflt, "rud1_elR",
xflt, "rud1_elT",
xint, "rud2[10]",
xflt, "rud2_elR",
xflt, "rud2_elT",
xint, "fla1[10]",
xflt, "fla1_elR",
xflt, "fla1_elT",
xint, "fla2[10]",
xflt, "fla2_elR",
xflt, "fla2_elT",
xint, "slat[10]",
xint, "sbrk[10]",
xflt, "sbrk_elR",
xflt, "sbrk_elT",
xflt, "ca_xyz[20][3]",
xflt, "co_xyz[20][3]",
    ]
    wing810=list(wing8000)
    wing810.extend([
xint, "inc_elv2[10]",
xint, "elv2[10]",
xflt, "elv2_elR",
xflt, "elv2_elT",
xflt, "overflow_dat[100]",
    ])
    wing815=wing810
    wing830=wing810
    wing840=wing810
    wing860=wing810
    wing900=wing810
    wing901=wing810
    wing902=wing810

    part8000 = [
xint, "part_eq",
xflt, "part_x",
xflt, "part_psi",
xflt, "aero_x_os",
xflt, "area_frnt",
xint, "patt_prt",
xflt, "part_y",
xflt, "part_the",
xflt, "aero_y_os",
xflt, "area_side",
xint, "patt_con",
xflt, "part_z",
xflt, "part_phi",
xflt, "aero_z_os",
xflt, "area_nrml",
xflt, "patt_rat",
xflt, "cd",
xflt, "scon",
xflt, "damp",
xint, "part_tex",
xflt, "top_s1",
xflt, "bot_s1",
xflt, "top_t1",
xflt, "bot_t1",
xflt, "top_s2",
xflt, "bot_s2",
xflt, "top_t2",
xflt, "bot_t2",
xflt, "part_r",
xint, "s_dim",
xint, "r_dim",
xflt, "geo_xyz[20][18][3]",
xflt, "nrm_xyz[20][18][3]",
xflt, "st[20][18][2]",
xchr, "locked[20][18]",
    ]
    part800=part8000	# For weapons
    part810=part8000
    part815=part8000
    part830=part8000
    part840=part8000
    part860=part8000
    part900=part8000
    part901=part8000
    part902=part8000

    gear8000=[
xint, "gear_type",
xint, "steers",
xflt, "scon",
xflt, "damp",
xflt, "leg_len",
xflt, "cyc_time",
xflt, "dep_rat",
xflt, "stat_def",	# the gear TIRE LOCATION IS OFFSET DOWN BY THIS MUCH IN X-PLANE since people ALWAYS enter gear location UNDER STATIC DEFLECTION!
xflt, "strut_comp",
xflt, "tire_radius",
xflt, "tire_swidth",
xflt, "tire_mi",
xflt, "gear_x",
xflt, "latE",	# extended
xflt, "lonE",
xflt, "axiE",
xflt, "x_nodef",
xflt, "gear_y",
xflt, "latR",	# retracted
xflt, "lonR",
xflt, "axiR",
xflt, "y_nodef",
xflt, "gear_z",
xflt, "latN",	# now
xflt, "lonN",
xflt, "axiN",
xflt, "z_nodef",
    ]
    gear810=gear8000
    gear815=gear8000
    gear830=gear8000
    gear840=gear8000
    gear860=gear8000
    gear900=gear8000
    gear901=gear8000
    gear902=gear8000

    watt8000=[
xchr, "watt_name[40]",
xint, "watt_prt",
xint, "watt_con",
xflt, "watt_x",
xflt, "watt_psi",
xflt, "watt_y",
xflt, "watt_the",
xflt, "watt_z",
xflt, "watt_phi",
    ]
    watt810=watt8000
    watt815=watt8000
    watt830=watt8000
    watt840=watt8000
    watt860=watt8000
    watt900=watt8000
    watt901=watt8000
    watt902=watt8000

    door8000=[
xint, "type",
xflt, "area",
xflt, "xyz[3]",
xflt, "geo[4][4][3]",	# the doors are 4x4, to allow curvature and stuff in 3D
xflt, "nrm[4][4][3]",	# i dont use these yet
xflt, "axi_rot",
xflt, "inn_s1",
xflt, "out_s1",
xflt, "ext_ang",
xflt, "inn_t1",
xflt, "out_t1",
xflt, "ret_ang",
xflt, "inn_s2",
xflt, "out_s2",
xflt, "ang_now",
xflt, "inn_t2",
xflt, "out_t2",
    ]
    door810=door8000
    door815=door8000
    door830=door8000
    door840=door8000
    door860=door8000
    door900=door8000
    door901=door8000
    door902=door8000

    objs840=[	# same as watt. variable names may not match Laminar's
xchr, "obj_name[40]",
xint, "obj_prt",
xint, "obj_con",
xflt, "obj_x",
xflt, "obj_psi",
xflt, "obj_y",
xflt, "obj_the",
xflt, "obj_z",
xflt, "obj_phi",
    ]
    objs860=objs840
    objs900=objs840
    objs901=objs840
    objs902=objs840
    
# Derived from WPN740.def by Stanislaw Pusep
#   http://sysd.org/xplane/acftools/WPN740.def
# and from X-Plane v7 docs
#   ./Instructions/Manual_Files/X-Plane ACF_format.html
    wpn740=[
#xchr, "HEADER_platform",
#xint, "HEADER_version",
xint, "type",
xint, "free_flyer",
xint, "action_mode",
xflt, "x_wpn_att",
xflt, "y_wpn_att",
xflt, "z_wpn_att",
xflt, "cgY",
xflt, "cgZ",
xflt, "las_range",
xflt, "conv_range",
xflt, "bul_rounds_per_sec",
xflt, "bul_rounds",
xflt, "bul_muzzle_speed",
xflt, "bul_area",
xflt, "added_mass",
xflt, "total_weapon_mass_max",
xflt, "fuel_warhead_mass_max",
xint, "warhead_type",
xflt, "mis_drag_co",
xflt, "mis_drag_chute_S",
xflt, "mis_fin_z[4]",
xflt, "mis_fin_cr[4]",
xflt, "mis_fin_ct[4]",
xflt, "mis_fin_semilen[4]",
xflt, "mis_fin_sweep[4]",
xflt, "mis_fin_conrat[4]",
xflt, "mis_fin_steer[4]",
xflt, "mis_fin_dihed[4][2]",	# dihedrals: [x,x] means [x,180-x]. Sheesh.
xchr, "mis_afl[4][40]",
xflt, "mis_thrust[3]",
xflt, "mis_duration[3]",
xflt, "mis_cone_width",
xflt, "mis_crat_per_deg_bore",
xflt, "mis_crat_per_degpersec_bore",
xflt, "mis_crat_per_degpersec",
xflt, "gun_del_psi_deg_max",
xflt, "gun_del_the_deg_max",
xflt, "gun_del_psi_deg_now",
xflt, "gun_del_the_deg_now",
xflt, "s_frn",
xflt, "s_sid",
xflt, "s_top",
xflt, "X_body_aero",
xflt, "Y_body_aero",
xflt, "Z_body_aero",
xflt, "Jxx_unitmass",
xflt, "Jyy_unitmass",
xflt, "Jzz_unitmass",
xint, "i",
xint, "j",
xint, "target_index",
xflt, "targ_lat",
xflt, "targ_lon",
xflt, "targ_h",
xflt, "del_psi",
xflt, "del_the",
xflt, "rudd_rat",
xflt, "elev_rat",
xflt, "V_msc",
xflt, "AV_msc",
xflt, "dist_targ",
xflt, "dist_point",
xflt, "time_point",
xflt, "sin_the",
xflt, "cos_the",
xflt, "sin_psi",
xflt, "cos_psi",
xflt, "sin_phi",
xflt, "cos_phi",
xflt, "fx_axis",
xflt, "fy_axis",
xflt, "fz_axis",
xflt, "vx",
xflt, "vy",
xflt, "vz",
xflt, "x",
xflt, "y",
xflt, "z",
xflt, "L",
xflt, "M",
xflt, "N",
xflt, "Prad",
xflt, "Qrad",
xflt, "Rrad",
xflt, "q[4]",
xflt, "the",
xflt, "psi",
xflt, "phi",
xflt, "next_bull_time",
xflt, "total_weapon_mass_now",
xflt, "fuel_warhead_mass_now",
xflt, "impact_time",
xflt, "xflt_overflow[973]",
xint, "xint_overflow[1000]",
xchr, "xchr_overflow[1000]",
xflt, "body_radius",
xflt, "PARTS_body_X[20][18]",
xflt, "PARTS_body_Y[20][18]",
xflt, "PARTS_body_Z[20][18]",
    ]

    #------------------------------------------------------------------------
    # Derived from hl_acf_structs.h
    wpn800=[
#xchr, "HEADER_platform",
#xint, "HEADER_version",
xint, "type",
xint, "free_flyer",
xint, "action_mode",
xflt, "impact_time",
xflt, "next_bull_time",
xflt, "cgY",
xflt, "cgZ",
xflt, "las_rangexflt",
xflt, "conv_range",
xflt, "bul_rounds_per_sec",
xflt, "bul_rounds",
xflt, "bul_muzzle_speed",
xflt, "bul_area",
xint, "warhead_type",
xflt, "added_mass",
xflt, "total_weapon_mass_max",
xflt, "fuel_warhead_mass_max",
xflt, "total_weapon_mass_now",
xflt, "fuel_warhead_mass_now",
xflt, "mis_drag_chute_S",
xflt, "mis_fin_z[4]",		# long arm
xflt, "mis_fin_cr[4]",		# root chord
xflt, "mis_fin_ct[4]",		# tip chord
xflt, "mis_fin_semilen[4]",
xflt, "mis_fin_sweep[4]",
xflt, "mis_fin_conrat[4]",	# control size
xflt, "mis_fin_steer[4]",
xflt, "mis_fin_dihed[4][2]",	# dihedrals: [x,x] means [x,180-x]. Sheesh.
xchr, "mis_afl[4][40]",
xflt, "mis_thrust[3]",
xflt, "mis_duration[3]",
xflt, "mis_cone_width",
xflt, "mis_crat_per_deg_bore",
xflt, "mis_crat_per_degpersec_bore",
xflt, "mis_crat_per_degpersec",
xflt, "gun_del_psi_deg_max",
xflt, "gun_del_the_deg_max",
xflt, "psi_con",
xflt, "the_con",
xflt, "phi_con",
xflt, "psi_acf",
xflt, "the_acf",
xflt, "phi_acf",
xflt, "psi_wrl",
xflt, "the_wrl",
xflt, "phi_wrl",
xflt, "s_frn",
xflt, "s_sid",
xflt, "s_top",
xflt, "Jxx_unitmass",
xflt, "Jyy_unitmass",
xflt, "Jzz_unitmass",
xint, "target_index",
xflt, "targ_lat",
xflt, "targ_lon",
xflt, "targ_h",
xflt, "del_psi",
xflt, "del_the ",
xflt, "rudd_rat",
xflt, "elev_rat",
xflt, "V_msc",
xflt, "AV_msc",
xflt, "dist_targ",
xflt, "dist_point",
xflt, "time_point",
xflt, "sin_the",
xflt, "cos_the",
xflt, "sin_psi",
xflt, "cos_psi",
xflt, "sin_phi",
xflt, "cos_phi",
xflt, "fx_axis",
xflt, "fy_axis",
xflt, "fz_axis",
xflt, "vx",
xflt, "vy",
xflt, "vz",
xflt, "x",
xflt, "y",
xflt, "z",
xflt, "L",
xflt, "M",
xflt, "N",
xflt, "Prad",
xflt, "Qrad",
xflt, "Rrad",
xflt, "q[4]",
xflt, "chute_vector_wrl[3]",

xstruct, "part",

xflt, "xflt_overflow[99]",	# Should be 100 !!!
    ]


#------------------------------------------------------------------------
#-- ACF --
#------------------------------------------------------------------------
class ACF:

    # slurp the acf file
    def __init__(self, filename, debug,
                 defs=None, fmt=None, prefix='', prg=True):

        # Reading sub-structure?
        if defs:
            self.parse(filename, debug, defs, fmt, prefix, prg)
            return

        acffile=open(filename, "rb")
        if debug>1:
            dmp=open(filename[:filename.rindex('.')]+'.txt', 'wt')
        else:
            dmp=None

        # HEADER_platform
        self.HEADER_platform=acffile.read(1)
        if self.HEADER_platform=='a':
            fmt='>'
        elif self.HEADER_platform=='i':
            fmt='<'
        else:
            acffile.close()
            raise ParseError("This isn't a v7 or v8 X-Plane file!")
        if dmp:
            dmp.write("%6x:\tHEADER_platform:\t%s\n" %(0,self.HEADER_platform))

        # HEADER_version
        (self.HEADER_version,)=unpack(fmt+'i', acffile.read(4))
        if self.HEADER_version==1:
            defs=DEFfmt.wpn740
        elif self.HEADER_version==800:
            defs=DEFfmt.wpn800
        elif ((self.HEADER_version<700 or self.HEADER_version>=1000) and
              self.HEADER_version!=8000):
            acffile.close()
            raise ParseError("This isn't a v7, v8 or v9 X-Plane file!")
        elif self.HEADER_version<800:
            if self.HEADER_version in [700, 740]:
                defs=DEFfmt.acf740
            else:
                acffile.close()
                raise ParseError("This is a %4.2f format plane! Please re-save it in PlaneMaker 7.63." % (self.HEADER_version/100.0))
        elif self.HEADER_version in [8000,810,815,830,840,860,900,901,902]:
            defs=eval("DEFfmt.acf%s" % self.HEADER_version)
        else:
            acffile.close()
            raise ParseError("Can't read %4.2f format planes!" % (self.HEADER_version/100.0))
        if dmp:
            dmp.write("%6x:\tHEADER_version:\t%s\n" % (1,self.HEADER_version))

        self.parse(acffile, dmp, defs, fmt, prefix, prg)
        if dmp: dmp.close()
        acffile.close()

        if self.HEADER_version>=800:
            return

        # v7 weapon
        if self.HEADER_version==1:
            self.part=(v7wpn(self))
            return

        # Rewrite selected v7 acf variables to v8 format

        # engines
        self.engn=[]
        for n in range(DEFfmt.engnDIM):
            self.engn.append(v7engn(self, n))

        # wings
        self.wing=[]
        for n in range(DEFfmt.wingDIM):
            if DEFfmt.v7parts.has_key(n):
                (v7, s_dim, r_dim, tex,
                 top_s1, bot_s1, top_t1, bot_t1,
                 top_s2, bot_s2, top_t2, bot_t2)=DEFfmt.v7parts[n]
                self.wing.append(v7wing(self, v7))
            else:
                self.wing.append(v7wing(None))
        
        # parts
        self.part=[]
        for n in range(DEFfmt.partDIM):
            if DEFfmt.v7parts.has_key(n):
                (v7, s_dim, r_dim, tex,
                 top_s1, bot_s1, top_t1, bot_t1,
                 top_s2, bot_s2, top_t2, bot_t2)=DEFfmt.v7parts[n]
                self.part.append(v7part(self, v7, s_dim, r_dim, tex,
                                        top_s1, bot_s1, top_t1, bot_t1,
                                        top_s2, bot_s2, top_t2, bot_t2))
            else:
                self.part.append(v7part(None))

        # gear
        self.gear=[]
        for n in range(67,73):
            self.gear.append(v7gear(self, n))
        for n in range(4):
            self.gear.append(v7gear(None))
            			#    wheel,     tread
        self.GEAR_wheel_tire_s1=[ 1/1024.0,  1/1024.0]
        self.GEAR_wheel_tire_t1=[      0.0, 50/1024.0]
        self.GEAR_wheel_tire_s2=[15/1024.0, 15/1024.0]
        self.GEAR_wheel_tire_t2=[50/1024.0, 79/1024.0]
        self.GEAR_strut_s1=[0 for i in range(10)]
        self.GEAR_strut_t1=[0 for i in range(10)]
        self.GEAR_strut_s2=[0 for i in range(10)]
        self.GEAR_strut_t2=[0 for i in range(10)]
        
        # weapons
        self.watt=[]
        for n in range(DEFfmt.wattDIM):
            self.watt.append(v7watt(self, n))

        # doors
        self.door=[]
        for n in range(10):
            self.door.append(v7door(self, n))
        for n in range(10,DEFfmt.doorDIM+DEFfmt.sbrkDIM):
            self.door.append(v7door(None))

        # misc
        self.WB_tank_xyz=[]
        for i in range(3):
            self.WB_tank_xyz.append([self.WB_tank_X[i],
                                     self.WB_tank_Y[i],
                                     self.WB_tank_Z[i]])

        self.VIEW_lanlite1_con=self.VIEW_lanlite2_con=self.VIEW_taxilite_con=0
        self.OVERFLOW_custom_st_coords=0


    #------------------------------------------------------------------------
    def data(self, acffile, dmp, number, size, t, fmt, var):
        v=[]
        for i in range(number):
            if t==DEFfmt.xstruct:
                x=ACF(acffile, dmp,
                      eval("DEFfmt.%s%s" % (var, self.HEADER_version)),
                      fmt, "%s[%s]." % (var, i), 0)
            else:
                ifmt=fmt+'i'
                ffmt=fmt+'f'
                c=acffile.read(size)
                if t==DEFfmt.xchr:
                    if size==1:
                        if not c:
                            x=0
                        elif "0123456789".find(c)!=-1:
                            x=int(c)
                        else:
                            x=0
                    elif c.find("\0")!=-1:
                        x=c[:c.index("\0")]	# trim nulls
                    else:
                        x=c
                elif t==DEFfmt.xint:
                    (x,)=unpack(ifmt, c)
                elif t==DEFfmt.xflt:
                    (x,)=unpack(ffmt, c)
                    #x=round(x,1+Vertex.ROUND)
                else:
                    acffile.close()
                    raise ParseError("Can't parse file")

            if number==1:
                return x
            v.append(x)
        return v


    #------------------------------------------------------------------------
    def parse(self, acffile, dmp, defs, fmt, prefix, prg):
        n=len(defs)
        for i in range(0,n,2):
            if prg:
                Window.DrawProgressBar(i/(4.0*n), "Reading data ...")
            off=acffile.tell()
            t=defs[i]	# Data type
            
            size=4	# ints and floats
            k=defs[i+1].split("[")
            var=k.pop(0)
            for j in range(len(k)):
                k[j]=int(k[j][:-1])
            if t==DEFfmt.xchr:
                if len(k)>0:
                    size=k.pop()
                else:
                    size=1

            v=[]
            if len(k)>0:
                number=k.pop()
                if len(k)>0:
                    for o in range(k[0]):
                        if len(k)>1:
                            assert(len(k)==2)
                            vo=[]
                            for p in range(k[1]):
                                vo.append(self.data(acffile, dmp, number,
                                                    size, t, fmt, var))
                            v.append(vo)
                        else:    
                            v.append(self.data(acffile, dmp, number,
                                               size, t, fmt, var))
                else:
                    v=self.data(acffile, dmp, number, size, t, fmt, var)
            else:
                v=self.data(acffile, dmp, 1, size, t, fmt, var)

            if dmp and t!=DEFfmt.xstruct:
                dmp.write("%6x:\t%s%s:\t%s\n" % (off, prefix, var, v))
            exec("self.%s=v" % var)
        
        
#------------------------------------------------------------------------
class v7engn:
    def __init__(self, acf, v7):
        self.engn_type=acf.PROP_engn_type[v7]
        self.num_blades=acf.PROP_num_blades[v7]
        self.vert_init=acf.PROP_vert_cant_init[v7]
        self.side_init=acf.PROP_side_cant_init[v7]
        self.prop_dir=acf.PROP_prop_dir[v7]

class v7wing:
    def __init__(self, acf, v7=0):
        if not acf:
            self.semilen_SEG=0.0
            return
        self.is_left=acf.OVERFLOW_is_left[v7]
        self.lat_sign=acf.OVERFLOW_lat_sign[v7]
        self.Rafl0=acf.PARTS_Rafl0[v7]
        self.Rafl1=acf.PARTS_Rafl1[v7]
        self.Tafl0=acf.PARTS_Tafl0[v7]
        self.Tafl1=acf.PARTS_Tafl1[v7]
        self.els=acf.PARTS_els[v7]
        self.Croot=acf.PARTS_Croot[v7]
        self.Ctip=acf.PARTS_Ctip[v7]
        self.semilen_SEG=acf.PARTS_semilen_SEG[v7]
        self.semilen_JND=acf.PARTS_semilen_JND[v7]
        self.dihed1=acf.PARTS_dihed1[v7]
        self.sweep1=acf.PARTS_sweep1[v7]
        self.incidence=acf.PARTS_incidence[v7]
        self.inc_vect=acf.PARTS_inc_vect[v7]

class v7part:
    def __init__(self, acf, v7=0, s_dim=0, r_dim=0, tex=0,
                 top_s1=0, bot_s1=0, top_t1=0, bot_t1=0,
                 top_s2=0, bot_s2=0, top_t2=0, bot_t2=0):
        if not acf:
            self.part_eq=0
            return
        self.s_dim=s_dim
        self.r_dim=r_dim
        self.top_s1=top_s1/1024.0
        self.bot_s1=bot_s1/1024.0
        self.top_t1=top_t1/1024.0
        self.bot_t1=bot_t1/1024.0
        self.top_s2=top_s2/1024.0
        self.bot_s2=bot_s2/1024.0
        self.top_t2=top_t2/1024.0
        self.bot_t2=bot_t2/1024.0
        self.patt_con=0
        self.part_tex=tex
        self.part_eq=acf.PARTS_part_eq[v7]
        self.part_x=acf.PARTS_Xarm[v7]
        self.part_y=acf.PARTS_Yarm[v7]
        self.part_z=acf.PARTS_Zarm[v7]
        self.part_psi=acf.OVERFLOW_heading[v7]
        self.part_phi=acf.OVERFLOW_roll[v7]
        self.part_the=acf.OVERFLOW_pitch[v7]
        if s_dim and r_dim:
            self.geo_xyz=[]
            for s in range(DEFfmt.body_sDIM):
                v=[]
                for r in range(DEFfmt.body_rDIM):
                    v.append([acf.PARTS_body_X[v7][s][r],
                              acf.PARTS_body_Y[v7][s][r],
                              acf.PARTS_body_Z[v7][s][r]])
                self.geo_xyz.append(v)

class v7gear:
    def __init__(self, acf, v7=0):
        if not acf:
            self.gear_type=0
            return
        self.gear_type=acf.PARTS_gear_type[v7]
        self.gear_x=acf.PARTS_Xarm[v7]
        self.gear_y=acf.PARTS_Yarm[v7]
        self.gear_z=acf.PARTS_Zarm[v7]
        self.latE=acf.PARTS_gear_latE[v7]
        self.lonE=acf.PARTS_gear_lonE[v7]
        self.axiE=acf.PARTS_gear_axiE[v7]
        self.tire_radius=acf.PARTS_tire_radius[v7]
        self.tire_swidth=acf.PARTS_tire_swidth[v7]
        self.leg_len=acf.PARTS_gear_leglen[v7]

class v7watt:
    def __init__(self, acf, v7):
        self.watt_name=acf.WEAPONS_wpn_name[v7]
        self.watt_con=0
        self.watt_x=acf.WEAPONS_x_wpn_att[v7]
        self.watt_y=acf.WEAPONS_y_wpn_att[v7]
        self.watt_z=acf.WEAPONS_z_wpn_att[v7]
        self.watt_psi=acf.WEAPONS_psi_wpn_att[v7]
        self.watt_the=acf.WEAPONS_the_wpn_att[v7]
        self.watt_phi=acf.WEAPONS_roll_wpn_att[v7]

class v7wpn:
    def __init__(self, acf):
        if not acf:
            self.part_eq=0
            return
        self.s_dim=DEFfmt.body_sDIM
        self.r_dim=DEFfmt.body_rDIM
        self.top_s1=0
        self.bot_s1=0
        self.top_t1=0.5
        self.bot_t1=0.0
        self.top_s2=0.508
        self.bot_s2=0.508
        self.top_t2=1.0
        self.bot_t2=0.5
        self.part_eq=1
        self.part_x=acf.x_wpn_att
        self.part_y=acf.y_wpn_att
        self.part_z=acf.z_wpn_att
        self.geo_xyz=[]
        for s in range(DEFfmt.body_sDIM):
            v=[]
            for r in range(DEFfmt.body_rDIM):
                v.append([acf.PARTS_body_X[s][r],
                          acf.PARTS_body_Y[s][r],
                          acf.PARTS_body_Z[s][r]])
            self.geo_xyz.append(v)
        self.mis_fin_z=acf.mis_fin_z
        self.mis_fin_cr=acf.mis_fin_cr
        self.mis_fin_ct=acf.mis_fin_ct
        self.mis_fin_semilen=acf.mis_fin_semilen
        self.mis_fin_sweep=acf.mis_fin_sweep
        self.mis_fin_conrat=acf.mis_fin_conrat
        self.mis_fin_steer=acf.mis_fin_steer
        self.mis_fin_dihed=acf.mis_fin_dihed
    
class v7door:
    def __init__(self, acf, v7=None):
        if not acf:
            self.type=DEFfmt.gear_door_none
            return
        self.type=acf.GEAR_gear_door_typ[v7]
        self.xyz=[acf.GEAR_gear_door_loc[v7][0],
                  acf.GEAR_gear_door_loc[v7][1],
                  acf.GEAR_gear_door_loc[v7][2]]
        self.axi_rot=acf.GEAR_gear_door_axi_rot[v7]
        self.ext_ang=acf.GEAR_gear_door_ext_ang[v7]
        self.inn_s1=0.0
        self.out_s1=0.0
        self.inn_t1=0.3837890625
        self.out_t1=0.3837890625
        self.inn_s2=0.015625
        self.out_s2=0.015625
        self.inn_t2=0.5078125
        self.out_t2=0.5078125
        self.geo=[[acf.GEAR_gear_door_geo[v7][0],None,None,
                   acf.GEAR_gear_door_geo[v7][1]],
                  None, None,
                  [acf.GEAR_gear_door_geo[v7][3],None,None,
                   acf.GEAR_gear_door_geo[v7][2]]]


def quatmult(q1,q2):
    return Quaternion([q1[0]*q2[0] - q1[1]*q2[1] - q1[2]*q2[2] - q1[3]*q2[3],
                       q1[0]*q2[1] + q1[1]*q2[0] + q1[2]*q2[3] - q1[3]*q2[2],
                       q1[0]*q2[2] + q1[2]*q2[0] + q1[3]*q2[1] - q1[1]*q2[3],
                       q1[0]*q2[3] + q1[3]*q2[0] + q1[1]*q2[2] - q1[2]*q2[1]])

        
#------------------------------------------------------------------------
relocate=False

def file_callback (filename):
    print "Starting ACF import from " + filename
    Blender.Window.DrawProgressBar(0, "Opening ...")
    try:
        acf=ACFimport(filename, True, relocate)
    except ParseError, e:
        Blender.Window.DrawProgressBar(1, "ERROR")
        print("ERROR:\t%s.\n" % e.msg)
        Blender.Draw.PupMenu("ERROR: %s" % e.msg)
        return
    acf.doImport()
    Blender.Window.DrawProgressBar(1, "Finished")
    print "Finished\n"
    Blender.Redraw()


#------------------------------------------------------------------------
# main routine
#------------------------------------------------------------------------

opt=Blender.Draw.PupMenu("Cursor location:%t|Reference point (for cockpit & misc objects)|Centre of gravity (for CSLs & static scenery)")
if opt==1:
    relocate=False
    Blender.Window.FileSelector(file_callback, "Import ACF or WPN")
elif opt==2:
    relocate=True
    Blender.Window.FileSelector(file_callback, "Import ACF or WPN")
