import bpy
import os
import sys
from shutil import *
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.xplane_helpers import VerStruct
from bpy.app import build_type

__dirname__ = os.path.dirname(__file__)

class TestBuildNumberVerStruct(XPlaneBuildNumberTestCase):
    def test_constructor_defaults_correct(self):
        ver_s = VerStruct()

        self.assertTrue(ver_s.addon_version      == (0,0,0), "addon_version %s does not match it's default %s" % (ver_s.addon_version, (0,0,0)))
        self.assertTrue(ver_s.build_type         == xplane_constants.BUILD_TYPE_DEV, "build_type %s does not match it's default %s" % (ver_s.build_type, xplane_constants.BUILD_TYPE_DEV))
        self.assertTrue(ver_s.build_type_version == 0, "build_type_version %s does not match it's default %s" % (ver_s.build_type_version,0))
        self.assertTrue(ver_s.data_model_version == 0, "data_model_version %s does not match it's default %s" % (ver_s.data_model_version,0))
        self.assertTrue(ver_s.build_number       == xplane_constants.BUILD_NUMBER_NONE,"build_number %s does not match it's default %s" % (ver_s.build_number,xplane_constants.BUILD_NUMBER_NONE))

    def test_repr_str_are_same(self):
        ver_s = self.xplane2blender_ver.make_struct()
        
        self.assertTrue(repr(ver_s) == repr(self.current), "VerStuct and XPlane2BlenderVersion's repr implenentation are not the same: %s vs %s" % (repr(ver_s),repr(self.current)))
        self.assertTrue(str(ver_s) == str(self.current), "VerStuct and XPlane2BlenderVersion's str implenentation are not the same: %s vs %s" % (str(ver_s),str(self.current)))

    def test_repr_makes_struct_in_eval(self):
        ver_s = self.xplane2blender_ver.make_struct()
        
        try:
            VerStruct(*eval(repr(ver_s)))
        except:
            self.assertTrue(False,"repr of VerStruct was unable to turn back into a VerStruct: %s" % repr(ver_s))

    def test_xplane2blender_str(self):
        parsed_str = str(VerStruct.parse_version('3.4.0'))
        self.assertEqual("3.4.0-leg.0+0.NO_BUILD_NUMBR", parsed_str, "VerStruct.__str__ does not format string into proper form %s" % parsed_str)
 
    def test_invalid_ver_addition(self):
        orig_history_len = len(self.history)
        new_entry = VerStruct.add_to_version_history(VerStruct((-1,-1,-1),"INVALID",-1,-1,"INVALID"))
        self.assertTrue(new_entry is None, "Invalid entry was allowed into version history")
        self.assertTrue(orig_history_len == len(self.history), "History was not returned to original length after invalid addition")
        
    def test_valid_ver_addition(self):
        orig_history_len = len(self.history)
        new_entry = VerStruct.add_to_version_history(self.current)
        self.assertTrue(new_entry is not None, "Valid entry was not allowed into version history")
        self.assertTrue(orig_history_len != orig_history_len+1, "History length was not incremented by one after valid addition")

    def test_make_new_build_number(self):
        ver_s = self.xplane2blender_ver.make_struct()
        ver_s.build_number = VerStruct.make_new_build_number()
        self.assertTrue(ver_s.is_valid(), "VerStruct.get_build_number_datetime does not generate vaild build numbers")
        
    def test_parse_version(self):
        incorrect_versions_legacy = [
            "random_letters qwerasdfzxcv",
            "340",
            "03.4.0"
            "3.4.0.",
            "(3.4.0)",
            "3_20_20",
            ]
        
        for test_v in incorrect_versions_legacy:
            try:
                self.assertFalse(VerStruct.parse_version(test_v) != None, "VerStruct.parse_version allowed bad legacy style version %s through" % test_v)
            except Exception as e:
                pass
        
        incorrect_versions_modern = [
            "3.4.0.beta.1", #Bad separator
            "3.4.0-alpha.-1", #Int, but not > 0
            "3.4.0-rc", #Missing revision number
            "3.4.0-rc.1-1.20170906153430", #Bad separator
            "3.4.0-rc.1+1.YYYYMMDDHHMMSS", #Parsing the description, not the contents
            "3.4.0-rc.1+1.2017" #Build string is numbers, but not long enough
            ]
        
        for test_v in incorrect_versions_modern:
            try:
                self.assertFalse(VerStruct.parse_version(test_v) != None, "VerStruct.parse_version allowed bad modern style version %s through" % test_v)
            except Exception as e:
                pass
        
        correct_versions_legacy = [
            ("3.2.0", VerStruct(addon_version=(3,2,0), build_type=xplane_constants.BUILD_TYPE_LEGACY)),
            ("3.20.0",VerStruct(addon_version=(3,20,0), build_type=xplane_constants.BUILD_TYPE_LEGACY)), #Keep 20->2 in xplane_updater.py
            ("3.3.13",VerStruct(addon_version=(3,3,13),build_type=xplane_constants.BUILD_TYPE_LEGACY))
            ]
        
        for test_v, test_v_res in correct_versions_legacy:
            v_res = VerStruct.parse_version(test_v)
            self.assertTrue(v_res != None, "VerStruct.parse_version did not allow valid legacy style version %s through" % test_v)
            self.assertTrue(VerStruct.cmp(test_v_res,v_res,True,True) == 0, "Test string %s did not parse to expected data %s" % (test_v,str(v_res)))
            
        correct_versions_modern = [
            ("3.4.0-rc.5+1.20170914160830",VerStruct(addon_version=(3,4,0),build_type=xplane_constants.BUILD_TYPE_RC,  build_type_version=5,
                                                       data_model_version=1,build_number="20170914160830"))
            ]
             
        for test_v, test_v_res in correct_versions_modern:
            v_res = VerStruct.parse_version(test_v)
            self.assertTrue(v_res != None, "VerStruct.parse_version did not allow valid modern style version %s through" % test_v)
            self.assertTrue(VerStruct.cmp(test_v_res,v_res,True,True) == 0, "Test string %s did not parse to expected data %s" % (test_v,str(v_res)))
        
    def test_cmp(self):
        addon_versions = [(3,2,0),(4,3,1),(5,4,2)]
        build_numbers = ["20170915103830","20180915103830"]
        
        def test_variations(v1, v2, expected_result,include_data_model_version=True,include_build_number=True):
            if expected_result == -1 or expected_result == 0:
                actual_cmp_res = VerStruct.cmp(v1,v2,include_data_model_version,include_build_number)
            elif expected_result == 1:
                actual_cmp_res = VerStruct.cmp(v2,v1,include_data_model_version,include_build_number)
            else:
                raise Exception("expected_result parameter in test_variations must be -1,0,1")
            
            self.assertTrue(actual_cmp_res == expected_result, "Comparing %s and %s expected %d but got %d" % (str(v1),str(v2),expected_result,actual_cmp_res))

        #Test addon_version vs addon_version
        for i in range(len(addon_versions)-1):
            v1 = VerStruct(addon_versions[i]  ,xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[0])
            v2 = VerStruct(addon_versions[i+1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[0])
            test_variations(v1, v2, -1)
            test_variations(v1, v2, 1)

        #Test build_type precedence
        for i in range(len(xplane_constants.BUILD_TYPES)-1):
            v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPES[i]  ,1,1,build_numbers[0])
            v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPES[i+1],1,1,build_numbers[0])
            test_variations(v1, v2, -1)
            test_variations(v1, v2, 1)
         
        #Test build_type_version
        v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[0])
        v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,2,1,build_numbers[0])
        test_variations(v1, v2, -1,False,False)
        test_variations(v1, v2, 1, False,False)

        #Test data model
        v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[0])
        v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,2,build_numbers[0])
        test_variations(v1, v2, -1,True,False)
        test_variations(v1, v2, 1,True,False)

        #Test build number
        v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[0])
        v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[1])
        test_variations(v1, v2, -1,False,True)
        test_variations(v1, v2, 1,False,True)

        #Test data model build number precedence (data model chosen first)
        v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[1])
        v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,2,build_numbers[0])
        test_variations(v1, v2, -1)
        
        #Test equality  
        v1 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[1])
        v2 = VerStruct(addon_versions[1],xplane_constants.BUILD_TYPE_RC,1,1,build_numbers[1])
        test_variations(v1, v2, 0)

runTestCases([TestBuildNumberVerStruct])
