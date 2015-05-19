import os
import glob
import subprocess

for file in glob.glob('./tests/**/*.test.blend'):
  subprocess.call(['blender', '-b', file, '--python', file.replace('.blend', '.py')])
