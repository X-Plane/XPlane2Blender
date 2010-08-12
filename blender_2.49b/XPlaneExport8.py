#!BPY
""" Registration info for Blender menus:
Name: 'X-Plane v8/v9 Object (.obj)'
Blender: 245
Group: 'Export'
Tooltip: 'Export to X-Plane v8 or v9 format object (.obj)'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script exports scenery created in Blender to X-Plane v8 or v9
.obj format for placement with World-Maker.

Limitations:<br>
  * Only Lamps and Mesh Faces (including "lines") are exported.<br>
  * All faces must share a single texture (this is a limitation of<br>
    the X-Plane .obj file format) apart from cockpit panel faces<br>
    which can additionally use the cockpit panel texture. Multiple<br>
    textures are not automagically merged into one file during the<br>
    export.
"""

#------------------------------------------------------------------------
# X-Plane exporter for blender 2.43 or above
#
# Copyright (c) 2005-2007 Jonathan Harris
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
# 2005-11-10 v2.10
#  - New file
#
# 2005-11-17 v2.11
#  - Fixed error when ipo exists, but no curve defined.
#  - Added support for updated (hopefully final) Blender 2.40 API.
#  - Fixed bug with translation of child bones.
#
# 2005-11-21 v2.13
#  - Don't emit redundant ATTR_[no_]shade attributes.
#  - Added optimisation to re-use points (but not indices) between animations.
#
# 2005-11-21 v2.14
#  - Speeded up point re-use optimisation.
#
# 2005-12-21 v2.15
#  - Handle armatures set in "Rest position" - requires 2.40.
#  - Tweaked progress bar.
#  - Add support for custom datarefs added by XPLMRegisterDataAccessor().
#
# 2006-01-05 v2.16
#  - Fix for relative and v8 texture paths.
#
# 2006-02-24 v2.18
#  - Import datarefs from DataRefs.txt. Add checking of type and arrayness.
#
# 2006-04-16 v2.20
#  - Translation fix for animations nested >=3 deep.
#  - Emit unit rotation vector even when Armature is scaled.
#  - Fix face direction when object negatively scaled.
#  - Fix face normal to be unit length when object is scaled.
#  - Default to ATTR_no_blend.
#
# 2006-04-22 v2.21
#  - Oops. ATTR_no_blend not such a good idea.
#
# 2006-07-19 v2.26
#  - Support for named lights, layer group, custom LOD ranges.
#
# 2006-07-30 v2.28
#  - Light names taken from "name" property, if present.
#  - Support for ANIM_show/hide.
#  - Support for ATTR_hard <surface>.
#  - Support for materials.
#  - Add sorting by group name.
#
# 2006-08-17 v2.30
#  - Speed up export by successively filtering triangle list.
#  - Support for slung_load_weight.
#
# 2006-10-03 v2.31
#  - Fix for nested animation translations.
#
# 2006-10-03 v2.32
#  - Fix for animations with duplicate show/hide values.
#
# 2006-12-04 v2.34
#  - Fix for weird sim/weather datarefs.
#  - ANIM_show/hide commands output in order found.
#
# 2007-02-26 v2.35
#  - Select problematic objects on error.
#  - Check for ambiguous dataref leaf names.
#  - Check that dataref indices don't exceed length of array.
#
# 2007-05-09 v2.37
#  - Allow a bone to be a child of a bone in another armature.
#  - Support for smoke_black and smoke_white.
#
# 2007-06-14 v2.39
#  - Use Mesh instead of NMesh for speed.
#  - Support for mesh modifiers.
#  - Info and warnings reported in popup menu - selects objects referred to.
#
# 2007-06-19 v2.40
#  - Fix for models with groups and multiple LODs.
#
# 2007-09-06 v2.41
#  - Tweaked ordering: Lines and Lights after tris. npoly has highest priority.
#
# 2007-09-19 v2.43
#  - Fix for lights in animated models.
#
# 2007-10-02 v2.44
#  - Only correctly named files are treated as cockpit objects.
#
# 2007-11-30 v2.46
#  - Support for custom lights.
#  - Fix for bones connected to parent with "Con" button.
#
# 2007-12-02 v3.00
#  - Animations can use more than two key frames.
#
# 2007-12-05 v3.02
#  - Bones in the same armature can have different frame counts.
#
# 2007-12-11 v3.04
#  - On animation error, highlight the child object.
#  - All dataref values default to 1 (other than first).
#
# 2007-12-21 v3.05
#  - Support for cockpit panel regions.
#
# 2000-01-02 v3.06
#  - Support for ATTR_hard_deck.
#
# 2008-01-20 v3.07
#  - Warn on using v9 features.
#
# 2008-01-21 v3.08
#  - Fix for custom light vertices with no corresponding faces.
#

#
# X-Plane renders polygons in scenery files mostly in the order that it finds
# them - it detects use of alpha and deletes wholly transparent polys, but
# doesn't sort by Z-buffer order.
#
# So we have to sort on export to ensure alpha comes after non-alpha. We also
# sort to minimise attribute state changes, in rough order of expense:
#  - Hard - should be first. Renderer merges hard polys with similar non-hard.
#  - TWOSIDE
#  - Materials
#  - Animations
#  - PANEL - most expensive, put as late as we can
#  - ALPHA - must be last for correctness. Renderer will merge with previous.
#  - NPOLY - negative so polygon offsets come first. Assumed to be on ground
#            so no ordering issues, so can be higher priority than ALPHA.
#  - Lines and lights
#  - Group
#  - Layer
#

import sys
import Blender
from Blender import Armature, Mesh, Lamp, Image, Draw, Window
from Blender.Mathutils import Matrix, RotationMatrix, TranslationMatrix, MatMultVec, Vector, Quaternion, Euler
from XPlaneUtils import Vertex, UV, MatrixrotationOnly, getDatarefs, PanelRegionHandler, getManipulators, make_short_name
from XPlaneExport import *
#import time

datarefs={}

# Default X-Plane (not Blender) material (ambient & specular do jack)
DEFMAT=((1,1,1), (0,0,0), 0)	# diffuse, emission, shiny

#----------------------------------------------------------------------------------------------------------------
# VERTEX DATA TYPES
#----------------------------------------------------------------------------------------------------------------
# These data types store informantion about a single vertex in the model, and typically convert to the string
# representation for an OBJ.
#
# VT: textured vertex, for triangles
# VLINE: colored vertex, for lines
# VLIGHT: RGB light (that is, an old legacy light)
# NLIGHT: a named light
# CLIGHT: a custom light with a dataref and all params
# SMOKE: a smoke puff generator
#
class VT:
    def __init__(self, v, n, uv):
        self.v=v		# Vertex location
        self.n=n		# Vertex normal
        self.uv=uv		# Vertex UV tex coords

    def __str__ (self):
        return "%s\t%6.3f %6.3f %6.3f\t%s" % (self.v, self.n.x, self.n.y,
                                              self.n.z, self.uv)

    def equals (self, b, fudge=Vertex.LIMIT):
        return (self.v.equals(b.v, fudge) and
                self.n.equals(b.n, fudge) and
                self.uv.equals(b.uv))

class VLINE:
    def __init__(self, v, c):
        self.v=v		# Vertex location
        self.c=c		# Vertex color

    def __str__ (self):
        return "%s\t%6.3f %6.3f %6.3f" % (self.v,
                                          round(self.c[0],2),
                                          round(self.c[1],2),
                                          round(self.c[2],2))
    def equals (self, b):
        return (self.v.equals(b.v) and self.c==b.c)

class VLIGHT:
    def __init__(self, v, c):
        self.v=v		# Light location
        self.c=c		# Vertex color

    def __str__ (self):
        return "%s\t%6.3f %6.3f %6.3f" % (self.v,
                                          round(self.c[0],2),
                                          round(self.c[1],2),
                                          round(self.c[2],2))

    def equals (self, b):
        return (self.v.equals(b.v) and self.c==b.c)

class NLIGHT:
    def __init__(self, v, n):
        self.v=v	# Light Location
        self.n=n	# Light Name

    def __str__ (self):
        return "LIGHT_NAMED\t%s\t%s%s" % (self.n, '\t'*(2-len(self.n)/8), self.v)

    def equals (self, b):
        return (isinstance(b,NLIGHT) and self.v.equals(b.v) and self.n==b.n)

class CLIGHT:
    def __init__(self, v, rgba, s, uv1, uv2, d):
        self.v=v		# Light Location
        self.rgba=rgba	# Light Default Color
        self.s=s		# Light Size
        self.uv1=uv1	# Light UV mapping pairs
        self.uv2=uv2
        self.d=d		# Light DAtaref

    def __str__ (self):
        return "LIGHT_CUSTOM\t%s\t%6.3f %6.3f %6.3f %6.3f %9.4f\t%s %s\t%s" % (self.v, self.rgba[0], self.rgba[1], self.rgba[2], self.rgba[3], self.s, self.uv1, self.uv2, self.d)

    def equals (self, b):
        return (isinstance(b,CLIGHT) and self.v.equals(b.v) and self.n==b.n)

class SMOKE:
    def __init__(self, v, n, p):
        self.v=v	# Smoke Puff Location
        self.n=n	# Puff name (obj cmd name for puff: smoke_black or smoke_white)
        self.p=p	# Puff Size

    def __str__ (self):
        return "%s\t%s\t%4.2f" % (self.n, self.v, self.p)

    def equals (self, b):
        return (isinstance(b,SMOKE) and self.v.equals(b.v) and self.n==b.n and self.p==b.p)

