#!BPY
"""
Name: 'X-Plane'
Blender: 236
Group: 'Help'
Tooltip: 'XPlane2Blender manual'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script opens the default web browser at the XPlane2Blender manual.
"""

import Blender, webbrowser, types

for location in ['uscriptsdir', 'scriptsdir']:
    path=Blender.Get(location)
    if not path:
        continue
    filename=Blender.sys.join(path, 'XPlane2Blender.html')
    try:
        file=open(filename, 'rb')
        file.close()
        if type(filename)==types.UnicodeType:
            filename=filename.encode('utf-8')
    except IOError:
        continue
    else:
        webbrowser.open("file:%s" % filename)
        break
