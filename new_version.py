import os
import sys
import re
import subprocess

def execCmd(args):
    out = subprocess.check_output(args, stderr = subprocess.STDOUT)

    if sys.version_info >= (3, 0):
        out = out.decode('utf-8')

    return out

if len(sys.argv) < 2:
    print('Usages: python new_version.py [version]')
    exit(1)
version = sys.argv[1]

__dirname__ = os.path.dirname(__file__)

f = open(os.path.join(__dirname__, 'io_xplane2blender', '__init__.py'), 'rw+')

initFile = f.read()

initFile = re.sub(r"\"version\"\: \(\d+,\d+,\d+\)", '"version": (%s)' % version.replace('.', ','), initFile)

f.truncate(0)
f.write(initFile)
f.close()

# now commit new version and tag it
print(execCmd(['git', 'add', 'io_xplane2blender/__init__.py']))
print(execCmd(['git', 'commit', '-m', 'v%s' % version]))
print(execCmd(['git', 'tag', 'v%s' % version]))
