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
    "name": "Export: X-Plane (.obj)",
    "author": "Ondrej Brinkel, Ted Greene",
    "version": (3, 5, 0),
    "blender": (2, 7, 8),
    "location": "File > Import/Export > X-Plane",
    "description": "Import and Export X-Plane objects/planes (.obj format)",
    "warning": "",
    "wiki_url": "https://github.com/der-On/XPlane2Blender/wiki",
    "tracker_url": "https://github.com/der-On/XPlane2Blender/issues",
    "category": "Import-Export"
}

if "bpy" in locals():
    import imp
    imp.reload(xplane_ui)
    imp.reload(xplane_props)
    imp.reload(xplane_export)
    imp.reload(xplane_ops)
    imp.reload(xplane_config)
    imp.reload(xplane_updater)
else:
    import bpy
    from . import xplane_ui
    from . import xplane_props
    from . import xplane_export
    from . import xplane_ops
    from . import xplane_config
    from . import xplane_updater


# Function: menu_func
# Adds the export option to the menu.
#
# Parameters:
#   self - Instance to something
#   context - The Blender context object
def menu_func(self, context):
    self.layout.operator(xplane_export.ExportXPlane.bl_idname, text = "X-Plane Object (.obj)")

# Function: register
# Registers the addon with all its classes and the menu function.
def register():
    xplane_props.addXPlaneRNA()
    xplane_ops.addXPlaneOps()
    xplane_ui.addXPlaneUI()
    bpy.utils.register_class(xplane_export.ExportXPlane)
    bpy.types.INFO_MT_file_export.append(menu_func)
    bpy.utils.register_module(__name__)

# Function: unregister
# Unregisters the addon and all its classes and removes the entry from the menu.
def unregister():
    xplane_ui.removeXPlaneUI()
    xplane_ops.removeXPlaneOps()
    xplane_props.removeXPlaneRNA()
    bpy.utils.unregister_class(xplane_export.ExportXPlane)
    bpy.types.INFO_MT_file_export.remove(menu_func)
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