#----------------------------------------------------------------------------------------------------------------
# STATE SORTED PRIMITIVE
#----------------------------------------------------------------------------------------------------------------
# The prim class is the heart of the obj exporter.  It holds a single "primitive" (that is, one triange/quad,
# line, light, smoke puff, etc. as well as all of the state information that is being applied to it.
#
# 'Style' is an enum that tells us what kind of primtive we have: a tri, line, vlight (indexed RGB lights) or
# named light.
#
# Note: all point-based primitives that are not indexed (named lights, custom lights, smoke puffs) use the
# nlight style, since they are all equivalent: an XYZ location and some more stuff that can be output as a string.
# Since we may end up with new lights (940 has parameterized lights) it's useful to have it be light-weight to
# introduce new lights.
#
# The "index" field (i) contains differing values depending on what we are.
# - points and lines: the prim contains an array of indices within the master vertex table.  E.g. if we might
#   have 50, 51 for a line.  There are two master vertex tables - for points and lines, so the numbering scheme is
#   type specific.  NOTE: if the prim is a quad in blender, we will have six indices for the two tris that it can
#   be decomposed into.
# - for nlight and vlight styles, we will have in index a ptr to another object, referenced directly, e.g.
#   nlight, vlight, etc.
#
# Each primitive contains "offset" and "count" - that is the span of its indices in the master index table.  When
# a primitive is "indexed" we remember these, so that we can easily identify and consolidate "runs" of tris.  Since
# we index and output primitives in the same order, we tend to get large index runs.
#
# For tris and lines, offset/count is as expected.  For vlight, offset is the index number of the vlight among all
# vlights, and count is always 1.  This does have the effect of producing a lot of LIGHTS statements without
# consolidation.  To fix this, we should consolidate "LIGHTS" stages later, not muck around inside this class.
#
# STATE SORTING
#
# Each state attribute sits inside this class.  Primitives can be compared (See below).  The exporter pulls out
# all primitives for the scene and sorts them by state.  When they are output, this produces the minimal set of
# state transitions possible.
#
# Animation index: each primitive has its animation obj attached, but for the purpose of export, it is most
# efficient to take animation in Dept First Search (DFS) order, so that nested animations don't require re-stating
# the parent animation.  Since the exporter finds animations in this order naturally, we simply record per
# primitive the index number of the animation we attached within the master animation list on the exporter.  This
# way we can simply sort by index number (without having to call "index" on our parent clsas) to rapidly get our
# animations organized.
#
# WARNING: this technique assumes that lights and lines have state - technically this is not really true...lights
# and lines can appear anywhere in the OBJ.  So this implementation will put some unnecessary state changes in front
# of lines/lights to assure a "normal" state going into the lights/lines.  This is actually a good thing.  X-Plane
# has historically had tons of bugs with state change and non-tri primitives...for older x-plane this prevents bugs.
# For newer X-Plane (late v9 versions) the OBJ optimizer inside x-plane handles out-of-state primitives correctly
# and probably discards every unnecessary "padded" attribute, producing the true minimal state change needed to
# draw a light.  So this design doesn't harm a new x-plane and probably fixes old bugs.  Note that in 940 a change
# to a light is a full shader + texture change, plus a bunch of other scary things..that is, it is actually quite
# expensive.  So having the exporter output primitive changes as requiring state change (change of style, and maybe
# change of current attributes) is a pretty accurate representation of what really happens.  (E.g. if you have poly_os
# on and you draw  light, x-plane _does_ turn poly_os off temporarily, then turn it back on again!)
#
class Prim:
    # Flags in sort order - lower indices are tweaked more often
    HARD=1
    DECK=2
    TWOSIDE=4
    PANEL=8	# Should be 2nd last
    ALPHA=16	# Must be last
    NPOLY=32

    SURFACES=[None, 'water', 'concrete', 'asphalt', 'grass', 'dirt', 'gravel', 'lakebed', 'snow', 'shoulder', 'blastpad']
    STYLE=['Tri','Line','VLight','NLight']

    # surface comes here
    BUCKET1=HARD|DECK|TWOSIDE		# Why the bit flags?  So we can filter out and compare parts of the status.  High-flag fields are more expensive.
    # material comes here
    # anim comes here
    BUCKET2=PANEL|ALPHA|NPOLY
    # lines and lights drawn here
    LINES  =PANEL|ALPHA|NPOLY		# These are the flags we use for lines/lights.
    LIGHTS =PANEL|ALPHA|NPOLY
    # group comes here
    # layer comes here

    def __init__ (self, object, group, flags, surface, mat, anim, aidx,style):
        self.i=[]		# indices for lines & tris, VLIGHT/NLIGHT for lights within master geometry table
        self.offset=-1	# range of our indices within the master index table for tris and lines
        self.count=-1
        self.style=style
        self.anim=anim
        self.anim_idx=aidx
        self.flags=flags	# bitmask
        self.region=-1	# image, -1 for no region
        self.surface=surface	# tris: one of Prim.SURFACES
        self.mat=mat		# tris: (diffuse, emission, shiny)
        self.group=group
        self.layer=object.Layer		# This is the set of layers we belong to.
        self.layer_now=-1			# This is the one layer we pay attention to now for sorting or state update.
        self.hasPanelTexture = hasPanelTexture(object) #Ondrej: This stores if the object uses the panel.png.
        self.name = object.name #Ondrej: This stores the object name.

	#----------------------------------------------------------------------------------------------------------------
	# STATE PRIORITIZATION
	#----------------------------------------------------------------------------------------------------------------
	# This tiny piece of code has a huge impact on objects - this is the prioritized list of how we organize state
	# change.  Basically the earlier on the list the state type, the LESS we will change that state.  So for example
	# LOD is first on the list because we can't change LOD, then change back - we must sort to have each LOD on its own.
	# By comparison, hard surface type is at the bottom because it turns out this is a very cheap attribute.  You
	# can read this as saying: the exporter wil sort first by LOD, then by surface.  Thus the surface may be changed many
	# times as it must be reset inside each LOD.
	#
	# So: to see other optimizations, simply change the order of this loop.  A few interesting notes:
	# - Primitive type of line/light (self.style) is state, so we can force consoldiation by primitive type.  This might
	#   pay off in some cases - testing is needed!
	# - Animation (by index) is state, so we can choose to prioritize other change over animation.  The exporter will
	#   put the animation in twice to minimize other state change.

    def __cmp__ (self,other):
        if self.layer_now != other.layer_now:					# LOD - highest prio, must be on outside
            return cmp(self.layer_now,other.layer_now)
        elif self.group != other.group:					# respect groups, then
            return cmp_grp(self.group,other.group)
        elif (self.flags&Prim.BUCKET2) != (other.flags&Prim.BUCKET2):
            return cmp((self.flags&Prim.BUCKET2),(other.flags&Prim.BUCKET2))
        elif self.anim_idx != other.anim_idx:					# don't dupe animation...well except for panels.
            return cmp(self.anim_idx,other.anim_idx)
        elif self.mat != other.mat:
            return cmp_mat(self.mat,other.mat)
        elif (self.flags&Prim.BUCKET1) != (other.flags&Prim.BUCKET1):
            return cmp((self.flags&Prim.BUCKET1),(other.flags&Prim.BUCKET1))
        elif self.region != other.region:				# cockpit tex and materials mean shader change, as do some of the flags
            return cmp(self.region,other.region)
        elif self.style != other.style:
            return cmp(self.style,other.style)
        else:
            return cmp(self.surface,other.surface)

def cmp_mat(a, b):
    if a == DEFMAT:
        return -1
    elif b == DEFMAT:
        return 1
    else:
        return cmp(a,b)

def cmp_grp(a, b):
    if a == None:
        return -1
    elif b == None:
        return 1
    else:
        return cmp(a.name, b.name)

#------------------------------------------------------------------------
#-- OBJexport --
#------------------------------------------------------------------------
class OBJexport8:

    #------------------------------------------------------------------------
    def __init__(self, filename):
        #--- public you can change these ---
        self.verbose=2	# level of verbosity in console 0-none, 1-some, 2-most
        self.debug=1	# extra debug info in console

        #--- class private don't touch ---
        self.file=None
        self.filename=filename
        self.iscockpit=(filename.lower().endswith("_cockpit.obj") or
                        filename.lower().endswith("_cockpit_inn.obj") or
                        filename.lower().endswith("_cockpit_out.obj"))
        self.layermask=1
        self.texture=None
        self.regions={}		# (x,y,width,height) by image
        self.drawgroup=None
        self.slung=0
        self.linewidth=0.101
        self.nprim=0		# Number of X-Plane primitives exported
        self.log=[]
        self.v9=False		# Used v9 features

        #
        # Attribute tracking variables.  This is the last state that we wrote into the OBJ file.
        # UpdateAttr compares these to what it needs and writes only the changes.
        #
        self.hardness=0
        self.surface=None
        self.mat=DEFMAT
        self.twoside=False
        self.npoly=True
        self.panel=False
        self.region=-1
        self.alpha=False	# implicit - doesn't appear in output file
        self.layer=0
        self.group=None
        self.lod=None		# list of lod limits
        self.anim=Anim(self, None)

        #
        # Index list tracking.  When we accumulate triangles or lines, we simply track what range
        # we have written here.  When we write more, we simply extend the region (if the regions are
        # contiguous.  This lets us consolidate 25000 tris into one TRIS.  -1,-1 is used to indicate
        # that we don't have an "open" list.
        self.tri_offset=-1
        self.tri_count=-1
        self.tri_ins=""
        self.line_offset=-1
        self.line_count=-1
        self.line_ins=""

        #
        # Global vertex lists
        #
        self.vt=[]
        self.vline=[]
        self.vlights=[]							# Actual vlight objs get put here as well as inside the prim, because they are indexed.
        self.prims=[]							# Master primitive lists

        #
        # Global list of all known animations, materials, groups.  We need groups because we have to search top-down to find objs.
        # We need animations to convert anim to index for sorting.  Ben say: I think we do NOT need a global material list anymore.
        #
        self.anims=[Anim(self, None)]
