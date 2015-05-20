import os
import glob
import subprocess
import sys

blenderExecutable = 'blender'

if len(sys.argv) > 1:
    blenderExecutable = sys.argv[1]

for file in glob.glob('./tests/**/*.test.blend'):
  subprocess.call([blenderExecutable, '-b', file, '--python', file.replace('.blend', '.py')])
