import argparse
import glob
import os
import re
import shutil
import subprocess
import sys

    
"""
SPECIAL HARDCODED STRING error checking string

Rather than try complicated string matching, the exporter prints

LOGGER HAD X UNEXPECTED ERRORS 

The string is never indented. The formating of X is not specified, as long as it parses to an int
"""
ERROR_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED ERRORS"
# One day if we need to have a strictness rating we can have it stop on warnings as well as errors
#WARNING_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED WARNING"

def clean_tmp_folder():
    # TODO: This cannot run when the tmp folder is open
    # in a file browser or is in use. This is annoying.
    if os.path.exists('./tests/tmp'):
        # empty temp directory
        shutil.rmtree('./tests/tmp',ignore_errors=True)

    # create temp dir if not exists
    os.makedirs('./tests/tmp')

def _make_argparse():
    parser = argparse.ArgumentParser(description="Runs the XPlane2Blender test suite")
    test_selection = parser.add_argument_group("Test Selection And Control")
    test_selection.add_argument("-f", "--filter",
            help="Filter test files with a regular expression",
            type=str)#[regex]
    test_selection.add_argument("--exclude",
            help="Exclude test files with a regular expression",
            type=str)#[regex]
    test_selection.add_argument("-c", "--continue", 
            help="Keep running after a test failure", 
            default=False,
            action="store_true",
            dest="keep_going")

    output_control = parser.add_argument_group("Output Control")
    output_control.add_argument("-q", "--quiet",
            default=False,
            help="Only output if tests pass or fail",
            action="store_true")
    output_control.add_argument("-p", "--print-fails",
            default=False,
            help="Like --quiet, but also prints the output of failed tests", 
            action="store_true")
    # Hopefully it could one day also enable pydev, and we can move this to a --verbose argument
    output_control.add_argument("--force-xplane-debug",
            default=False,
            help="Shows verbose(!) debug info and turns on Scene's Debug if not set in Blend file",
            action='store_true')

    blender_options = parser.add_argument_group("Blender Options")
    blender_options.add_argument("--blender",
            default="blender",# Use the blender in the system path
            type=str,
            help="Provide alternative path to blender executable")
    blender_options .add_argument("--force-blender-debug",
            help="Turn on Blender's --debug flag", 
            action="store_true")
    blender_options.add_argument("-n", "--no-factory-startup",
            help="Run Blender with current prefs rather than factory prefs",
            action="store_true")
    return parser

def main(argv=None):
    clean_tmp_folder()
    if argv is None:
        argv = _make_argparse().parse_args(sys.argv[1:])
    exit_code = 0

    def printTestBeginning(text):
        '''Print the /* and {{{ and ending pairs are so that text editors can recognize places to automatically fold up the tests'''
        print(("/*=== " + text + " ").ljust(75,'=')+'{{{')

    def printTestEnd():
        print(('=' *75)+"}}}*/")     

    def inFilter(filepath):
        passes = True

        if argv.filter != None:
            passes &= bool(re.search(argv.filter, filepath))

        if argv.exclude != None:
            passes &= not (re.search(argv.exclude, filepath))

        return passes

    for root, dirs, files in os.walk('./tests'):
        for pyFile in files:
            pyFile = os.path.join(root, pyFile)
            if pyFile.endswith('.test.py'):
                # skip files not within filter
                if inFilter(pyFile):
                    blendFile = pyFile.replace('.py', '.blend')

                    if not (argv.quiet or argv.print_fails):
                        printTestBeginning("Running file " + pyFile)

                    blender_args = [argv.blender, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b']

                    if argv.no_factory_startup:
                        blender_args.remove('--factory-startup')

                    if os.path.exists(blendFile):
                        blender_args.append(blendFile)
                    else:
                        if not (argv.quiet or argv.print_fails):
                            print("WARNING: Blender file " + blendFile + " does not exist")
                            printTestEnd()

                    blender_args.extend(['--python', pyFile])

                    if argv.force_blender_debug:
                        blender_args.append('--debug')

                    # Small Hack!
                    # Blender stops parsing after '--', so we can append the test runner
                    # args and bridge the gap without anything fancy!
                    blender_args.extend(['--']+sys.argv[1:])

                    if not argv.quiet and\
                            (argv.force_blender_debug or argv.force_xplane_debug):
                        # print the command used to execute the script
                        # to be able to easily re-run it manually to get better error output
                        print(' '.join(blender_args))

                    out = subprocess.check_output(blender_args, stderr = subprocess.STDOUT)

                    if sys.version_info >= (3, 0):
                        out = out.decode('utf-8')
                        
                    logger_matches = re.search(ERROR_LOGGER_REGEX, out)
                    if logger_matches == None:
                        num_errors = 0
                    else:
                        num_errors = (int(logger_matches.group(1)))
     
                    if not (argv.quiet or argv.print_fails): 
                        print(out)
                    
                    #Normalize line endings because Windows is dumb 
                    out = out.replace('\r\n','\n')
                    out_lines = out.split('\n')
                    
                    #First line of output is unittest's sequece of dots, E's and F's
                    #TODO: Except when it isn't like when a SyntaxError occurs and
                    #the test appears to pass!
                    if 'E' in out_lines[0] or 'F' in out_lines[0] or num_errors != 0:
                        exit_code = 1
                        if argv.print_fails:
                            printTestBeginning("Running file %s - FAILED" % (pyFile))
                            print(out)
                        else:
                            print('%s FAILED' % pyFile)
                        
                        if argv.print_fails:
                            printTestEnd()

                        if not argv.keep_going:
                            return exit_code
                    elif (argv.quiet or argv.print_fails):
                        print('%s passed' % pyFile)
                    
                    #THIS IS THE LAST THING TO PRINT BEFORE A TEST ENDS
                    #Its a little easier to see the boundaries between test suites,
                    #given that there is a mess of print statements from Python, unittest, the XPlane2Blender logger,
                    #Blender, and more in there sometimes
                    if not argv.quiet:
                        printTestEnd()
    return exit_code 

if __name__ == "__main__":
    sys.exit(main())