#       self.mats=[DEFMAT]	# list of (diffuse, emission, shiny)
        if Blender.Get('version')>=242:	# new in 2.42
            self.groups=Blender.Group.Get()
            self.groups.sort(lambda x,y: cmp(x.name.lower(), y.name.lower()))
        else:
            self.groups=[]

        #
        # When we have a mesh on an armature, it might be that the same mesh is used multiple times.  This lets us
        # look for duplicates and reuse them.
        #
        self.animcands=[]	# indices into tris of candidates for reuse

    #------------------------------------------------------------------------
    def export(self, scene):
        theObjects = scene.objects

        print 'Starting OBJ export to ' + self.filename
        if not checkFile(self.filename):
            return

        Window.WaitCursor(1)
        Window.DrawProgressBar(0, 'Examining textures')
        self.texture=getTexture(self,theObjects,False,8)

        if self.verbose:
            print 'Texture\t"%s"' % self.texture

        #clock=time.clock()	# Processor time
        frame=Blender.Get('curframe')

        self.file = open(self.filename, 'w')
        self.writeHeader ()
        self.writeObjects (theObjects)
        checkLayers (self, theObjects)
        if self.regions or self.v9:
            print 'Warn:\tThis object requires X-Plane v9'
            self.log.append(('This object requires X-Plane v9', None))


        Blender.Set('curframe', frame)
        #scene.update(1)
        #scene.makeCurrent()	# see Blender bug #4696
        Window.DrawProgressBar(1, 'Finished')
        Window.WaitCursor(0)
        #print "%s CPU time" % (time.clock()-clock)
        print "Finished - exported %s primitives\n" % self.nprim
        if self.log:
            r=Draw.PupMenu(("Exported %s primitives%%t|" % self.nprim)+'|'.join([a[0] for a in self.log]))
            if r>0: raise ExportError(None, self.log[r-1][1])
        else:
            Draw.PupMenu("Exported %s primitives%%t|OK" % self.nprim)

	#------------------------------------------------------------------------
    def writeHeader (self):
        if 'blender.app' in Blender.sys.progname:
            systype='A'
        else:
            systype='I'
        self.file.write("%s\n800\nOBJ\n\n" % systype)
        if self.texture:
            self.file.write("TEXTURE\t\t%s\n" % self.texture)
            l=self.texture.rfind('.')
            if l!=-1 and self.texture[l-3:l].upper()!='LIT':
                self.file.write("TEXTURE_LIT\t%s_LIT%s\n" %(self.texture[:-4],
                                                            self.texture[-4:]))
                self.file.write("TEXTURE_NORMAL\t%s_NML%s\n" %(self.texture[:-4],
                                                            self.texture[-4:]))


        else:	# X-Plane barfs if no texture specified
            self.file.write("TEXTURE\t\n")
        for img in self.regions.keys():
            (n,x,y,width,height)=self.regions[img]
            self.file.write("COCKPIT_REGION\t%4d %4d %4d %4d\n" % (x,y,x+width,y+height))

    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    # MASTER OUTPUT FUNCTION
    #------------------------------------------------------------------------
    #------------------------------------------------------------------------
    def writeObjects (self, theObjects):

        if self.layermask==1:
            lseq=[1]
        else:
            lseq=[1,2,4]

        # Speed optimisation
        if self.iscockpit:
            surfaces=[None]
        else:
            surfaces=Prim.SURFACES
        regionimages=[None]+self.regions.keys()
        h=PanelRegionHandler()

		#------------------------------------------------------------------------
        # SCENE EXPLORATION
	    #------------------------------------------------------------------------
		# Step 1 - we go through all of the blender objects we are exporting and
		# "sort" them - that is, dump their individual primitives (faces, lines,
		# etc) into the master primitive bucket.  When we are done, everything
		# we care about is in our export obj somewhere.

        # Build global vertex lists
        nobj=len(theObjects)
        for o in range (nobj-1,-1,-1):
            object=theObjects[o]
            if not object.Layer&self.layermask or h.isHandlerObj(object):
                continue
            Window.DrawProgressBar(float(nobj-o)*0.4/nobj,
                                   "Exporting %d%% ..." % ((nobj-o)*40/nobj))
            objType=object.getType()
            if objType == 'Mesh':
                if isLine(object, self.linewidth):
                    self.sortLine(object)
                elif isLight(object):
                    self.sortLamp(object)
                else:
                    self.sortMesh(object)
            #elif objType in ['Curve','Surf']:
            #    self.sortMesh(object)
            elif objType=='Lamp':
                self.sortLamp(object)
            elif objType=='Armature':
                pass    # dealt with separately
            elif objType == 'Empty':
                for prop in object.getAllProperties():
                    if prop.type in ['INT', 'FLOAT'] and prop.name.strip().startswith('group_'):
                        self.drawgroup=(prop.name.strip()[6:], int(prop.data))
                        if not self.drawgroup[0] in ['terrain', 'beaches', 'shoulders', 'taxiways', 'runways', 'markings', 'airports', 'roads', 'objects', 'light_objects', 'cars']:
                            raise ExportError('Invalid drawing group "%s" in "%s"' % (self.drawgroup[0], object.name), [object])
                    elif prop.type in ['INT', 'FLOAT'] and prop.name.strip()=='slung_load_weight':
                        self.slung=prop.data
            #elif objType not in ['Camera','Lattice']:
            #    print 'Warn:\tIgnoring %s "%s"' % (objType.lower(),object.name)
            #    self.log.append(('Ignoring %s "%s"' % (objType.lower(), object.name),[object]))

        #------------------------------------------------------------------------
        # STATE SORT
        #------------------------------------------------------------------------
		# First set layer_now to something sane.  The lowest included bit
		# would be best, but for now just grouping all layer 1 memberships as
		# "just 1" is good enough to get the critical effect: not reordering
		# layer 1 items by their other-layer membership.
        for p in self.prims:
            if p.layer & 1:
                p.layer_now = 1
            else:
                p.layer_now = p.layer

		# This is what munges the OBJ order.  Prims contains everything we want
		# to output, tagged with state.  Now we will have it in the order we want
		# to write the file.
        self.prims.sort()

		#------------------------------------------------------------------------
		# BUILD INDICES
		#------------------------------------------------------------------------
		# Now we will go throguh all of the primitives and build the master index
		# list.  The primitives already have their vertex reservations (E.g. the
		# number of "VT", etc.  We must do at least two pases over the geometry
		# to get lines after lights. (Q: does x-plane really care?)  We could
		# do lights with lines for more speed.

        indices=[]
        progress=0.0
        for tri in self.prims:
            if tri.style=='Tri':
                tri.offset=len(indices)
                indices.append(tri.i[0])
                indices.append(tri.i[1])
                indices.append(tri.i[2])
                if len(tri.i)==4:    # quad
                    indices.append(tri.i[0])
                    indices.append(tri.i[2])
                    indices.append(tri.i[3])
                tri.count=len(indices)-tri.offset
        for line in self.prims:
            if line.style=='Line':
                line.offset=len(indices)
                indices.append(line.i[0])
                indices.append(line.i[1])
                line.count=len(indices)-line.offset

        # Lights
        for light in self.prims:
            if light.style=='VLight':
                light.offset=len(self.vlights)
                self.vlights.append(light)
                light.count=1

		#------------------------------------------------------------------------
		# WRITE OUT ALL HEADERS, INDEX TABLES, AND OTHER META DATA
		#------------------------------------------------------------------------
        self.nprim=len(self.vt)+len(self.vline)+len(self.vlights)
        self.file.write("POINT_COUNTS\t%d %d %d %d\n\n" % (len(self.vt),
                                                           len(self.vline),
                                                           len(self.vlights),
                                                           len(indices)))
        Window.DrawProgressBar(0.8, 'Exporting 80% ...')
        for vt in self.vt:
            self.file.write("VT\t%s\n" % vt)
        if self.vt:
            self.file.write("\n")

        for vline in self.vline:
            self.file.write("VLINE\t%s\n" % vline)
        if self.vline:
            self.file.write("\n")

        for light in self.vlights:
            self.file.write("VLIGHT\t%s\n" % light.i)
        if self.vlights:
            self.file.write("\n")

        Window.DrawProgressBar(0.9, 'Exporting 90% ...')
        n=len(indices)
        for i in range(0, n-9, 10):
            self.file.write("IDX10\t"+' '.join([str(j) for j in indices[i:i+10]])+"\n")
        for i in range(n-(n%10), n):
            self.file.write("IDX\t%d\n" % indices[i])

        if self.slung:
            self.file.write("\nslung_load_weight\t%s\n" % self.slung)
        if self.drawgroup:
            self.file.write("\nATTR_layer_group\t%s\t%d\n" % (
                self.drawgroup[0], self.drawgroup[1]))

		#------------------------------------------------------------------------
		# WRITE OUT COMMAND TABLE
		#------------------------------------------------------------------------
		# The command table is written by writing out each primitive.  We update
		# ATTRs between each one to sync state.  99% of the time, that means no
		# state change because we sorted.
		#
		# We must treat each style in a single loop or else we will be implicitly
		# pulling out all the lines from tris, etc. which will mean LODs
		# get duplicated (which is illegal!)

        for l in lseq:
            for prim in self.prims:
                if prim.layer & l:
                    if l > 1:
                        prim.flags = prim.flags & ~(Prim.HARD|Prim.DECK)
                    prim.layer_now = l                	# Update layer_now to the layer we "focus" on now, so update_attr knows what we are doing.
                    if prim.style=='Tri':
                        self.updateAttr(prim)
                        self.accum_tri(prim.anim.ins(),prim.offset,prim.count)
                    elif prim.style=='Line':
                        self.updateAttr(prim)
                        self.accum_line(prim.anim.ins(),prim.offset,prim.count)
                    elif prim.style=='VLight':
                        self.updateAttr(prim)
                        self.file.write("%sLIGHTS\t%d %d\n" %
                                         (prim.anim.ins(),prim.offset,prim.count))
                    elif prim.style=='NLight':
                        self.updateAttr(prim)
                        self.file.write("%s%s\n" %
                                            (prim.anim.ins(), prim.i))

		# Close triangles in the final layer
        self.flush_prim()
        # Close animations in final layer
        while not self.anim.equals(Anim(self, None)):
            #Mike Format the manipulator output
            if self.anim.manipulator != None:
                self.file.write("%sATTR_no_cockpit\n" % self.anim.ins())
            self.anim=self.anim.anim
            self.file.write("%sANIM_end\n" % self.anim.ins())

        self.file.write("\n# Built with Blender %4.2f. Exported with XPlane2Blender %s.\n" % (float(Blender.Get('version'))/100, __version__))
        self.file.close()

