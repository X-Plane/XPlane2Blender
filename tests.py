import os
import glob
import subprocess
import sys
import shutil

blenderExecutable = 'blender'

# empty temp directory
shutil.rmtree('./tests/tmp')

# create temp dir if not exists
if not os.path.exists('./tests/tmp'):
    os.mkdir('./tests/tmp')

if len(sys.argv) > 1:
    blenderExecutable = sys.argv[1]

for pyFile in glob.glob('./tests/**/*.test.py'):
    blendFile = pyFile.replace('.py', '.blend')

    if os.path.exists(blendFile):
        subprocess.call([blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b', blendFile, '--python', pyFile])
    else:
        subprocess.call([blenderExecutable, '--addons', 'io_xplane2blender', '--factory-startup', '-noaudio', '-b', '--python', pyFile])
