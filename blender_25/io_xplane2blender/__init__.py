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
	'author': '',
	'version': '3.11beta',
	'blender': (2, 5, 3),
	'location': 'File > Import/Export > XPlane ',
	'description': 'Import and Export Xplane objects/planes (.obj,.aif format)',
	'warning': '', # used for warning icon and text in addons panel
	'category': 'Import/Export'}

import bpy

def register():
	from io_xplane2blender import xplane_ui
	bpy.types.register(xplane_ui.OBJECT_PT_xplane)

def unregister():
	from io_xplane2blender import xplane_ui
	bpy.types.unregister(xplane_ui.OBJECT_PT_xplane)

if __name__ == "__main__":
    register()