#        if not n==len(offsets)==len(counts):
#           raise ExportError('Bug - indices out of sync')

    #------------------------------------------------------------------------
	# SORTING LAMPS
    #------------------------------------------------------------------------
    def sortLamp(self, object):

        (anim, mm, aidx)=self.makeAnim(object)

        if object.getType()=='Mesh':
            # This is actually a custom light - material has HALO set
            mesh=object.getData(mesh=True)
            mats=mesh.materials
            material=mats[0]    # may not have any faces - assume 1st material
            rgba=[material.R, material.G, material.B, material.alpha]
            mtex=material.getTextures()[0]
            if mtex:
                uv1=UV(mtex.tex.crop[0], mtex.tex.crop[1])
                uv2=UV(mtex.tex.crop[2], mtex.tex.crop[3])
            else:
                uv1=UV(0,0)
                uv2=UV(1,1)

            # get RGBA and name properties
            dataref='NULL'
            for prop in object.getAllProperties():
                if prop.name in ['R','G','B','A']:
                    if prop.type in ['INT', 'FLOAT']:
                        rgba[['R','G','B','A'].index(prop.name)]=float(prop.data)
                    else:
                        raise ExportError('Unsupported data type for property "%s" in custom light "%s"' % (prop.name, object.name), [object])
                elif prop.name=='name':
                    if prop.type!='STRING': raise ExportError('Unsupported data type for dataref in custom light "%s"' % object.name, [object])
                    ref=prop.data.strip()
                    if ref in datarefs and datarefs[ref]:
                        (path, n)=datarefs[ref]
                        dataref=path
                        if n!=9: raise ExportError('Dataref %s can\'t be used for custom lights' % dataref, [object])
                    else:
                        dataref=getcustomdataref(object, object, 'custom light', [ref])

            for v in mesh.verts:
                light=Prim(object, self.findgroup(object), Prim.LIGHTS, False, DEFMAT, anim, aidx,'NLight')
                light.i=CLIGHT(Vertex(v.co[0], v.co[1], v.co[2], mm),
                               rgba, material.haloSize,
                               uv1, uv2, dataref)
                self.prims.append(light)
            return

        light=Prim(object, self.findgroup(object), Prim.LIGHTS, False, DEFMAT, anim, aidx,'VLight')

        lamp=object.getData()
        name=object.name
        special=0

        if lamp.getType() != Lamp.Types.Lamp:
            print 'Info:\tIgnoring Area, Spot, Sun or Hemi lamp "%s"' % name
            self.log.append(('Ignoring Area, Spot, Sun or Hemi lamp "%s"' % name, [object]))
            return

        if self.verbose:
            print 'Info:\tExporting Light "%s"' % name

        if '.' in name: name=name[:name.index('.')]
        lname=name.lower().split()
        c=[0,0,0]
        if 'pulse' in lname:
            c[0]=c[1]=c[2]=9.9
            special=1
        elif 'strobe' in lname:
            c[0]=c[1]=c[2]=9.8
            special=1
        elif 'traffic' in lname:
            c[0]=c[1]=c[2]=9.7
            special=1
        elif 'flash' in lname:
            c[0]=-lamp.col[0]
            c[1]=-lamp.col[1]
            c[2]=-lamp.col[2]
        elif 'lamp' in lname:
            c[0]=lamp.col[0]
            c[1]=lamp.col[1]
            c[2]=lamp.col[2]
        elif name in ['smoke_black', 'smoke_white']:
            light.i=SMOKE(Vertex(0,0,0, mm), name, lamp.energy)
            light.style='NLight'
            self.prims.append(light)
            return
        else:    # named light
            for prop in object.getAllProperties():
                if prop.name.lower()=='name': name=str(prop.data).strip()
            light.i=NLIGHT(Vertex(0,0,0, mm), name)
            light.style='NLight'
            self.prims.append(light)
            return

        light.i=VLIGHT(Vertex(0,0,0, mm), c)
        self.prims.append(light)


    #------------------------------------------------------------------------
	# SORTING LINES
    #------------------------------------------------------------------------
    def sortLine(self, object):
        if self.verbose:
            print 'Info:\tExporting Line "%s"' % object.name

        (anim, mm, aidx)=self.makeAnim(object)
        line=Prim(object, self.findgroup(object), Prim.LINES, False, DEFMAT, anim, aidx,'Line')

        mesh=object.getData()
        face=mesh.faces[0]

        v=[]
        for i in range(4):
            v.append(Vertex(face.v[i][0],face.v[i][1],face.v[i][2], mm))
        if (v[0].equals(v[1],self.linewidth) and
            v[2].equals(v[3],self.linewidth)):
            i=0
        else:
            i=1
        v1=Vertex((v[i].x+v[i+1].x)/2,
                  (v[i].y+v[i+1].y)/2,
                  (v[i].z+v[i+1].z)/2)
        v2=Vertex((v[i+2].x+v[(i+3)%4].x)/2,
                  (v[i+2].y+v[(i+3)%4].y)/2,
                  (v[i+2].z+v[(i+3)%4].z)/2)

        if len(mesh.materials)>face.mat and mesh.materials[face.mat]:
            c=[mesh.materials[face.mat].R,
               mesh.materials[face.mat].G,
               mesh.materials[face.mat].B,]
        else:
            c=[0.5,0.5,0.5]

        for v in [v1,v2]:
            vline=VLINE(v, c)

            for j in range(len(self.vline)):
                q=self.vline[j]
                if vline.equals(q):
                    line.i.append(j)
                    break
            else:
                j=len(self.vline)
                self.vline.append(vline)
                line.i.append(j)

        self.prims.append(line)


    #------------------------------------------------------------------------
	# SORTING MESHES
    #------------------------------------------------------------------------
    def sortMesh(self, object):

        mesh=object.getData(mesh=True)
        mats=mesh.materials

        if object.getType()!='Mesh' or object.modifiers:
            # use dummy mesh with modifiers applied instead
            mesh=Mesh.New()
            mesh.getFromObject(object)

        (anim, mm, aidx)=self.makeAnim(object)
        hasanim=not anim.equals(Anim(self, None))
        nm=MatrixrotationOnly(mm, object)
        # Vertex order, taking into account negative scaling
        if object.SizeX*object.SizeY*object.SizeZ<0:
            seq=[[],[],[],[0,1,2],[0,1,2,3]]
        else:
            seq=[[],[],[],[2,1,0],[3,2,1,0]]

        if self.verbose:
            print 'Info:\tExporting Mesh "%s"' % object.name

        if self.debug:
            print 'Mesh "%s" %s faces' % (object.name, len(mesh.faces))

        group=self.findgroup(object)
        hardness=Prim.HARD
        surface=None
        if not self.iscockpit:
            for prop in object.getAllProperties():
                if prop.name.strip().lower()=='surface':
                    if str(prop.data).strip() in Prim.SURFACES:
                        surface=prop.data.strip()
                    else:
                        raise ExportError('Invalid surface "%s" for face in mesh "%s"' % (prop.data, object.name), [object])
                elif prop.name.strip().lower()=='deck' and prop.data:
                    print prop, prop.name, prop.data
                    hardness=Prim.DECK

        # Optimisation: Children of animations might be dupes. This test only
        # looks for exact duplicates, but this can reduce vertex count by ~10%.
        twosideerr=[]
        harderr=[]
        degenerr=[]
        mode=Mesh.FaceModes.DYNAMIC
        if hasanim:
            animcands=list(self.animcands)    # List of candidate tris
            trino=0
            fudge=Vertex.LIMIT*10        # Be more lenient
            for f in mesh.faces:
                if mesh.faceUV: mode=f.mode
                n=len(f.v)
                if not n in [3,4]:
                    pass
                elif not (mode & Mesh.FaceModes.INVISIBLE):
                    for i in seq[n]:
                        nmv=f.verts[i]
                        vertex=Vertex(nmv.co[0], nmv.co[1], nmv.co[2], mm)
                        if not f.smooth:
                            norm=Vertex(f.no, nm)
                        else:
                            norm=Vertex(nmv.no, nm)
                        if mode & Mesh.FaceModes.TEX:
                            uv=UV(f.uv[i][0], f.uv[i][1])
                        else:    # File format requires something - using (0,0)
                            uv=UV(0,0)
                        vt=VT(vertex, norm, uv)

                        j=0
                        while j<len(animcands):
                            if not vt.equals(self.vt[self.prims[animcands[j]+trino].i[seq[n][i]]], fudge):
                                animcands.pop(j)    # no longer a candidate
                            else:
                                j=j+1

                    if not len(animcands):
                        break    # exhausted candidates
                    trino+=1
            else:
                # Success - re-use tris starting at self.vt[animcands[0]]
                trino=0
                for f in mesh.faces:
                    if mesh.faceUV: mode=f.mode
                    n=len(f.v)
                    if not n in [3,4]:
                        degenerr.append(f)
                    elif not (mode & Mesh.FaceModes.INVISIBLE):
                        if f.mat<len(mats) and mats[f.mat]:
                            material=mats[f.mat]
                            # diffuse, emission, shiny
                            mat=((material.R, material.G, material.B),
                                 (material.mirR*material.emit,
                                  material.mirG*material.emit,
                                  material.mirB*material.emit), material.spec)
