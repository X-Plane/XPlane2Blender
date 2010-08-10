#!/bin/bash
# Installation script for MacOS X

clear
echo Installing Blender scripts . . .
echo

cd "`dirname "$0"`"
IFS="
"

LS=/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister	# MacOS 10.5
if [ ! -x $LS ]; then
    # From http://developer.apple.com/documentation/Carbon/Conceptual/MDImporters/Concepts/Troubleshooting.html
    LS=/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister	# MacOS 10.3 & 10.4
    if [ ! -x $LS ]; then
        echo Can\'t find the lsregister tool!
        LS=echo;
    fi;
fi

# Candidate application locations (but completely ignore Trash)
DIRS=$($LS -dump | awk '!match($0, "\.Trash") && match($0, "/.*/.*[B|b]lender.*\.app") { print substr($0, RSTART) "/Contents/MacOS/.blender/scripts" }' | sort -u)

# Remove old files from everywhere
FILES="../Bpymenus
helpXPlane.py
uvCopyPaste.py
uvFixupACF.py
uvResize.py
XPlaneAnimObject.py
XPlaneExport.py
XPlaneExport.pyc
XPlaneExport7.py
XPlaneExport8.py
XPlaneExportCSL.py
XPlaneExportBodies.py
XPlaneImport.py
XPlaneImport.pyc
XPlaneImportPlane.py
XPlaneImportBodies.py
XPlanePanelRegions.py
XPlaneUtils.py
XPlaneUtils.pyc
XPlaneHelp.py
XPlaneACF.py
XPlaneACF.pyc
XPlane2Blender.html
XPlaneImportPlane.html
XPlaneReadme.txt
DataRefs.txt"

for I in "$HOME/.blender/scripts" $DIRS; do
    for J in $FILES; do
        if [ -e "$I/$J" ]; then
            rm -f "$I/$J";
        fi
    done;
done

# Files to install
FILES="uvCopyPaste.py
uvFixupACF.py
uvResize.py
XPlaneAnimObject.py
XPlaneExport.py
XPlaneExport7.py
XPlaneExport8.py
XPlaneExportCSL.py
XPlaneImport.py
XPlaneImportPlane.py
XPlanePanelRegions.py
XPlaneUtils.py
XPlaneHelp.py
XPlane2Blender.html
DataRefs.txt"
if [ -d "$HOME/.blender/scripts" ]; then
    DIRS="$HOME/.blender/scripts"
fi

# Copy new
DONE=
for I in $DIRS; do
    if [ -d "$I" ]; then
        if [ -w "$I" ]; then
            DIROK=1
            cp -f $FILES "$I" 2>/dev/null
            for J in $FILES; do
                if ! [ -r "$I/$J" ]; then DIROK=; fi;
            done
            if [ "$DIROK" ]; then
                DONE="$DONE
  $I";
            fi;
        else
            echo "Can't install scripts in folder:
  $I"
            if ! [ -O "$I" ]; then
                echo this folder is owned by `ls -ld "$I"|awk '{print $3}'`.;
            fi
            echo;
        fi;
    fi;
done

if [ "$DONE" ]; then
    echo "Installed scripts in folder(s):$DONE"
    echo
    exit 0;
fi

for I in $DIRS; do
    if [[ -d "$I" && "$I" != /Volumes/* ]]; then
        echo Failed to find the correct location for the scripts !!!
        echo
        exit 1;
    fi;
done

# User only has Blender on disk images
echo Failed !!!
echo Install the Blender application, eg by copying it from the disk image
echo to your Applications folder or Desktop, then run this installer again.
echo
exit 1
