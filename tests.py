import os
import glob
import subprocess
import sys
import shutil
import re

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
blenderExecutable = getOption('--blender', 'blender')
debug = getFlag('--debug')
showHelp = getFlag('--help')

if showHelp:
    print(
        'Usage: python tests.py [options]\n\n' +
        'Options:\n\n' +
        '  --filter [regex]\tfilter test files with a regular expression\n' +
        '  --debug\t\tenable debugging\n' +
        '  --blender [path]\tProvide alternative path to blender executable\n' +
        '  --help\t\tdisplay this help\n\n'
    )
    sys.exit(0)

def inFilter(filepath):
    if fileFilter == None:
        return True

    return (re.search(fileFilter, filepath))

for root, dirs, files in os.walk('./tests'):
    for pyFile in files:
        pyFile = os.path.join(root, pyFile)
        if pyFile.endswith('.test.py'):
            # skip files not within filter
            if inFilter(pyFile):
                blendFile = pyFile.replace('.py', '.blend')

                print('Running file %s' % pyFile)

                args = [blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b']

                if os.path.exists(blendFile):
                    args.append(blendFile)

                args.append('--python')
                args.append(pyFile)

                if debug:
                    args.append('--debug')

                subprocess.call(args)