#                            if not mat in self.mats: self.mats.append(mat)
                        else:
                            mat=DEFMAT
                        face=Prim(object, group, 0, None, mat, anim, aidx,'Tri')

                        if mode & Mesh.FaceModes.TEX:
                            if len(f.uv)!=n:
                                raise ExportError('Missing UV in mesh "%s"' % object.name, [object])
                            if f.transp == Mesh.FaceTranspModes.ALPHA:
                                face.flags|=Prim.ALPHA

                        if mode & Mesh.FaceModes.TWOSIDE:
                            face.flags|=Prim.TWOSIDE
                            twosideerr.append(f)

                        if not mode&Mesh.FaceModes.TILES or self.iscockpit:
                            face.flags|=Prim.NPOLY

                        if self.iscockpit and mode&Mesh.FaceModes.TEX:
                            if f.image in self.regions:
                                face.flags=(face.flags|Prim.PANEL)&~Prim.ALPHA
                                face.region=self.regions.keys().index(f.image)
                            elif f.image and 'panel.' in f.image.name.lower():
                                face.flags|=Prim.PANEL

                        if not self.iscockpit and object.Layer&1 and not mode&Mesh.FaceModes.DYNAMIC:
                            face.flags|=hardness
                            face.surface=surface
                            harderr.append(f)

                        for i in range(n):
                            face.i.append(self.prims[animcands[0]+trino].i[i])

                        self.prims.append(face)
                        trino+=1

                if degenerr and self.verbose:
                    print 'Info:\tIgnoring %s degenerate face(s) in mesh "%s"' % (len(degenerr), object.name)
                    self.log.append(('Ignoring %s degenerate face(s) in mesh "%s"' % (len(degenerr), object.name), (object, mesh, degenerr)))
                if harderr:
                    print 'Info:\tFound %s hard face(s) in mesh "%s"' % (len(harderr), object.name)
                    self.log.append(('Found %s hard face(s) in mesh "%s"' % (len(harderr), object.name), (object, mesh, harderr)))
                if twosideerr:
                    print 'Info:\tFound %s two-sided face(s) in mesh "%s"' % (len(twosideerr), object.name)
                    self.log.append(('Found %s two-sided face(s) in mesh "%s"' % (len(twosideerr), object.name), (object, mesh, twosideerr)))
                return

        # Either no animation, or no matching animation
        starttri=len(self.prims)
        # Optimisation: Build list of faces and vertices
        vti = [[] for i in range(len(mesh.verts))]    # indices into vt

        for f in mesh.faces:
            if mesh.faceUV: mode=f.mode
            n=len(f.v)
            if not n in [3,4]:
                degenerr.append(f)
            elif not (mode & Mesh.FaceModes.INVISIBLE):
                if f.mat<len(mats) and mats[f.mat]:
                    material=mats[f.mat]
                    # diffuse, emission, shiny
                    mat=((material.R, material.G, material.B),
                         (material.mirR*material.emit,
                          material.mirG*material.emit,
                          material.mirB*material.emit), material.spec)
