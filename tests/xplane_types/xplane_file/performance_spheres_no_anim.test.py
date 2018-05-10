import os
import inspect
import time
import sys

import bpy
from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestPerformanceSpheresNoAnim(XPlaneTestCase):
    def test_performance_spheres_no_anim(self):
        start = time.perf_counter()
        xplane_config.setDebug(True)
        out = self.exportLayer(0)
        end = time.perf_counter() - start

        filename = inspect.stack()[0][3]
        print("Export time of {}: {}".format(filename,end))
        
        # 63.0 was the high water mark on my laptop
        # Using Blender 2.79, external Python 3.5.3 environment,
        # I used PyVmMonitor that started and connceted in the addon's
        # __init__ function, right at the beginning
        #
        # Total Cumulative Export Time
        # Minimum: 52.5 seconds total
        # Mean: ?
        # Maximum: 63.0 seconds total, this is probably an outlier
        #
        # CPU - Intel Core i7 6700HQ @ 2.60GHz
        # GPU - 3071 MB NVIDIA GeForce GTX 970M
        # RAM - 16GB
        # OS - 64 bit Win10 (bleh), with standard development tools and browser running
        # no other large system hogs running at the time
        #
        # Travis CI seems to be able to export this in 42.0 to 44.00 seconds
        # - Ted, 5/10/2018  
        MAX_TOTAL_CUMULATIVE_EXPORT_TIME = 63.0
        self.assertTrue((time.perf_counter()-start) < MAX_TOTAL_CUMULATIVE_EXPORT_TIME)

        #Thanks https://stackoverflow.com/a/13094326!
        def find_nth(string, substring, n):
           if (n == 1):
               return string.find(substring)
           else:
               return string.find(substring, find_nth(string, substring, n - 1) + 1)

        #print(out[0:1150]+'|\n')
        s = out[find_nth(out,"VT",1):find_nth(out,"\n",7)]
        #print(s)
        #print("VT	0.16221175	0.55557019	-0.81549317	0.08653186	0.46962854	-0.87861329	0	0	# 1")

        # This is all we need to confirm we're removing trailing 0s and making ints when possible
        self.assertTrue(s == \
                "VT\t0.16221175\t0.55557019\t-0.81549317\t0.08653186\t0.46962854\t-0.87861329\t0\t0\t# 1")
        s = (out[find_nth(out,"VT",7):find_nth(out,"\n",14-1)])
        #print(s)
        #print("VT	0.10838643	-0.83146966	-0.54489505	0.04637594	-0.88097215	-0.4708899	0	0	# 7")
        self.assertTrue(s == \
                "VT\t0.10838643\t-0.83146966\t-0.54489505\t0.04637594\t-0.88097215\t-0.4708899\t0\t0\t# 7")

runTestCases([TestPerformanceSpheresNoAnim])
