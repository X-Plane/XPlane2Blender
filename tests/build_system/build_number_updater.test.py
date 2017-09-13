import bpy
import os
import sys
from shutil import *
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config, xplane_constants

from io_xplane2blender.xplane_helpers import VerStruct

__dirname__ = os.path.dirname(__file__)

class TestBuildNumberUpdater(XPlaneBuildNumberTestCase):
    @classmethod
    def run_update_cycle(self,filename,to_parse):
        original_path = os.path.normpath(os.path.join(__dirname__,"originals", filename))
        copy_path = os.path.normpath(os.path.join(__dirname__,"..","tmp", filename))
        if os.path.isfile(copy_path) is False:
            shutil.copyfile(original_path,copy_path)
        bpy.ops.wm.open_mainfile(filepath=copy_path)

        def try_asserts(addon_version):
            self.assertTrue(bpy.context.scene['xplane2blender_version'] == xplane_constants.DEPRECATED_XP2B_VER,
                             "scene['xplane2blender_version'] was not deprecated on load")

            self.assertTrue(VerStruct.cmp(self.current,self.xplane2blender_ver,True,True) == 0, 'xplane2blender_version has been mutated after loading')

            self.assertTrue(len(self.history) == 2,
                            'xplane2blender_ver_history is %d long, not 2' % len(self.history))
            self.assertTrue(VerStruct.cmp(self.history[0], VerStruct.parse_version(to_parse),include_data_model_version=True) == 0,
                            'First entry in history %s is wrong or not the legacy string' % self.history[0])
            self.assertTrue(VerStruct.cmp(self.history[1], self.current,include_data_model_version=True) == 0,
                            'Second entry in history %s is wrong or not the legacy string' % self.history[1])

        bpy.ops.wm.save_mainfile(filepath=copy_path, check_existing=False)

    def test_update_from_3_2_14(self):
        addon_version = ('3','20','14')
        filename="v" + "_".join(addon_version) + ".blend"
        to_parse=".".join(addon_version)
        self.run_update_cycle(filename,to_parse)
        self.run_update_cycle(filename,to_parse)
            
    def test_update_from_3_3_13(self):
        addon_version = ('3','3','13')
        filename="v" + "_".join(addon_version) + ".blend"
        to_parse=".".join(addon_version)
        self.run_update_cycle(filename,to_parse)
        self.run_update_cycle(filename,to_parse)

    def test_update_from_3_4_0(self):
        filename="v3_4_0-beta_4.blend"
        to_parse="3.4.0-beta.4"
        self.run_update_cycle(filename,to_parse)
        self.run_update_cycle(filename,to_parse)
    
    def test_update_from_new_file(self):
       bpy.ops.wm.read_homefile() 
       blend_path = os.path.join(__dirname__,"..","tmp","build_number_new_save_test.blend")
       bpy.ops.wm.save_mainfile(filepath=blend_path, check_existing=False)
       self.run_update_cycle(blend_path,str(self.current))

runTestCases([TestBuildNumberUpdater])