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

bl_addon_info = {
    'name': 'Import/Export: XPlane',
    'author': 'Ondrej Brinkel',
    'version': (3,20),
    'blender': (2, 5, 4),
    'location': 'File > Import/Export > XPlane ',
    'description': 'Import and Export XPlane objects/planes (.obj,.aif format)',
    'warning': '', # used for warning icon and text in addons panel
    'category': 'Import-Export'}

import bpy
from io_xplane2blender import xplane_ui
from io_xplane2blender import xplane_props
from io_xplane2blender import xplane_export
from io_xplane2blender.xplane_config import *


# Add to a menu
def menu_func(self, context):
    self.layout.operator(xplane_export.ExportXPlane9.bl_idname, text="XPlane Object (.obj)")

def register():    
    xplane_props.addXPlaneRNA()
    xplane_ui.addXPlaneUI()
    bpy.types.INFO_MT_file_export.append(menu_func)

def unregister():
    xplane_ui.removeXPlaneUI()
    xplane_props.removeXPlaneRNA()
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()