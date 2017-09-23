
# ======================================================#
# File automagically generated by GUI2Exe version 0.5.0
# Andrea Gavana, 01 April 2007
# ======================================================#

# Let's start with some default (for me) imports...

from cx_Freeze import setup, Executable


# Process the includes, excludes and packages first

includes = ['cairo', 'gobject', 'gtk', 'pango',
            'pangocairo', 'Crypto.Cipher', 'czipfile']
excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter']
packages = []
path = []

# These will give us a nice-looking gtk+ theme on the Windows side
include_files = [
    ('win32support/gtkrc', 'etc/gtk-2.0/gtkrc'),
    ('win32support/libclearlooks.dll',
     'lib/gtk-2.0/2.10.0/engines/libclearlooks.dll'),
]

# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

# No custom code added

# The setup for cx_Freeze is different from py2exe. Here I am going to
# use the Python class Executable from cx_Freeze


GUI2Exe_Target_1 = Executable(
    # what to build
    script="eschalon_main.py",
    initScript=None,
    base=None,
    targetDir=r"dist",
    targetName="eschalon_gui.exe",
    compress=True,
    copyDependentFiles=False,
    appendScriptToExe=False,
    appendScriptToLibrary=False,
    icon=None
)

# That's serious now: we have all (or almost all) the options cx_Freeze
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(

    version="1.0.2",
    description="Eschalon Utilities",
    author="CJ Kucera",
    name="Eschalon Utilities",

    options={"build_exe": {"includes": includes,
                           "excludes": excludes,
                           "packages": packages,
                           "path": path,
                           "include_files": include_files,
                           }
             },

    executables=[
        GUI2Exe_Target_1,
    ]
)

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

# No post-compilation code added


# And we are done. That's a setup script :-D
