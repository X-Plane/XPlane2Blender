#!BPY
""" Registration info for Blender menus:
Name: 'Merge _paint and _paint2'
Blender: 243
Group: 'Image'
Tooltip: 'Merge X-Plane plane_paint and plane_paint2 bitmaps'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script fixes up an imported plane's texture assignments to use
a single bitmap file.

Usage:<br>
  * Create a new texture bitmap with plane_paint on the left
    and plane paint2 on the right.<br>
  * Save the new texture bitmap as a PNG with the same name
    as the blend file.<br>
  * Run this script from the UVs menu in the UV/Image Editor<br>
    window.<br>
"""

#------------------------------------------------------------------------
# UV Resize for blender 2.43 or above
#
# Copyright (c) 2006,2007 Jonathan Harris
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
# 2006-04-07 v2.20
#  - New file
#
# 2007-10-16 v2.45
#  - Fix for Blender 2.45
#
# 2008-04-08 v3.09
#  - Fix for break in version 3.03
#

import Blender
from Blender import Draw, Image, Scene, NMesh, Window
from os.path import splitext

(newfile,ext)=splitext(Blender.Get('filename'))
for ext in ['.dds', '.DDS', '.png', '.PNG', '.bmp', '.BMP']:
    try:
        tex=Image.Load(newfile+ext)
        dim=tex.getSize()

        for ob in Scene.GetCurrent().objects:
            if ob.getType() == "Mesh" and ob.getData().hasFaceUV():
                mesh = ob.getData()
                for face in mesh.faces:
                    if face.mode & NMesh.FaceModes.TEX and face.image:
                        oldfile=face.image.filename.lower()
                        if '_paint.' in oldfile:
                            for i in range(len(face.uv)):
                                (s,t)=face.uv[i]
                                face.uv[i]=(s/2, t)
                                face.image=tex
                        elif '_paint2.' in oldfile:
                            for i in range(len(face.uv)):
                                (s,t)=face.uv[i]
                                face.uv[i]=(0.5+s/2, t)
                                face.image=tex
                ob.setName(ob.name.replace('*',''))
                mesh.name=mesh.name.replace('*','')
                mesh.update()

        Window.RedrawAll()
        break

    except (RuntimeError, IOError):
        pass

else:
    msg='Can\'t load texture file %s.png or .bmp' % newfile
    print "ERROR:\t%s\n" % msg
    Draw.PupMenu("ERROR: %s" % msg)

