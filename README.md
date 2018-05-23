[![Build Status](https://travis-ci.org/der-On/XPlane2Blender.svg?branch=v3-3)](https://travis-ci.org/der-On/XPlane2Blender)

# Introduction
This addon for Blender 2.76 and up makes it possible to export models made in Blender to the X-Plane object format (.obj). Despite the name "XPlane2Blender", there is no import feature.

## General Requirements
- Blender 2.76 or higher
- XPlane2Blender 3.3.10 or higher

People wishing to develop the plugin should the tutorial on Plugin Development in the manual.

## Automatic Installation
**Note: This process will override an existing copy of the plugin!** To backup your current version of the plugin, see the manual instructions in the [manual](https://der-on.gitbooks.io/xplane2blender-docs/content/v3.4/34_installation.html). **Always make backups of your work, especially when beta testing, as newer versions may not be backwards compatibility.** Read the release notes for more details.

1. Download the latest **non-pre-release** ``.zip`` version of the plugin from the [releases page](https://github.com/der-On/XPlane2Blender/releases). Download the .zip file that has ``_rc`` in the name: for instance ``io_xplane2blender_3_4_0_rc-1-3_20171223025744.zip``. Do **NOT** unzip the file
2. In Blender, open up the User Preferences, go to the Addons tab, and click at the bottom "Install From File..."
3. Using the file picker, find the .zip file and click "Install From File...". This will automatically unzip to the addons folder
4. Ensure the checkbox next to the words "Import-Export: Export: X-Plane (.obj)" is checked
5. Restart Blender even if you see the UI change and begin using XPlane2Blender!
How to use:
-----------
- [XPlane2Blender Manual](https://der-on.gitbooks.io/xplane2blender-docs/content/)
- [Dan Klaue's "Using Blender With PlaneMaker" Playlist](https://www.youtube.com/playlist?list=PLDB0F4B925CF9169C)
- [X-Plane Scenery File Formats](http://developer.x-plane.com/docs/specs/)
- [X-Plane.org's 3d Modeling board](https://forums.x-plane.org/index.php?/forums/forum/45-3d-modeling/)
- [X-Plane Scenery Developer Blog/Knowledge Base](http://developer.x-plane.com/)
- [X-Plane Modeling Tutorials](http://developer.x-plane.com/docs/modeling/)


## Contact Us
The best way to contact us is through [a bug report](https://github.com/der-On/XPlane2Blender/issues). Otherwise, e-mail ted at x-plane dot com, especially if you're worried about the security of your payware models while debugging them.
## Test Suite
**The average user does not need the test suite.** Before releasing a build to the public we test the code many many many times! This is only useful for developers and power user who make changes to the source code.

If you have Python installed (hopefully matching Blender's internal interpreter for maximum stability) and the **full source code** downloaded, you can run the test suite. It will attempt to export sample .blend files that utilize various features of the exporter and print the results (see the contents of the ``test`` folder). All passing means XPlane2Blender is safe to use. In the XPlane2Blender folder, open up a command line and run

``python tests.py --print-fails``

This will run all tests until the end or a failure occurs. Only detailed logs will be printed for the failed test. See ``--help`` to show all flags and what they do.
