@echo off
set PATH=%PATH%;"C:\Program Files\Inno Setup 5";"C:\Program Files (x86)\Inno Setup 5"
echo "Removing old build artifacts"
rd /s /q build
rd /s /q dist
rd /s /q Output
echo "Building exes"
win-setup.py build_exe
echo "Setting up the distribution directory"
copy build\exe.win32-2.7\*.* dist\
copy data\*.* dist\
echo "Compiling the installer"
iscc win-inno.iss
