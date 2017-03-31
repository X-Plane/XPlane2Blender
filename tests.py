import os
import glob
import subprocess
import sys
import shutil
import re

    
"""
SPECIAL HARDCODED STRING error checking string

Rather than try complicated string matching, the exporter prints

LOGGER HAD X UNEXPECTED ERRORS 

The string is never indented. The formating of X is not specified, as long as it parses to an int
"""
ERRORED_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED ERRORS"

if os.path.exists('./tests/tmp'):
    # empty temp directory
    shutil.rmtree('./tests/tmp')

# create temp dir if not exists
os.mkdir('./tests/tmp')

def getFlag(name):
    return name in sys.argv

def getOption(name, default):
    index = -1

    try:
        index = sys.argv.index(name)
    except:
        pass

    if index > 0 and len(sys.argv) > index + 1:
        return sys.argv[index + 1]

    return default

fileFilter = getOption('--filter', None)
exclude = getOption('--exclude', None)
blenderExecutable = getOption('--blender', 'blender')
debug = getFlag('--debug')
keep_going = getFlag('--continue')
be_quiet = getFlag('--quiet')
showHelp = getFlag('--help')

if showHelp:
    print(
        'Usage: python tests.py [options]\n\n' +
        'Options:\n\n' +
        '  --filter [regex]\tfilter test files with a regular expression\n' +
        '  --exclude [regex]\texclude test files with a regular expression\n' +
        '  --debug\t\tenable debugging\n' +
        '  --continue\tKeep running after test failure\n' +
        '  --quiet\tReduce output from tests\n' +
        '  --blender [path]\tProvide alternative path to blender executable\n' +
        '  --help\t\tdisplay this help\n\n'
    )
    sys.exit(0)

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
                    print(("/*=== Running file " + pyFile).ljust(75,'=')+'{{{')

                args = [blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b']

                if os.path.exists(blendFile):
                    args.append(blendFile)

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
                    
                logger_matches = re.search(ERRORED_LOGGER_REGEX, out)
                if logger_matches == None:
                    num_errors = 0
                else:
                    num_errors = (int(logger_matches.group(1)))
 
                if not be_quiet: 
                    print(out)
                                   
                if out.find('FAIL') != -1 or num_errors != 0:
                    print('%s FAILED' % pyFile)
                    if not keep_going:
                        exit(1)
                elif be_quiet:
                    print('%s passed' % pyFile)
                
                #THIS IS THE LAST THING TO PRINT BEFORE A TEST ENDS
                #Its a little easier to see the boundaries between test suites,
                #given that there is a mess of print statements from Python, unittest, the XPlane2Blender logger,
                #Blender, and more in there sometimes
                if not be_quiet:
                    print(('=' *75)+"}}}*/")
