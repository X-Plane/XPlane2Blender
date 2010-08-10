#!BPY
""" Registration info for Blender menus:
Name: 'X-Plane panel regions...'
Blender: 243
Group: 'Image'
Tooltip: 'Manage X-Plane cockpit panel regions'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"

#------------------------------------------------------------------------
# XPlanePanelRegions for blender 2.43 or above
#
# Copyright (c) 2007 Jonathan Harris
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
# 2007-12-21 v3.05
#  - New file.
#

from Blender import Draw, Image, Window
from math import log

from XPlaneUtils import PanelRegionHandler

image=Image.GetCurrent()	# may be None
h=PanelRegionHandler()

opts=[]
if not image:
    pass
elif h.isRegion(image):
    opts.append('Delete this region%x1')
    opts.append('Reload all regions%x3')
elif h.isPanel(image):
    if h.countRegions()<PanelRegionHandler.REGIONCOUNT:
        opts.append('Create new region...%x2')
    else:
        opts.append('Can\'t create new region - already using maximum of %d regions%%x0' % PanelRegionHandler.REGIONCOUNT)
    opts.append('Reload all regions%x3')
elif image and 'panel.' in image.name.lower() and '.region' not in image.name.lower():
    opts.append('Create new region...%x2')

if not opts:
    r=Draw.PupMenu('This is not a Panel Texture or Region%t')
else:
    r=Draw.PupMenu('X-Plane panel regions%t|'+('|'.join(opts)))
    if r==1:
        h.delRegion(image)
        h.panelimage().makeCurrent()
    elif r==2:
        maxx=2**int(log(image.size[0],2))
        maxy=2**int(log(image.size[1],2))
        xoff=Draw.Create(0)
        yoff=Draw.Create(0)
        width=Draw.Create(min(maxx,1024))
        height=Draw.Create(min(maxy,1024))
        block=[]
        block.append(('Left:',   xoff,   0, image.size[0]))
        block.append(('Bottom:', yoff,   0, image.size[1]))
        block.append(('Width:',  width,  0, maxx))
        block.append(('Height:', height, 0, maxy))
        
        while Draw.PupBlock('Create new region', block):
            if not width.val or not height.val or 2**int(log(width.val,2))!=width.val or 2**int(log(height.val,2))!=height.val:
                if isinstance(block[-1], tuple): block.extend(['',''])
                block[-2]='Width & Height must'
                block[-1]='be powers of 2'
            elif xoff.val+width.val>image.size[0]:
                if isinstance(block[-1], tuple): block.extend(['',''])
                block[-2]='Left + Width must'
                block[-1]='be less than %d' % image.size[0]
            elif yoff.val+height.val>image.size[1]:
                if isinstance(block[-1], tuple): block.extend(['',''])
                block[-2]='Bottom + Height must'
                block[-1]='be less than %d' % image.size[1]
            else:
                Window.WaitCursor(1)
                if not h.isPanel(image):
                    h=h.New(image)
                h.addRegion(xoff.val, yoff.val, width.val, height.val).makeCurrent()
                Window.WaitCursor(0)
                break
    elif r==3:
        h.regenerate()