#                    if not mat in self.mats: self.mats.append(mat)
                else:
                    mat=DEFMAT
                face=Prim(object, group, 0, None, mat, anim, aidx,'Tri')

                if mode & Mesh.FaceModes.TEX:
                    if len(f.uv)!=n:
                        raise ExportError('Missing UV for face in mesh "%s"' % object.name, (object, mesh, [f]))
                    if f.transp == Mesh.FaceTranspModes.ALPHA:
                        face.flags|=Prim.ALPHA

                if mode & Mesh.FaceModes.TWOSIDE:
                    face.flags|=Prim.TWOSIDE
                    twosideerr.append(f)

                if not mode&Mesh.FaceModes.TILES or self.iscockpit:
                    face.flags|=Prim.NPOLY

                if self.iscockpit and mode&Mesh.FaceModes.TEX:
                    if f.image in self.regions:
                        face.flags=(face.flags|Prim.PANEL)&~Prim.ALPHA
                        face.region=self.regions.keys().index(f.image)
                    elif f.image and 'panel.' in f.image.name.lower():
                        face.flags|=Prim.PANEL

                if not self.iscockpit and object.Layer&1 and not mode&Mesh.FaceModes.DYNAMIC:
                    face.flags|=hardness
                    face.surface=surface
                    harderr.append(f)

                for i in seq[n]:
                    nmv=f.verts[i]
                    vertex=Vertex(nmv.co[0], nmv.co[1], nmv.co[2], mm)
                    if not f.smooth:
                        norm=Vertex(f.no, nm)
                    else:
                        norm=Vertex(nmv.no, nm)
                    if mode & Mesh.FaceModes.TEX:
                        uv=UV(f.uv[i][0], f.uv[i][1])
                    else:    # File format requires something - using (0,0)
                        uv=UV(0,0)
                    vt=VT(vertex, norm, uv)

                    # Does one already exist?
                    #for j in range(len(self.vt)):    # Search all meshes
                    for j in vti[nmv.index]:    	# Search this vertex
                        q=self.vt[j]
                        if vt.equals(q):
                            q.uv= (q.uv+ vt.uv)/2
                            face.i.append(j)
                            break
                    else:
                        j=len(self.vt)
                        self.vt.append(vt)
                        face.i.append(j)
                        vti[nmv.index].append(j)

                self.prims.append(face)

                #if self.debug: print face

        if hasanim:
            # Save tris for matching next
            self.animcands.append(starttri)

        if degenerr and self.verbose:
            print 'Info:\tIgnoring %s degenerate face(s) in mesh "%s"' % (len(degenerr), object.name)
            self.log.append(('Ignoring %s degenerate face(s) in mesh "%s"' % (len(degenerr), object.name), (object, mesh, degenerr)))
        if harderr:
            print 'Info:\tFound %s hard face(s) in mesh "%s"' % (len(harderr), object.name)
            self.log.append(('Found %s hard face(s) in mesh "%s"' % (len(harderr), object.name), (object, mesh, harderr)))
        if twosideerr:
            print 'Info:\tFound %s two-sided face(s) in mesh "%s"' % (len(twosideerr), object.name)
            self.log.append(('Found %s two-sided face(s) in mesh "%s"' % (len(twosideerr), object.name), (object, mesh, twosideerr)))


    #------------------------------------------------------------------------
    # Return name of group that this object belongs to
    def findgroup(self, ob):
        for group in self.groups:
            if ob in group.objects:
                return group
        return None

    #------------------------------------------------------------------------
    # Return (Anim object, Transformation for object relative to world/parent, index of anim in master list)
    def makeAnim(self, child):

        #return (Anim(None), mm)	# test - return frame 1 position

        anim=Anim(self, child)

        # Add parent anims first
        al=[]
        a=anim
        while not a.equals(Anim(self, None)):
            al.insert(0, a)
            a=a.anim

        Blender.Set('curframe', 1)
        #scene=Blender.Scene.GetCurrent()
        #scene.update(1)
        #scene.makeCurrent()	# see Blender bug #4696

        #mm=Matrix(child.getMatrix('localspace')) doesn't work in 2.40alpha
        mm=child.getMatrix('worldspace')

        for a in al:
            # Hack!
            # We need the position of the child in bone space - ie
            # rest position relative to bone root.
            # child.getMatrix('localspace') doesn't return this in 2.40.
            # So un-apply animation from child's worldspace in frame 1:
            #  - get child in worldspace in frame 1 (mm)
            #  - translate so centre of rotation is at origin (-bone root)
            #  - unrotate (-pose rotation)

            if self.debug:
                print "pre\t%s" % mm.rotationPart().toEuler()
                print "\t%s" % mm.translationPart()

            # anim is in X-Plane space. But we need Blender space. Yuck.
            if a.t:
                mm=Matrix(mm[0],mm[1],mm[2],
                          mm[3]-Vector([a.t[0].x, -a.t[0].z, a.t[0].y, 0]))

            if a.r and a.a[0]:
                tr=RotationMatrix(a.a[0], 4, 'r',
                                  -Vector([a.r[0].x, -a.r[0].z, a.r[0].y]))
                mm=mm*tr
                if self.debug:
                    print "rot\t%s" % tr.rotationPart().toEuler()

            if self.debug:
                print "post\t%s" % mm.rotationPart().toEuler()
                print "\t%s" % mm.translationPart()

            # Add Anim, but avoid dups
            for b in self.anims:
                if a.equals(b):
                    anim=b
                    break
            else:
                self.anims.append(a)
                anim=a	# The anim we just made is the last one in the list

        if anim.equals(Anim(self,None)):
            return (anim, mm, -1)
        else:
            return (anim, mm, self.anims.index(anim))


    #------------------------------------------------------------------------
	# PRIMITIVE FLUSHING UTILS
    #------------------------------------------------------------------------
	# These utils manage the output of TRIS and LINES commands, accumulating
	# index range and writing the minimal number of TRIS/LINES
    def flush_prim(self):
        if self.tri_offset != -1:
            self.file.write("%sTRIS\t%d %d\n" %
                (self.tri_ins,self.tri_offset,self.tri_count))
        if self.line_offset != -1:
            self.file.write("%sLINES\t%d %d\n" %
                (self.line_ins,self.line_offset,self.line_count))

        self.tri_offset=-1
        self.tri_count=-1
        self.line_offset=-1
        self.line_count=-1


    def accum_tri(self,ins,offset, count):
        if (self.tri_offset+self.tri_count) != offset or self.line_offset != -1:
            self.flush_prim()
            self.tri_offset=offset
            self.tri_count=count
            self.tri_ins=ins
        else:
            self.tri_count+=count
            self.tri_ins=ins

    def accum_line(self,ins,offset, count):
        if (self.line_offset+self.line_count) != offset or self.tri_offset != -1:
            self.flush_prim()
            self.line_offset=offset
            self.line_count=count
            self.line_ins=ins
        else:
            self.line_count+=count
            self.line_ins=ins

    #------------------------------------------------------------------------
	# STATE UPDATE CODE
    #------------------------------------------------------------------------
	# This routine writes the ATTRibutes to the OBJ file based on attributes
	# changing.
    def updateAttr(self, prim):
        layer=prim.layer_now
        group=prim.group
        anim=prim.anim
        region=-1
        surface=None
        mat=None
        hardness=None
        twoside=None
        npoly=None
        panel=None
        alpha=None

        if prim.style=='Tri':
            region=prim.region
            surface=prim.surface
            mat=prim.mat
            hardness=prim.flags&(Prim.HARD|Prim.DECK)
            twoside=prim.flags&(Prim.TWOSIDE)
            npoly=prim.flags&(Prim.NPOLY)
            panel=prim.flags&(Prim.PANEL)
            alpha=prim.flags&(Prim.ALPHA)
            #Ondrej: Store hasPanelTexture Flag
            hasPanelTexture=prim.hasPanelTexture

        # Write in sort order for readability
        if layer!=self.layer:
            # Reset all attributes
            self.flush_prim()
            while not self.anim.equals(Anim(self, None)):
                self.anim=self.anim.anim
                self.file.write("%sANIM_end\n" % self.anim.ins())

            self.surface=None
            self.mat=DEFMAT
            self.twoside=False
            self.npoly=True
            self.panel=False
            self.region=-1
            self.alpha=False
            self.group=None
            self.hardness=False
            self.surface=None

            if self.layermask==1:
                self.file.write("\n")
            else:
                self.file.write("\nATTR_LOD\t%d %d\n" % (
                    self.lod[layer/2], self.lod[layer/2+1]))
            self.layer=layer

        if not anim.equals(self.anim):
            olda=[]
            newa=[]
            a=self.anim
            while not a.equals(Anim(self, None)):
                olda.insert(0, a)
                a=a.anim
            a=anim
            while not a.equals(Anim(self, None)):
                newa.insert(0, a)
                a=a.anim
            for i in range(len(olda)-1,-1,-1):
                if i>=len(newa) or not newa[i].equals(olda[i]):
                    #Mike Format the manipulator output
                    oldm = self.anim

                    olda.pop()
                    self.anim=self.anim.anim
                    self.flush_prim()
                    #Mike Format the manipulator output
                    if oldm.manipulator != None:
                        self.file.write("%sATTR_no_cockpit\n" % oldm.ins())

                    self.file.write("%sANIM_end\n" % self.anim.ins())
        else:
            newa=olda=[]

        if self.group!=group:
            self.flush_prim()
            if group==None:
                self.file.write("%s####No_group\n" % self.anim.ins())
            else:
                self.file.write("%s####_group\t%s\n" %(self.anim.ins(),group.name))
            self.group=group

        if npoly!=None:
            if self.npoly and not npoly:
                self.flush_prim()
                self.file.write("%sATTR_poly_os\t2\n" % self.anim.ins())
            elif npoly and not self.npoly:
                self.flush_prim()
                self.file.write("%sATTR_poly_os\t0\n" % self.anim.ins())
            self.npoly=npoly

        # alpha is implicit - doesn't appear in output file
        if alpha!=None:
            if self.alpha and not alpha:
                self.flush_prim()
                self.file.write("%s####_no_alpha\n" % self.anim.ins())
            elif alpha and not self.alpha:
                self.flush_prim()
                self.file.write("%s####_alpha\n" % self.anim.ins())
            self.alpha=alpha

        if panel!=None:
            if self.panel and not panel:
                self.flush_prim()
                if hasPanelTexture:
                    self.file.write("%sATTR_cockpit\n" % self.anim.ins())
                else:
                    self.file.write("%sATTR_no_cockpit\n" % self.anim.ins())
            elif region!=self.region:
                self.flush_prim()
                if hasPanelTexture:
                    self.file.write("%sATTR_cockpit\t%d\n" % (self.anim.ins(), region))
                else:
                    self.file.write("%sATTR_cockpit_region\t%d\n" % (self.anim.ins(), region))
            elif panel and not self.panel:
                self.flush_prim()
                if hasPanelTexture:
                    self.file.write("%sATTR_cockpit\n" % self.anim.ins())
                else:
                    self.file.write("%sATTR_no_cockpit\n" % self.anim.ins())
            self.panel=panel
            self.region=region

        for i in newa[len(olda):]:
            self.flush_prim()
            self.file.write("%sANIM_begin\n" % self.anim.ins())

            #Ondrej: add comment with Object name for easier debugging of obj-files
            if(self.debug):
                self.file.write("%s#%s\n" % (self.anim.ins(),prim.name))
                
            self.anim=i

            #Ondrej: output hasPanelTexture Flag
            if self.verbose:
                print 'Mesh "%s" hasPanelTexture = %s' % (prim.name,hasPanelTexture)

            #Mike Format the manipulator output
            if self.anim.manipulator != None:
                #Ondrej: Set cockpit Attribute depending on Texture used in uv-face
                if hasPanelTexture:
				    self.file.write("%sATTR_cockpit\n" % self.anim.ins())
                else:
                    self.file.write("%sATTR_cockpit_region\n" % self.anim.ins())
                    
            #Ondrej: Set cockpit Attribute depending on Texture used in uv-face
            elif hasPanelTexture:
                self.file.write("%sATTR_cockpit\n" % self.anim.ins())
            else:
                self.file.write("%sATTR_no_cockpit\n" % self.anim.ins())

            for (sh, d, v1, v2) in self.anim.showhide:
                self.file.write("%sANIM_%s\t%s %s\t%s\n" % (
                    self.anim.ins(), sh, v1, v2, d))

            if len(self.anim.t)==0 or (len(self.anim.t)==1 and self.anim.t[0].equals(Vertex(0,0,0))):
                pass
            elif len(self.anim.t)==1:
                # not moving - save a potential accessor callback
                self.file.write("%sANIM_trans\t%s\t%s\t%s %s\t%s\n" % (
                    self.anim.ins(), self.anim.t[0], self.anim.t[0],
                    0, 0, 'no_ref'))
            elif len(self.anim.t)>2 or self.anim.loop:
                self.file.write("%sANIM_trans_begin\t%s\n" % (
                    self.anim.ins(), self.anim.dataref))
                for j in range(len(self.anim.t)):
                    self.file.write("%s\tANIM_trans_key\t%s\t%s\n" % (
                        self.anim.ins(), self.anim.v[j], self.anim.t[j]))
                if self.anim.loop:
                    self.file.write("%s\tANIM_keyframe_loop\t%s\n" % (
                        self.anim.ins(), self.anim.loop))
                self.file.write("%sANIM_trans_end\n" % self.anim.ins())
            else:	# v8.x style
                self.file.write("%sANIM_trans\t%s\t%s\t%s %s\t%s\n" % (
                    self.anim.ins(), self.anim.t[0], self.anim.t[1],
                    self.anim.v[0], self.anim.v[1], self.anim.dataref))

            if len(self.anim.r)==0:
                pass
            elif len(self.anim.r)==1 and len(self.anim.a)==2 and not self.anim.loop:	# v8.x style
                self.file.write("%sANIM_rotate\t%s\t%6.2f %6.2f\t%s %s\t%s\n"%(
                    self.anim.ins(), self.anim.r[0],
                    self.anim.a[0], self.anim.a[1],
                    self.anim.v[0], self.anim.v[1], self.anim.dataref))
            elif len(self.anim.r)==2 and not self.anim.loop:	# v8.x style
                self.file.write("%sANIM_rotate\t%s\t%6.2f %6.2f\t%s %s\t%s\n"%(
                    self.anim.ins(), self.anim.r[0],
                    self.anim.a[0], 0,
                    self.anim.v[0], self.anim.v[1], self.anim.dataref))
                self.file.write("%sANIM_rotate\t%s\t%6.2f %6.2f\t%s %s\t%s\n"%(
                    self.anim.ins(), self.anim.r[1],
                    0, self.anim.a[1],
                    self.anim.v[0], self.anim.v[1], self.anim.dataref))
            elif len(self.anim.r)==1:		# v9.x style, one axis
                self.file.write("%sANIM_rotate_begin\t%s\t%s\n"%(
                    self.anim.ins(), self.anim.r[0], self.anim.dataref))
                for j in range(len(self.anim.a)):
                    self.file.write("%s\tANIM_rotate_key\t%s\t%6.2f\n" % (
                        self.anim.ins(), self.anim.v[j], self.anim.a[j]))
                if self.anim.loop:
                    self.file.write("%s\tANIM_keyframe_loop\t%s\n" % (
                        self.anim.ins(), self.anim.loop))
                self.file.write("%sANIM_rotate_end\n" % self.anim.ins())
            else:				# v9.x style, multiple axes
                for axis in [[0,0,1],[0,1,0],[1,0,0]]:
                    self.file.write("%sANIM_rotate_begin\t%d %d %d\t%s\n"%(
                        self.anim.ins(), axis[0], axis[1], axis[2], self.anim.dataref))
                    for j in range(len(self.anim.r)):
                        self.file.write("%s\tANIM_rotate_key\t%s\t%6.2f\n" % (
                            self.anim.ins(), self.anim.v[j], Quaternion(self.anim.r[j].toVector(3), self.anim.a[j]).toEuler()[axis.index(1)]))
                    if self.anim.loop:
                        self.file.write("%s\tANIM_keyframe_loop\t%s\n" % (
                            self.anim.ins(), self.anim.loop))
                    self.file.write("%sANIM_rotate_end\n" % self.anim.ins())

            #Mike Format the manipulator output
            if self.anim.manipulator != None:
                self.file.write("%s%s\n" % (
                    self.anim.ins(),
                    self.formatManipulator(self.anim.manipulator)))

        if mat!=None:
            if self.mat!=mat and mat==DEFMAT:
                self.flush_prim()
                self.file.write("%sATTR_reset\n" % self.anim.ins())
            else:
                # diffuse, emission, shiny
                if self.mat[0]!=mat[0]:
                    self.flush_prim()
                    self.file.write("%sATTR_diffuse_rgb\t%6.3f %6.3f %6.3f\n" % (self.anim.ins(), mat[0][0], mat[0][1], mat[0][2]))
                if self.mat[1]!=mat[1]:
                    self.flush_prim()
                    self.file.write("%sATTR_emission_rgb\t%6.3f %6.3f %6.3f\n" % (self.anim.ins(), mat[1][0], mat[1][1], mat[1][2]))
                if self.mat[2]!=mat[2]:
                    self.flush_prim()
                    self.file.write("%sATTR_shiny_rat\t%6.3f\n" % (self.anim.ins(), mat[2]))
            self.mat=mat

        if twoside!=None:
            if self.twoside and not twoside:
                self.flush_prim()
                self.file.write("%sATTR_cull\n" % self.anim.ins())
            elif twoside and not self.twoside:
                self.flush_prim()
                self.file.write("%sATTR_no_cull\n" % self.anim.ins())
            self.twoside=twoside

        if hardness!=None:
            if self.hardness and not hardness:
                self.flush_prim()
                self.file.write("%sATTR_no_hard\n" % self.anim.ins())
                self.surface=None
            elif self.hardness!=hardness or self.surface!=surface:
                if surface:
                    thing='\t'+surface
                else:
                    thing=''
                if hardness:
                    if surface:
                        self.flush_prim()
                        self.file.write("%sATTR_hard\t%s\n" % (self.anim.ins(), surface))
                    else:
                        self.flush_prim()
                        self.file.write("%sATTR_hard\n" % self.anim.ins())
                if hardness==Prim.DECK:
                    if surface:
                        self.flush_prim()
                        self.file.write("%sATTR_hard_deck\t%s\n" % (self.anim.ins(), surface))
                    else:
                        self.flush_prim()
                        self.file.write("%sATTR_hard_deck\n" % self.anim.ins())
                self.surface=surface
            self.hardness=hardness

    #------------------------------------------------------------------------
    def formatManipulator(self, manipulator):
        """ Return a string representing a manipular structure.
        Keyword arguments:
        manipulator -- the manipulator dictionary

        """
        if manipulator == None:
            return 'ATTR_manip_none'

        keys = sorted(manipulator.keys())
        manipulator_str = manipulator['99@manipulator-name']
        for key in keys:
            if key == '99@manipulator-name':
                break

            manipulator_str += '\t'
            #print 'key=', key
            data = manipulator[key]

            if type(data).__name__ == 'str':
                manipulator_str += data.strip()

            if type(data).__name__ == 'float':
                manipulator_str += '%6.2f' % data

            if type(data).__name__ == 'int':
                manipulator_str += '%d' % data

        return manipulator_str



