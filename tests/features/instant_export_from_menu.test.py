import os
import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.tests import *

#This folder is going to be messy with creating folders
#We use fakefilename to imitate what a user will go through
#in the file picking box
EXPORT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','tmp'))

class TestInstantExportFromMenu(XPlaneTestCase):
    def assert_file_exists(self,layer_num:int,relpath:str):
        with TemporarilyMakeRootExportable(f"Layer {layer_num + 1}") as coll:
            try:
                bpy.ops.export.xplane_obj(filepath=EXPORT_FOLDER)

                dirname = os.path.dirname(bpy.context.blend_data.filepath)
                path = os.path.abspath(os.path.join(dirname,relpath))
                self.assertTrue(os.path.isfile(path))
            except KeyError:
                raise

    def test_ensure_append(self):
        self.assert_file_exists(0, os.path.join(EXPORT_FOLDER, "ensure_append.obj"))

    def test_ensure_no_append(self):
        self.assert_file_exists(1, os.path.join(EXPORT_FOLDER, "ensure_no_double_append.obj"))

    def test_ensure_no_folder_named_filename(self):
        bpy.data.collections["Layer 3"].xplane.is_exportable_collection = True
        bpy.ops.export.xplane_obj()
        bpy.data.collections["Layer 3"].xplane.is_exportable_collection = False

        self.assertFalse(os.path.isdir(os.path.join(EXPORT_FOLDER,"ensure","no","folder","named","filename")))

    def test_ensure_no_abs_path_filename(self):
        #Test Windows and Unix differently
        if os.name == 'nt':
            with TemporarilyMakeRootExportable("Layer 4") as coll:
                bpy.ops.export.xplane_obj()
        else:
            with TemporarilyMakeRootExportable("Layer 5") as coll:
                bpy.ops.export.xplane_obj()

        self.assertLoggerErrors(1)

    def test_ensure_paths_are_normalized_filename(self):
        self.assert_file_exists(5, os.path.join(EXPORT_FOLDER,"ensure","paths","are","normalized","filename.obj"))

    def test_ensure_blender_paths_resolve_filename(self):
        #Check if file exists
        self.assert_file_exists(6, os.path.join(EXPORT_FOLDER,"ensure","blender","paths","resolve","filename.obj"))


    def test_ensure_lazy_paths_resolve_filename(self):
        #Check if file exists
        self.assert_file_exists(7, os.path.join(EXPORT_FOLDER,"ensure","lazy","paths","resolve","filename.obj"))

    def test_ensure_dot_paths_are_created_filename(self):
        #Check if file exists
        self.assert_file_exists(8, os.path.join(EXPORT_FOLDER,"ensure","dot", "paths","resolve","filename.obj"))

runTestCases([TestInstantExportFromMenu])
