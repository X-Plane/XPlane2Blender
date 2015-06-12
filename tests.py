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

def inFilter(filepath):
    if fileFilter == None:
        return True

    return (re.search(fileFilter, filepath))

for pyFile in glob.glob('./tests/**/*.test.py'):
    # skip files not within filter
    if inFilter(pyFile):
        blendFile = pyFile.replace('.py', '.blend')

        print('Running file %s' % pyFile)

        if os.path.exists(blendFile):
            subprocess.call([blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b', blendFile, '--python', pyFile])
        else:
            subprocess.call([blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b', '--python', pyFile])
