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

bl_info = {
    "name": "Sequence Bakery",
    "description": "Extended version of Animated Render Baker, Ted fix",
    "author": "Christian Brinkmann (p2or), Janne Karhu (jahka)",
    "version": (0, 2),
    "blender": (2, 80, 0),
    "location": "",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Render"
}

'''
This Addon is basically an extended Version of -Animated Render Baker-
by Janne Karhu (jahka). The Addon allows to bake a series of frames as
well as overriding the filepath of a certain Image Texture Node on the
fly, which can be used to import and bake multiple images of a folder.

Workflow instructions (Cycles):

1. Prepare the object so that it's ready for a normal single frame baking:
   -> https://docs.blender.org/manual/en/dev/render/cycles/baking.html or
   -> https://blender.stackexchange.com/a/13509/3710

2. [Optional] Select the object, open up a Node Editor window, select the
   the Image Texture node of the corresponding material, open up the tool
   shelf (N), go to the misc area, enable "Override Image Path", select any
   Texture node to override, select a folder of images, press "Find Images"
   -> This will override the path of the selected image texture with all
   images of the selected folder per frame)

3. Create a new image in the UV/image editor (acts like a placeholder)

4. Save the image you just created with a "template name", i.e. "bake.jpg"
   -> This filename and path will be used as a template for the animated
      bake results, i.e. "bake0001.jpg", "bake0002.jpg" etc.
   -> If "Override Image Path" is enabled, the filename will be assembled
      by the orginal filename and the frame number, i.e: "image_frame-0001.jpg"

5. Create a new Image Texture node and assign the newly created image,
   Make sure that the node is selected, go to Properties > Render settings >
   Bake, set the desired frame range and press Animated Bake

Note: You can follow the progress in the console (Window > System Console)

'''

import bpy
import os
import shutil
from bpy.app.handlers import persistent

# ------------------------------------------------------
# Settings
# ------------------------------------------------------

image_list = []

