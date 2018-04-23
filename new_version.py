import argparse
import os
import sys
import re
import subprocess

from io_xplane2blender.xplane_helpers import VerStruct

parser = argparse.ArgumentParser(description='Change the version number information of XPlane2Blender')
parser.parse_args()

--source_folder
--version_major
--version_minor
--etc,etc
raise Exception

'''
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

filepath = os.path.join(__dirname__, 'io_xplane2blender', '__init__.py')
f = open(filepath, 'r')

initFile = f.read()
f.close()


import collections

args = collections.OrderedDict(
        {
            #Args
            '--version':('')
                }
        )

def main(argv):
    # args
    # --version put in new version to overwrite
    # --skip-validation
    # --use-time
    # --make-commit
    # -f, --force

optoin for typing in full string, simple string but with beta-6, or individual components
    # write new timestamp and 
    # run validation test on new io_xplane2blender (will need addon flag added to python tests saying which folder it should look into)

    #copy contents of io_xplane2blender to io_xplane2blender_3_4_0_asdlsdf
    use path object
    config_file = os.path.join(__file__,'..','io_xplane2blender','xplane_config.py')
    
    build_number = VerStruct.make_new_build_number()

    #Find all dot and __ folders and delete them
    #Find all .orig and .blend# files and delete them
    #Zip contents, place in builds folder
    #delete tmp folder
    #Append build log information

if __name__ == "main":
    main(sys.argv)

initFile = re.sub(r"\"version\"\: \(\d+,\d+,\d+\)", '"version": (%s)' % version.replace('.', ','), initFile)

f = open(filepath, 'w')
f.write(initFile)
f.close()

# now commit new version and tag it
print(execCmd(['git', 'add', 'io_xplane2blender/__init__.py']))
print(execCmd(['git', 'commit', '-m', 'v%s' % version]))
print(execCmd(['git', 'tag', 'v%s' % version]))
'''