#------------------------------------------------------------------------
class Anim:
    def __init__(self, expobj, child, bone=None):
        self.dataref=None	# None if null
        self.r=[]	# 0, 1, 2 or n-1 rotation vectors
        self.a=[]	# rotation angles, 0 or n-1 rotation angles
        self.t=[]	# translation, 0, 1 or n-1 translations
        self.v=[0,1]	# dataref value
        self.loop=0	# loop value (XPlane 9)
        self.showhide=[]	# show/hide values (show/hide, name, v1, v2)
        self.anim=None	# parent Anim
        self.manipulator=None #Mike

        if not child:
            return	# null

        object=child.parent	# child is lamp/mesh. object is parent armature
        if not object or object.getType()!='Armature':
            return

        if Blender.Get('version')<240:
            raise ExportError('Blender version 2.40 or later required for animation')

        self.manipulator = self.getmanipulator(object)

        #if object.parent:
        #    raise ExportError('Armature "%s" has a parent; this is not supported. Use multiple bones within a single armature to represent complex animations.' % object.name, [object])

        if not bone:
            bonename=child.getParentBoneName()
            if not bonename: raise ExportError('%s "%s" has an armature as its parent. Make "%s" the child of a bone' % (child.getType(), child.name, child.name), [child])
            bones=object.getData().bones
            if bonename in bones.keys():
                bone=bones[bonename]
            else:
                raise ExportError('%s "%s" has a deleted bone "%s" as its parent. Either make "%s" the child of an existing bone, or clear its parent' % (child.getType(), child.name, bonename, child.name), [child])

        if bone.parent:
            #print "bp", child, bone.parent
            self.anim=Anim(expobj, child, bone.parent)
        elif object.parent and object.parent.getType()=='Armature':
            # child's parent armature is itself parented to an armature
            bonename=object.getParentBoneName()
            if not bonename: raise ExportError('Bone "%s" has an armature as its parent. Make "%s" the child of another bone' % (bone.name, bone.name), [child])
            bones=object.parent.getData().bones
            if bonename in bones.keys():
                parentbone=bones[bonename]
            else:
                raise ExportError('%s "%s" has a deleted bone "%s" as its parent. Either make "%s" the child of an existing bone, or clear its parent' % (child.getType(), child.name, bonename, child.name), [child])
            #print "ob", object, parentbone
            self.anim=Anim(expobj, object, parentbone)
        else:
            self.anim=Anim(expobj, None)

        if not bone.parent:
            # Hide/show values if eldest bone in its armature
            vals={}
            for prop in object.getAllProperties():
                propname=prop.name.strip()
                for suffix in ['_hide_v', '_show_v']:
                    if not (suffix) in propname: continue
                    digit=propname[propname.index(suffix)+7:]
                    if not digit.isdigit() or not int(digit)&1: continue
                    (ref, v, loop)=self.getdataref(object, child, propname[:propname.index(suffix)], suffix[:-2], int(digit), 2)
                    if not None in v:
                        self.showhide.append((suffix[1:5],ref,v[0],v[1]))

        # find last frame
        framecount=0	# zero based
        action=object.getAction()
        if action and bone.name in action.getChannelNames():
            ipo=action.getChannelIpo(bone.name)
            for icu in ipo:
                for bez in icu.bezierPoints:
                    f=bez.pt[0]
                    if f>int(f):
                        framecount=max(framecount,int(f)+1) # like math.ceil()
                    else:
                        framecount=max(framecount,int(f))

        if framecount<2:
            print 'Warn:\tYou haven\'t created animation keys in frames 1 and 2 for bone "%s" in armature "%s". Skipping this bone.' % (bone.name, object.name)
            expobj.log.append(('Ignoring bone "%s" in armature "%s" - you haven\'t created animation keys in frames 1 and 2' % (bone.name, object.name), [child]))

            if self.showhide:
                # Create a dummy animation to hold hide/show values
                self.dataref='no_ref'	# mustn't eval to False
                self.t=[Vertex(0,0,0)]
            elif bone.parent:
                foo=Anim(expobj, child, bone.parent)
                self.dataref=foo.dataref
                self.r=foo.r
                self.a=foo.a
                self.t=foo.t
                self.v=foo.v
                self.loop=foo.loop
                self.anim=foo.anim
            else:
                self.dataref=None	# is null
            return
        elif framecount>2:
            expobj.v9=True

        (self.dataref, self.v, self.loop)=self.getdataref(object, child, bone.name, '', 1, framecount)
        if None in self.v:
            raise ExportError('Armature "%s" is missing a %s_v%d property' % (object.name, self.dataref.split('/')[-1], 1+self.v.index(None)), [child])

        scene=Blender.Scene.GetCurrent()

        if 0:	# debug
            for frame in range(1,framecount+1):
                Blender.Set('curframe', frame)
                #scene.update(1)
                #scene.makeCurrent()	# see Blender bug #4696
                print "Frame\t%s" % frame
                print child
                print "local\t%s" % child.getMatrix('localspace').rotationPart().toEuler()
                print "\t%s" % child.getMatrix('localspace').translationPart()
                print "world\t%s" % child.getMatrix('worldspace').rotationPart().toEuler()
                print "\t%s" % child.getMatrix('worldspace').translationPart()
                print object
                print "local\t%s" % object.getMatrix('localspace').rotationPart().toEuler()
                print "\t%s" % object.getMatrix('localspace').translationPart()
                print "world\t%s" % object.getMatrix('worldspace').rotationPart().toEuler()
                print "\t%s" % object.getMatrix('worldspace').translationPart()
                print bone
                print "bone\t%s" % bone.matrix['BONESPACE'].rotationPart().toEuler()
                #crashes print "\t%s" % bone.matrix['BONESPACE'].translationPart()
                print "arm\t%s" % bone.matrix['ARMATURESPACE'].rotationPart().toEuler()
                print "\t%s" % bone.matrix['ARMATURESPACE'].translationPart()
                print "head\t%s" % bone.head
                print "tail\t%s" % bone.tail
                print "roll\t%s" % bone.roll
                print ipo
                q = Quaternion([ipo.getCurveCurval('QuatW'),
                                ipo.getCurveCurval('QuatX'),
                                ipo.getCurveCurval('QuatY'),
                                ipo.getCurveCurval('QuatZ')])
                print "ipo\t%s" % q.toEuler()
                print "\t%s %s" % (q.angle, q.axis)
                print "\t%s" % Vector([ipo.getCurveCurval('LocX'),
                                       ipo.getCurveCurval('LocY'),
                                       ipo.getCurveCurval('LocZ')])
            print

        # Useful info in Blender 2.40:
        # child.getMatrix('localspace') - rot & trans rel to arm pre pose
        # child.getMatrix('worldspace') - rot & trans post pose
        # armature.getMatrix('local/worldspace') - abs position pre pose
        # bone.getRestMatrix('bonespace') - broken
        # bone.getRestMatrix('worldspace') - rot & trans rel to arm pre pose
        # bone.head - broken
        # bone.tail - posn of tail rel to armature pre pose
        # ipo - bone position rel to rest posn post pose
        #
        # In X-Plane:
        # Transformations are relative to unrotated position and cumulative
        # Rotations are relative to each other (ie cumulative)

        # Need to unset resting position of parent armature
        object.getData().restPosition=False
        # But grandparent armature (if any) need to be resting, since
        # getMatrix('localspace') doesn't account for rotation due to pose
        a=object.parent
        while a:
            a.getData().restPosition=True
            a=a.parent

        moved=False
        for frame in range(1,framecount+1):
            Blender.Set('curframe', frame)
            #scene.update(1)
            #scene.makeCurrent()	# see Blender bug #4696
            mm=object.getMatrix('worldspace')
            # mm.rotationPart() scaled to be unit size for rotation axis
            rm=MatrixrotationOnly(mm, object)

            if (not (bone.parent and Armature.CONNECTED in bone.options) and
                ipo.getCurve('LocX') and
                ipo.getCurve('LocY') and
                ipo.getCurve('LocZ')):
                t = Vector([ipo.getCurveCurval('LocX'),
                            ipo.getCurveCurval('LocY'),
                            ipo.getCurveCurval('LocZ')])
            else:
                t = Vector(0,0,0)

            t=Vertex(t*bone.matrix['ARMATURESPACE'].rotationPart()+
                     bone.matrix['ARMATURESPACE'].translationPart(),mm)
            # Child offset should be relative to parent
            anim=self.anim
            while not anim.equals(Anim(expobj, None)):
                t=t-anim.t[0]	# mesh location is relative to first frame
                anim=anim.anim
            self.t.append(t)
            if not t.equals(self.t[0]):
                moved=True

            if (ipo.getCurve('QuatW') and
                ipo.getCurve('QuatX') and
                ipo.getCurve('QuatY') and
                ipo.getCurve('QuatZ')):
                q=Quaternion([ipo.getCurveCurval('QuatW'),
                              ipo.getCurveCurval('QuatX'),
                              ipo.getCurveCurval('QuatY'),
                              ipo.getCurveCurval('QuatZ')])
                # In bone space
                qr=Vertex(q.axis*bone.matrix['ARMATURESPACE'].rotationPart(), rm)	# rotation axis
                a = round(q.angle, Vertex.ROUND)	# rotation angle
                if a==0:
                    self.r.append(None)	# axis doesn't matter if no rotation
                    self.a.append(0)
                else:
                    self.r.append(qr)
                    self.a.append(a)
            else:
                self.r.append(None)
                self.a.append(0)

        # Collapse translations if not moving
        if not moved:
            self.t=[self.t[0]]

        # Collapse rotation axes if coplanar
        coplanar=True
        r=None	# first axis
        for i in range(len(self.a)):
            if self.r[i]:
                if not r:
                    r=self.r[i]
                elif r.equals(-self.r[i]):
                    self.r[i]=-self.r[i]
                    self.a[i]=-self.a[i]
                elif not r.equals(self.r[i]):
                    coplanar=False
                    break
        if coplanar:
            if r:
                self.r=[r]
            else:
                self.r=[]
                self.a=[]
        else:
            for i in range(len(self.a)):
                if not self.r[i]:
                    self.r[i]=Vertex(0,1,0)	# arbitrary

        a=object.parent
        while a:
            a.getData().restPosition=False
            a=a.parent


    #------------------------------------------------------------------------
    def getmanipulator(self, object):

        manipulator = 'ATTR_manip_none'
        props = object.getAllProperties()

        for prop in props:
            if prop.name == 'manipulator_type':
                manipulator = prop.data

        if manipulator == 'ATTR_manip_none':
            return None

        manipulator_dict,cursorList = getManipulators()
        keys = sorted(manipulator_dict[manipulator].keys())
        for prop in props:
            if prop.name.startswith(manipulator):
                tmp = prop.name.split('_')
                key = tmp[len(tmp)-1]

                for dict_key in keys:
                    if dict_key.find(key) > 0:
                        key = dict_key
                        break

                manipulator_dict[manipulator][key] = prop.data

        manipulator_dict[manipulator]['99@manipulator-name'] = manipulator
        return manipulator_dict[manipulator]

    #------------------------------------------------------------------------
    def getdataref(self, object, child, name, suffix, first, count):
        if not suffix:
            thing='bone in armature'
            vals=[1 for i in range(count)]
            vals[0]=0
        else:
            thing='property in armature'
            vals=[None for i in range(count)]

        l=name.find('.')
        if l!=-1: name=name[:l]
        name=name.strip()
        # split name into ref & idx
        l=name.find('[')
        if l!=-1 and not name in datarefs:
            ref=name[:l].strip()
            idx=name[l+1:-1]
            if name[-1]!=']' or not idx or not idx.isdigit():
                raise ExportError('Malformed dataref index "%s" in bone "%s" in armature "%s"' % (name[l:], name, object.name), [child])
            idx_str="["+idx+"]"
            idx=int(idx)
            seq=[ref, name]
        else:
            ref=name
            idx_str=""
            idx=None
            seq=[ref]

        props=object.getAllProperties()

        if ref in datarefs and datarefs[ref]:
            (path, n)=datarefs[ref]
            dataref=path+idx_str
            if n==0:
                raise ExportError('Dataref %s can\'t be used for animation' % path+ref, [child])
            elif n==1 and idx!=None:
                raise ExportError('Dataref %s is not an array. Rename the %s to "%s"' % (path+ref, thing, ref), [child])
            elif n!=1 and idx==None:
                raise ExportError('Dataref %s is an array. Rename the %s to "%s[0]" to use the first value, etc' % (path+ref, thing, ref), [child])
            elif n!=1 and idx>=n:
                raise ExportError('Dataref %s has usable values from [0] to [%d]; but you specified [%d]' % (path+ref, n-1, idx), [child])
        else:
            dataref=getcustomdataref(object, child, thing, seq)

        seq.append(make_short_name(dataref))

        # dataref values vn and loop
        loop=0
        for tmpref in seq:
            for val in range(first,first+count):
                valstr="%s%s_v%d" % (tmpref, suffix, val)
                for prop in object.getAllProperties():
                    if prop.name.strip()==valstr:
                        if prop.type=='INT':
                            vals[val-first]=prop.data
                        elif prop.type=='FLOAT':
                            vals[val-first]=round(prop.data, Vertex.ROUND)
                        else:
                            raise ExportError('Unsupported data type for "%s" in armature "%s"' % (valstr, object.name), [child])
            valstr="%s%s_loop" % (tmpref, suffix)
            for prop in object.getAllProperties():
                if prop.name.strip()==valstr:
                    if prop.type=='INT':
                        loop=prop.data
                    elif prop.type=='FLOAT':
                        loop=round(prop.data, Vertex.ROUND)
                    else:
                        raise ExportError('Unsupported data type for "%s" in armature "%s"' % (valstr, object.name), [child])

        return (dataref, vals, loop)


    #------------------------------------------------------------------------
    def __str__ (self):
        if self.dataref:
            return "%x %s r=%s a=%s t=%s v=%s m=%s p=(%s)" % (id(self), self.dataref, self.r, self.a, self.t, self.v, self.manipulator, self.anim)
        else:
            return "None"

    #------------------------------------------------------------------------
    def equals (self, b):
        if self is b:
            return True
        if not self.dataref:	# null
            return not b.dataref
        if (self.dataref!=b.dataref or
            len(self.r)!=len(b.r) or
            len(self.a)!=len(b.a) or
            len(self.t)!=len(b.t) or
            self.v!=b.v or
            not self.anim.equals(b.anim)):
            return False
        if self.showhide!=b.showhide:
            return False
        for i in range(len(self.r)):
            if not self.r[i].equals(b.r[i]):
                return False
        for i in range(len(self.t)):
            if not self.t[i].equals(b.t[i]):
                return False
        for i in range(len(self.a)):
            if abs(self.a[i]-b.a[i])>Vertex.LIMIT:
                return False
        return True

    #------------------------------------------------------------------------
    def ins(self):
        t=''
        anim=self
        while not anim.equals(Anim(self, None)):
            t=t+"\t"
            anim=anim.anim
        return t


