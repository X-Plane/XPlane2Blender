@rem Installation script for Windows NT/2000/XP
@echo off

echo Installing Blender scripts . . .

for %%I in (%0) do cd "%%~dpI"

rem Old files
set FILES=..\Bpymenus helpXPlane.py uvCopyPaste.py uvFixupACF.py uvResize.py XPlaneAnimObject.py XPlaneExport.py XPlaneExport.pyc XPlaneExport7.py XPlaneExport8.py XPlaneExportCSL.py XPlaneExportBodies.py XPlaneImport.py XPlaneImport.pyc XPlaneImportPlane.py XPlaneImportBodies.py XPlanePanelRegions.py XPlaneUtils.py XPlaneUtils.pyc XPlaneHelp.py XPlaneACF.py XPlaneACF.pyc XPlane2Blender.html XPlaneImportPlane.html XPlaneReadme.txt DataRefs.txt

set DIRS=
if defined HOME set DIRS=%DIRS% "%HOME%\.blender\scripts"

rem Try to locate Blender
set FTYPE=
for /f "tokens=2 delims==" %%I in ('assoc .blend') do set FTYPE=%%I
if not defined FTYPE goto noassoc
set BDIR=
for /f "tokens=2* delims==" %%I in ('ftype %FTYPE%') do set BDIR=%%~dpI
if defined BDIR set DIRS=%DIRS% "%BDIR%.blender\scripts"
:noassoc

set DIRS=%DIRS% "%ProgramFiles%\Blender Foundation\Blender\.blender\scripts" "%USERPROFILE%\Application Data\Blender Foundation\Blender\.blender\scripts"

rem Remove old files from everywhere
for %%D in (%DIRS%) do for %%I in (%FILES%) do if exist "%%~D\%%I" del "%%~D\%%I" >nul: 2>&1

rem Remove empty script directories to prevent masking - but not home dir
if not defined BDIR goto defdir
set DESTDIR=%BDIR%.blender\scripts
set EMPTY=1
for %%I in ("%DESTDIR%\*") do set EMPTY=0
if exist "%DESTDIR%\" if %EMPTY%==1 rd "%DESTDIR%"

:defdir
set DESTDIR=%ProgramFiles%\Blender Foundation\Blender\.blender\scripts
set EMPTY=1
for %%I in ("%DESTDIR%\*") do set EMPTY=0
if exist "%DESTDIR%\" if %EMPTY%==1 rd "%DESTDIR%"

set DESTDIR=%USERPROFILE%\Application Data\Blender Foundation\Blender\.blender\scripts
set EMPTY=1
for %%I in ("%DESTDIR%\*") do set EMPTY=0
if exist "%DESTDIR%\" if %EMPTY%==1 rd "%DESTDIR%"

rem Find target script directory
for %%D in (%DIRS%) do if exist "%%~D\" (set DESTDIR=%%~D& goto copy)

:destfail
echo.
echo Failed to find the correct location for the scripts !!!
goto end

:copy
set FILES=uvCopyPaste.py uvFixupACF.py uvResize.py XPlaneAnimObject.py XPlaneExport.py XPlaneExport7.py XPlaneExport8.py XPlaneExportCSL.py XPlaneImport.py XPlaneImportPlane.py XPlanePanelRegions.py XPlaneUtils.py XPlaneHelp.py XPlane2Blender.html DataRefs.txt
for %%I in (%FILES%) do copy /v /y %%I "%DESTDIR%\" >nul:
for %%I in (%FILES%) do if not exist "%DESTDIR%\%%I" goto copyfail
echo.
echo Installed scripts in folder
echo   %DESTDIR%
goto end

:copyfail
echo.
echo Failed to install scripts in folder
echo   %DESTDIR% !!!
echo Did you extract all of the contents of the zip file?
goto end

:end
echo.
pause
:reallyend
