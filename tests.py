import argparser
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

#One day if we need to have a strictness rating we can have it stop on warnings as well as errors
#WARNING_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED WARNING"
if os.path.exists('./tests/tmp'):
    # empty temp directory
    shutil.rmtree('./tests/tmp',ignore_errors=True)

# create temp dir if not exists
os.makedirs('./tests/tmp')

def getFlag(names):
    for name in names:
        if name in sys.argv:
            return True
    return False

def getOption(names, default):
    index = -1

    for name in names:
            
        try:
            index = sys.argv.index(name)
        except:
            pass

        if index > 0 and len(sys.argv) > index + 1:
            return sys.argv[index + 1]

    return default

fileFilter = getOption(['-f','--filter'], None)
exclude = getOption(['--exclude'], None)
blenderExecutable = getOption(['--blender'], 'blender')
debug = getFlag(['--debug'])
keep_going = getFlag(['-c','--continue'])
print_fails = getFlag(['-p','--print-fails'])
be_quiet = getFlag(['-q', '--quiet']) or print_fails
showHelp = getFlag(['--help'])
no_factory_startup = getFlag(['-n', '--no-factory-startup'])

def parse_arguments():
    parser = argparser.ArgumentParser()
    parser.add_argument("--debug",         
            help="Enable debugging", 
            action="store_true")
    parser.add_argument("-f", "--filter",   
            help="Filter test files with a regular expression", 
            type=str, 
            action="store_true")#[regex]
    parser.add_argument("--exclude",        
            help="Exclude test files with a regular expression", 
            type=str, 
            action="store_true")#[regex]
    parser.add_argument("--debug",          
            help="Enable debugging", 
            action="store_true")#[regex]
    parser.add_argument("-c", "--continue", 
            help="Keep running after test failure", 
            action="store_true")
    parser.add_argument("-q", "--quiet",    
            help="Reduce output from tests", 
            action="store_true")
    parser.add_argument("-p", "--print-fails",        
            help="Sets --quiet, but also prints the output of failed tests", 
            action="store_true")
    parser.add_argument("-n", "--no-factory-startup", 
            help="Run Blender with current prefs rather than factory prefs", 
            action="store_true")
    parser.add_argument("--blender [path]", 
            help="Provide alternative path to blender executable")
    args = parser.parse_args()
    return args

def main(argv=None):
    if argv is None:
        argv = parse_arguments()
    exit_code = 0

    def printTestBeginning(text):
        '''Print the /* and {{{ and ending pairs are so that text editors can recognize places to automatically fold up the tests'''
        print(("/*=== " + text + " ").ljust(75,'=')+'{{{')

    def printTestEnd():
        print(('=' *75)+"}}}*/")     

    def inFilter(filepath):
        passes = False

        if fileFilter != None:
            passes = (re.search(fileFilter, filepath))
        else:
            passes = True

        if exclude != None:
            passes = not (re.search(exclude, filepath))

        return passes

    for root, dirs, files in os.walk('./tests'):
        for pyFile in files:
            pyFile = os.path.join(root, pyFile)
            if pyFile.endswith('.test.py'):
                # skip files not within filter
                if inFilter(pyFile):
                    blendFile = pyFile.replace('.py', '.blend')

                    if not be_quiet:
                        printTestBeginning("Running file " + pyFile)

                    args = [blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b']

                    if no_factory_startup:
                        args.remove('--factory-startup')

                    if os.path.exists(blendFile):
                        args.append(blendFile)
                    else:
                        if not be_quiet:
                            print("WARNING: Blender file " + blendFile + " does not exist")
                            printTestEnd()

                    args.append('--python')
                    args.append(pyFile)

                    if debug:
                        args.append('--debug')

                        # print the command used to execute the script
                        # to be able to easily re-run it manually to get better error output
                        print(' '.join(args))

                    out = subprocess.check_output(args, stderr = subprocess.STDOUT)

                    if sys.version_info >= (3, 0):
                        out = out.decode('utf-8')
                        
                    logger_matches = re.search(ERROR_LOGGER_REGEX, out)
                    if logger_matches == None:
                        num_errors = 0
                    else:
                        num_errors = (int(logger_matches.group(1)))
     
                    if not be_quiet: 
                        print(out)
                    
                    #Normalize line endings because Windows is dumb 
                    out = out.replace('\r\n','\n')
                    out_lines = out.split('\n')
                    
                    #First line of output is unittest's sequece of dots, E's and F's
                    if 'E' in out_lines[0] or 'F' in out_lines[0] or num_errors != 0:
                        exit_code = 1
                        if print_fails:
                            printTestBeginning("Running file %s - FAILED" % (pyFile))
                            print(out)
                        else:
                            print('%s FAILED' % pyFile)
                        
                        if print_fails:
                            printTestEnd()

                        if not keep_going:
                            return exit_code
                    elif be_quiet:
                        print('%s passed' % pyFile)
                    
                    #THIS IS THE LAST THING TO PRINT BEFORE A TEST ENDS
                    #Its a little easier to see the boundaries between test suites,
                    #given that there is a mess of print statements from Python, unittest, the XPlane2Blender logger,
                    #Blender, and more in there sometimes
                    if not be_quiet:
                        printTestEnd()
    return exit_code 

if __name__ == "__main__":
    sys.exit(main())
