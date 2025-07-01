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
import bpy

# Contains informations for Blender to recognize and categorize the addon.
bl_info = {
    "name": "XPlane2Blender Export for X-Plane OBJs",
    "description": "Export X-Plane objects/planes (.obj format)",
    "author": "Ted Greene, Ben Supnik, Amy Parent, Maya F. Eroglu",
    "version": (4, 4, 0),
    "blender": (2, 80, 0),
    "location": "File > Import/Export > X-Plane",
    "warning": "",
    "wiki_url": "https://github.com/X-Plane/XPlane2Blender/wiki",
    "tracker_url": "https://github.com/X-Plane/XPlane2Blender/issues",
    "category": "Import-Export",
}

if "" not in locals():

    from . import xplane_ui
    from . import xplane_props
    from . import xplane_export
    from . import xplane_ops
    from . import xplane_ops_dev
    from . import xplane_config
    from . import xplane_updater
    from .xplane_utils import xplane_lights_txt_parser
    from .xplane_utils import xplane_wiper_gradient
else:
    import importlib
    xplane_ui      = importlib.reload(xplane_ui)
    xplane_props   = importlib.reload(xplane_props)
    xplane_export  = importlib.reload(xplane_export)
    xplane_ops     = importlib.reload(xplane_ops)
    xplane_ops_dev = importlib.reload(xplane_ops_dev)
    xplane_config  = importlib.reload(xplane_config)
    xplane_updater = importlib.reload(xplane_updater)
    xplane_lights_txt_parser = importlib.reload(xplane_lights_txt_parser)
    xplane_wiper_gradient = importlib.reload(xplane_wiper_gradient)


# Function: menu_func
# Adds the export option to the menu.
#
# Parameters:
#   self - Instance to something
#   context - The Blender context object
def menu_func(self, context):
    self.layout.operator(
        xplane_export.EXPORT_OT_ExportXPlane.bl_idname, text="X-Plane Object (.obj)"
    )


# Function: register
# Registers the addon with all its classes and the menu function.
def register():
    xplane_export.register()
    xplane_props.register()
    xplane_ops.register()
    xplane_ops_dev.register()
    xplane_ui.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


# Function: unregister
# Unregisters the addon and all its classes and removes the entry from the menu.
def unregister():
    xplane_export.unregister()
    xplane_ui.unregister()
    xplane_ops.unregister()
    xplane_ops_dev.unregister()
    xplane_props.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
