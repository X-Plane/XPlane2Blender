[![Build Status](https://travis-ci.org/X-Plane/XPlane2Blender.svg?branch=master)](https://travis-ci.org/X-Plane/XPlane2Blender)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)

# Introduction
This addon for Blender 2.80 and up makes it possible to export models made in Blender to the X-Plane object format (.obj). 
An experimental importer has been added in 4.2.0-Alpha 1 and can be found here: https://github.com/X-Plane/XPlane2Blender/releases/tag/v4.2.0-alpha.1 

## Contact Us
The best way to contact us is through [a bug report](https://github.com/X-Plane/XPlane2Blender/issues). Otherwise, e-mail **ted at x-plane dot com**, especially if you're worried about the security of your models while we debug them.

## General Requirements
- Blender 2.80-83. 2.90 seems to work but is not officially supported
- For the greatest stability, use the latest non-beta version of [XPlane2Blender](https://github.com/X-Plane/XPlane2Blender/releases/latest)

XPlane2Blender for Blender 2.79 can still be downloaded from the releases page, but it isn't supported anymore. An experimental converter for Blender 2.49 projects is also available and is supported.

## Automatic Installation
**Note: This process will override an existing copy of the plugin!** To backup your current version of the plugin, see the manual instructions in the [manual](https://xp2b-docs.gitbook.io/xplane2blender-docs/index-3/34_installation). **Always make backups of your work, especially when beta testing, as newer versions may not be backwards compatibility.** Read the release notes for more details.

1. Download the [addon](https://github.com/X-Plane/XPlane2Blender/releases/latest) with a name like ``io_xplane2blender_4_0_0-rc_1-89_20200910152046.zip``. **Do not download the .zip file called "Source Code", do not unzip the io_xplane2blender .zip file**
2. In Blender, open up the Preferences, go to the Addons tab, and click at the bottom "Install From File..."
3. Using the file picker, find the .zip file and click "Install From File...". This will automatically unzip to the addons folder
4. Ensure the checkbox next to the words "Import-Export: Export: X-Plane (.obj)" is checked
5. **Restart Blender even if you see the UI change**
6. Begin using XPlane2Blender!

For less stable betas or different versions see the [releases page](https://github.com/X-Plane/XPlane2Blender/releases). Be sure to read the notes.

## Get Started!
See the [Introduction to XPlane2Blender Video](https://developer.x-plane.com/tools/blender/) and download the example files and you'll be well on your way to exporting your first mesh and seeing it in X-Plane! Although the Blender version shown is Blender 2.79, XPlane2Blender is almost entirely the same across versions.

## Documentation Sources
- [XPlane2Blender Manual](https://xp2b-docs.gitbook.io/xplane2blender-docs)
- [The PZL-M-18, an open source aircraft](https://github.com/todirbg/PZL-M-18)
- [The BD-5J Microjet, an open source jet](https://forums.x-plane.org/index.php?/files/file/27269-bd-5j-microjet)
- [Dan Klaue's "Using Blender With PlaneMaker" Playlist](https://www.youtube.com/playlist?list=PLDB0F4B925CF9169C). While older it still explains many of the principles of XPlane2Blender
- [X-Plane Scenery File Formats](http://developer.x-plane.com/docs/specs/)
- [X-Plane.org's 3d Modeling board](https://forums.x-plane.org/index.php?/forums/forum/45-3d-modeling/)
- [X-Plane Scenery Developer Blog/Knowledge Base](http://developer.x-plane.com/)
- [X-Plane Modeling Tutorials](http://developer.x-plane.com/docs/modeling/)

## Test Suite
**The average user does not need the test suite.** Before releasing a build to the public we test the code many many many times! This is only useful for developers and power users who make changes to the source code. The tests folder must also be in the same folder as the addon folder (see manual installation).

If you have Python installed (hopefully matching Blender's internal interpreter for maximum stability) and the **full source code** downloaded, you can run the test suite. It will attempt to export sample .blend files that utilize various features of the exporter and print the results (see the contents of the ``test`` folder). All passing means XPlane2Blender is safe to use. In the XPlane2Blender folder, open up a command line and run

``python tests.py --print-fails``

This will run all tests until the end or a failure occurs. Only detailed logs will be printed for the failed test. See ``--help`` to show all flags and what they do.