class SequenceBakerySettings(bpy.types.PropertyGroup):

    image_folder : bpy.props.StringProperty(
        name="",
        description="Path to Directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

    texture_node : bpy.props.StringProperty(
        name = "Image Texture Node",
        description = "Select any Texture Node",
        options={'SKIP_SAVE'})

    current_image_path : bpy.props.StringProperty(
        name = "Current Image Path",
        description = "Current Image Path")

    override : bpy.props.BoolProperty(
        name="Override",
        description="Enable or Disable Overriding the Image Path",
        default = False,
        options={'SKIP_SAVE'})

    bake_start : bpy.props.IntProperty(
        name="Start",
        description="Start frame of the animated bake",
        default=1)

    bake_end : bpy.props.IntProperty(
        name="End",
        description="End frame of the animated bake",
        default=250)

# ------------------------------------------------------
#   Operators
# ------------------------------------------------------

class SB_OT_printFoundImagesToConsole(bpy.types.Operator):
    """Print valid images to the console"""
    bl_idname = "node.sb_print_images_to_console"
    bl_label = "Print Images to Console"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'

    def execute(self, context):
        if image_list:
            image_names = [os.path.basename(i) for i in image_list]
            for i in image_names: print (i)
            self.report({'INFO'}, 'Names of Images printed to Console')
        else:
            self.report({'INFO'}, 'No images')
        return {'FINISHED'}

class SB_OT_refreshImageList(bpy.types.Operator):
    """Refresh Images"""
    bl_idname = "node.sb_refresh_image_list"
    bl_label = "Reload Images"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        #context.active_node.type == "TEX_IMAGE"
        return space.type == 'NODE_EDITOR'

    def execute(self, context):
        del image_list[:]
        bpy.ops.node.sb_find_images()
        context.scene.frame_set(context.scene.frame_start)
        self.report({'INFO'}, 'List of Images refreshed')
        return {'FINISHED'}

class SB_OT_findImagesInFolder(bpy.types.Operator):
    """Find Images in specified Folder"""
    bl_idname = "node.sb_find_images"
    bl_label = "Find Images"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        space = context.space_data
        return space.type == 'NODE_EDITOR'

    def execute(self, context):
        extensions = ('exr', 'tiff', 'jpeg', 'jpg', 'pic', 'png')
        if not image_list:
            path = context.scene.seq_bakery.image_folder
            img_folder = os.path.realpath(bpy.path.abspath(path))
            if os.path.isdir(img_folder):
                for f in os.listdir(img_folder):
                    if f.endswith(tuple(extensions)):
                        image_list.append(os.path.join(img_folder,f))
            if image_list:
                context.scene.frame_set(context.scene.frame_start)
                message = 'Found ' + str(len(image_list)) + " images"
                #bpy.ops.node.sb_print_images_to_console()
            else:
                message = 'No valid images found in Folder'
            self.report({'INFO'}, message)
        return {'FINISHED'}

# Modification of 'Animated Render Baker' operator by Janne Karhu (jahka)
# https://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/Animated_Render_Baker
class SB_OT_animatedRenderBake(bpy.types.Operator):
    bl_label = "Animated Render Bake"
    bl_description= "Bake animated image textures of selected objects"
    bl_idname = "object.sb_anim_bake_image"
    bl_register = True

    def framefile(self, context, filepath, frame):
        """
        Set frame number to file name image.png -> image0013.png
        """
        if context.scene.seq_bakery.override:
            bake_folder = os.path.dirname(filepath)
            filename = os.path.basename(context.scene.seq_bakery.current_image_path)
            fn, ext = os.path.splitext(filename)
            new_filename = "%s_frame-%04d-bake%s" % (fn, frame, ext)
            return os.path.join(bake_folder, new_filename)
        else:
            fn, ext = os.path.splitext(filepath)
            return "%s%04d%s" % (fn, frame, ext)

    def invoke(self, context, event):
        is_cycles = (context.scene.render.engine == 'CYCLES')
        scene = context.scene

        start = scene.seq_bakery.bake_start
        end = scene.seq_bakery.bake_end

        # Check for errors before starting
        if start >= end:
            self.report({'ERROR'}, "Start frame must be smaller than end frame")
            return {'CANCELLED'}

        selected = context.selected_objects

        # if len(selected) > 1:
        #    self.report({'ERROR'}, "Select only one object for animated baking")
         #   return {'CANCELLED'}

        if context.active_object.type != 'MESH':
            self.report({'ERROR'}, "The baked object must be a mesh object")
            return {'CANCELLED'}

        if context.active_object.mode == 'EDIT':
            self.report({'ERROR'}, "Can't bake in edit-mode")
            return {'CANCELLED'}

        img = None

        # find the image that's used for rendering
        # TODO: support multiple images per bake
        if is_cycles:
            # XXX This tries to mimic nodeGetActiveTexture(), but we have no access to 'texture_active' state from RNA...
            #     IMHO, this should be a func in RNA nodetree struct anyway?
            inactive = None
            selected = None
            for mat_slot in context.active_object.material_slots:
                mat = mat_slot.material
                if not mat or not mat.node_tree:
                    continue
                trees = [mat.node_tree]
                while trees and not img:
                    tree = trees.pop()
                    node = tree.nodes.active
                    if node.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'}:
                        img = node.image
                        break
                    for node in tree.nodes:
                        if node.type in {'TEX_IMAGE', 'TEX_ENVIRONMENT'} and node.image:
                            if node.select:
                                if not selected:
                                    selected = node
                            else:
                                if not inactive:
                                    inactive = node
                        elif node.type == 'GROUP':
                            trees.add(node.node_tree)
                if img:
                    break
            if not img:
                if selected:
                    img = selected.image
                elif inactive:
                    img = inactive.image
        else:
            for uvtex in context.active_object.data.uv_textures:
                if uvtex.active_render == True:
                    for uvdata in uvtex.data:
                        if uvdata.image is not None:
                            img = uvdata.image
                            break

        if img is None:
            self.report({'ERROR'}, "No valid image found to bake to")
            return {'CANCELLED'}

        if img.is_dirty:
            self.report({'ERROR'}, "Save the image that's used for baking before use")
            return {'CANCELLED'}

        if img.packed_file is not None:
            self.report({'ERROR'}, "Can't animation-bake packed file")
            return {'CANCELLED'}

        # make sure we have an absolute path so that copying works for sure
        img_filepath_abs = bpy.path.abspath(img.filepath, library=img.library)

        print("Animated baking for frames (%d - %d)" % (start, end))

        for cfra in range(start, end + 1):
            print("Baking frame %d" % cfra)

            # update scene to new frame and bake to template image
            scene.frame_set(cfra)
            if is_cycles:
                ret = bpy.ops.object.bake(type=scene.cycles.bake_type)
            else:
                ret = bpy.ops.object.bake_image()
            if 'CANCELLED' in ret:
                return {'CANCELLED'}

            # Currently the api doesn't allow img.save_as()
            # so just save the template image as usual for
            # every frame and copy to a file with frame specific filename
            img.save()
            img_filepath_new = self.framefile(context, img_filepath_abs, cfra)
            shutil.copyfile(img_filepath_abs, img_filepath_new)
            print("Saved %r" % img_filepath_new)

        print("Baking done!")

        return{'FINISHED'}

# ------------------------------------------------------
#   UI
# ------------------------------------------------------

class SB_PT_sequenceBakeryPanel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Override Image Path"
    bl_region_type = "UI"
    bl_category = "Extras"


    @classmethod
    def poll(cls, context):
        space = context.space_data
        node_active = context.active_node
        #hasattr(node_active, 'image')
        image = getattr(node_active, 'image', None)
        return image and space.type == 'NODE_EDITOR'

    def draw_header(self, context):
        scn = context.scene
        node_active = context.active_node
        if node_active.image and node_active.type == "TEX_IMAGE":
            self.layout.prop(scn.seq_bakery, "override", text="")

    def draw(self, context):
        scn = context.scene
        space = context.space_data
        node_active = context.active_node
        if node_active.image and node_active.type == "TEX_IMAGE":
            data = bpy.data.materials[space.id.name].node_tree
            img = os.path.basename(context.active_node.image.filepath)
            layout = self.layout

            row = layout.row()
            row.label(text="Image Texture Node: ")
            row = layout.row()
            row.prop_search(scn.seq_bakery, "texture_node", data, "nodes", text="")
            #layout.separator()
            row = layout.row()
            row.label(text="Image Folder: ")
            row = layout.row()
            col = row.column(align=True) #col.operator()
            rowsub = col.row(align=True)
            rowsub.prop(scn.seq_bakery, "image_folder")
            rowsub = col.row(align=True)
            rowsub.operator("node.sb_find_images", icon="VIEWZOOM")#rowsub = col.row(align=True)
            rowsub.operator("node.sb_refresh_image_list", icon="FILE_REFRESH", text="")
            rowsub.operator("node.sb_print_images_to_console", icon="CONSOLE", text="")
            layout.separator()

            row = layout.row()
            row.label(text='Image [Frame {num:03d}]:'.format(num=scn.frame_current))
            row = layout.row()
            row.label(text=img)
            row.separator()

# ------------------------------------------------------
#   Helper
# ------------------------------------------------------

def draw_animation_baker(self, context):

    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False  # No animation.

    scene = context.scene

    layout.separator()
    layout.operator("object.sb_anim_bake_image", text="Animated Bake", icon='RENDER_ANIMATION')

    layout.row()
    col = layout.column(align=True)
    #row.operator("object.sb_anim_bake_image", text="Animated Bake", icon="RENDER_ANIMATION")
    col.prop(scene.seq_bakery, "bake_start", text="Bake Start")
    col.prop(scene.seq_bakery, "bake_end", text="Bake End")



@persistent
def texture_node_handler(scene):
    if scene.seq_bakery.override:
        obj = bpy.context.active_object
        mat_name = bpy.context.active_object.active_material.name
        mat = bpy.data.materials[mat_name]
        nodes = mat.node_tree.nodes
        image_texture_node = nodes.get(scene.seq_bakery.texture_node)
        frame_offset = abs(0-scene.frame_start)
        image_list_index = scene.frame_current - frame_offset

        try:
            current_image = image_list[image_list_index]
            image_texture_node.image.filepath = current_image
            scene.seq_bakery.current_image_path = current_image
        except:
            pass

'''
def draw_func(self, context):
    row = self.layout.row()
    row.operator("node.sb_refresh_image_list", icon="FILE_REFRESH")
'''

# ------------------------------------------------------
#   Register
# ------------------------------------------------------

classes = (
    SequenceBakerySettings,
    SB_OT_printFoundImagesToConsole,
    SB_OT_refreshImageList,
    SB_OT_findImagesInFolder,
    SB_OT_animatedRenderBake,
    SB_PT_sequenceBakeryPanel
)


def register():

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.seq_bakery = bpy.props.PointerProperty(type=SequenceBakerySettings)
    bpy.types.CYCLES_RENDER_PT_bake.append(draw_animation_baker)

    bpy.app.handlers.frame_change_pre.append(texture_node_handler)


def unregister():

    bpy.app.handlers.frame_change_pre.remove(texture_node_handler)
    bpy.types.CYCLES_RENDER_PT_bake.remove(draw_animation_baker)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.seq_bakery

if __name__ == "__main__":
    register()