#------------------------------------------------------------------------
def getcustomdataref(object, child, thing, names):
    dataref=None
    props=object.getAllProperties()
    for tmpref in names:
        for prop in props:
            if prop.name.strip()==tmpref:
                # custom dataref
                if prop.type=='STRING':
                    path=prop.data.strip()
                    if path and path[-1]!='/': path=path+'/'
                    dataref=path+names[-1]
                else:
                    raise ExportError('Unsupported data type for full name of custom dataref "%s" in armature "%s"' % (names[0], object.name), [child])
                break
    if not dataref:
        if names[0] in datarefs:
            if object==child:	# not animation
                raise ExportError('Dataref %s is ambiguous. Add a new string property named %s with the path name of the dataref that you want to use' % (names[0], names[0]), [object])
            else:		# animation
                raise ExportError('Dataref %s is ambiguous. Specify the full name in the X-Plane Animation dialog' % names[0], [child])
        else:
            raise ExportError('Unrecognised dataref "%s" for %s "%s"' % (names[0], thing, object.name), [child])
    return dataref


#------------------------------------------------------------------------
if Window.EditMode(): Window.EditMode(0)
try:
    obj=None
    scene = Blender.Scene.GetCurrent()

    baseFileName=Blender.Get('filename')
    l = baseFileName.lower().rfind('.blend')
    if l==-1: raise ExportError('Save this .blend file first')
    baseFileName=baseFileName[:l]
    (datarefs,foo)=getDatarefs()
    obj=OBJexport8(baseFileName+'.obj')
    obj.export(scene)
except ExportError, e:
    for o in scene.objects: o.select(0)
    if e.objs:
        layers=[]
        if isinstance(e.objs, tuple):
            (o,mesh,faces)=e.objs
            o.select(1)
            layers=o.layers
            for f in mesh.faces: f.sel=0
            if faces:
                for f in faces: f.sel=1
                for i in range(len(mesh.faces)):
                    if mesh.faces[i]==faces[0]:
                        mesh.activeFace=i
                        break
        else:
            for o in e.objs:
                o.select(1)
                for layer in o.layers:
                    if (layer<=3 or not o.Layers&7) and not layer in layers:
                        layers.append(layer)
        Window.ViewLayers(layers)
        Window.RedrawAll()
    if e.msg:
        Window.WaitCursor(0)
        Window.DrawProgressBar(0, 'ERROR')
        print "ERROR:\t%s.\n" % e.msg
        Draw.PupMenu("ERROR%%t|%s" % e.msg)
        Window.DrawProgressBar(1, 'ERROR')
    if obj and obj.file: obj.file.close()
except IOError, e:
    Window.WaitCursor(0)
    Window.DrawProgressBar(0, 'ERROR')
    print "ERROR:\t%s\n" % e.strerror
    Draw.PupMenu("ERROR%%t|%s" % e.strerror)
    Window.DrawProgressBar(1, 'ERROR')
    if obj and obj.file: obj.file.close()
