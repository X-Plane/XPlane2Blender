import os
import glob
import subprocess
import sys

blenderExecutable = 'blender'

if len(sys.argv) > 1:
    blenderExecutable = sys.argv[1]

for file in glob.glob('./tests/**/*.test.blend'):
  subprocess.call([blenderExecutable, '-b', file, '--addons io_xplane2blender', '-noaudio', '--factory-startup', '--python', file.replace('.blend', '.py')])
