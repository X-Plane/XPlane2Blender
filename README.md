[![Build Status](https://travis-ci.org/der-On/XPlane2Blender.svg?branch=v3-3)](https://travis-ci.org/der-On/XPlane2Blender)

# Introduction
This addon for Blender 2.72 and up makes it possible to export models made in Blender to the X-Plane object format (.obj). Despite the name "XPlane2Blender", there is no import feature.

## General Requirements
- Blender 2.72 or higher
- XPlane2Blender 3.3.10 or higher

People wishing to develop the plugin should the tutorial on Plugin Development in the manual.

## Automatic Installation
**Note: This process will override an existing copy of the plugin!** This is probably what you want anyway, however, just in case you want, write down or copy the previous version of the plugin.

1. Download the latest **non-pre-release** ``.zip`` version of the plugin from the [releases page](https://github.com/der-On/XPlane2Blender/releases). Look for files that don't have ``-alpha``, ``-beta``, ``-rc`` in the name, such as ``io_xplane2blender_3_4_0+20170828124634.zip``. Do **NOT** unzip the file
2. In Blender, open up the User Preferences, go to the Addons tab, and click at the bottom "Install From File..."
3. Using the file picker, find the .zip file and click "Install From File...". This will automatically unzip to the addons folder, and enable it.
4. Restart Blender even if you see the UI change and begin using XPlane2Blender!

Make backups of your work. Newer versions may have introduced backwards compatibility issues. Check the release notes between your current version (if you have one) and the version you're downloading for details.

For a more detailed installation guide including, including manual installation, please read the [manual](https://der-on.gitbooks.io/xplane2blender-docs/content/v3.4/34_installation.html).

## Documentation Sources
Be aware, documentation for XPlane2Blender may not be up to date. **This is being worked on heavily because someone told us it was important to them!** Lessons learned: Read with an eye on dates published and version numbers, ask the devs for help, and tell us what you need! __We do reply back eventually.__

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
