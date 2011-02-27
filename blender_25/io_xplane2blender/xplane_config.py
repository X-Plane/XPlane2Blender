from io_xplane2blender.xplane_helpers import XPlaneDebugger,XPlaneProfiler

# Variable: debug
# Set to True for debugging output using <debugger>. Default is True, as we are still dealing with a development release.
debug = True

# Variable: log
# Set to True, to log debug output in a file. This is still experimental.
log = False

# Variable: profile
# Set to True to use profiling processes using the <profiler>. Profiling results will be printed to the console.
profile = True

# Variable: version
# Integer containing the version number of the addon. Until we reach a release candidate it will stay 3200 (3.20).
version = 3200

# Variable: debugger
# An instance of <XPlaneDebugger> which is used to output debug information.
debugger = XPlaneDebugger()

# Variable: profiler
# Instance of <XPlaneProfiler> which is used to profile processes.
profiler = XPlaneProfiler()