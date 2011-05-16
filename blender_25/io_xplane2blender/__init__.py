# File: __init__.py
# Needed for python to register this folder as a module and for blender to register/unregister the addon.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Variable: bl_info
# Contains informations for Blender to recognize and categorize the addon.
bl_info = {
    'name': 'Import/Export: XPlane',
    'author': 'Ondrej Brinkel',
    'version': (3,20),
    'blender': (2, 5, 7),
    'api': 36273,
    'location': 'File > Import/Export > XPlane ',
    'description': 'Import and Export XPlane objects/planes (.obj,.aif format)',
    'warning': 'beta', # used for warning icon and text in addons panel
    'category': 'Import-Export'}

if "bpy" in locals():
    import imp
    imp.reload(xplane_ui)
    imp.reload(xplane_props)
    imp.reload(xplane_export)
    imp.reload(xplane_ops)
    imp.reload(xplane_config)
else:
    import bpy
    from io_xplane2blender import xplane_ui
    from io_xplane2blender import xplane_props
    from io_xplane2blender import xplane_export
    from io_xplane2blender import xplane_ops
    from io_xplane2blender.xplane_config import *


# Function: menu_func
# Adds the export option to the menu.
#
# Parameters:
#   self - Instance to something
#   context - The Blender context object
def menu_func(self, context):
    self.layout.operator(xplane_export.ExportXPlane9.bl_idname, text="XPlane Object (.obj)")

# Function: register
# Registers the addon with all its classes and the menu function.
def register():    
    xplane_props.addXPlaneRNA()
    xplane_ops.addXPlaneOps()
    xplane_ui.addXPlaneUI()
    bpy.utils.register_class(xplane_export.ExportXPlane9)
    bpy.types.INFO_MT_file_export.append(menu_func)
    bpy.utils.register_module(__name__)

# Function: unregister
# Unregisters the addon and all its classes and removes the entry from the menu.
def unregister():
    xplane_ui.removeXPlaneUI()
    xplane_ops.removeXPlaneOps()
    xplane_props.removeXPlaneRNA()
    bpy.utils.unregister_class(xplane_export.ExportXPlane9)
    bpy.types.INFO_MT_file_export.remove(menu_func)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
