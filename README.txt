Eschalon Savefile Editor
Copyright (C) 2008-2010 CJ Kucera

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

Some icons in this program are Copyright Axialis Team, and released
under a Creative Commons Attribution 2.5 Generic license.  See
http://www.axialis.com/free/icons/ for details.

The code in fzipfile.py comes mostly from Python itself, which is under
the Python License at http://www.python.org/psf/license/

The class WrapLabel, in basegui.py is Copyright(c) 2005 VMware, Inc.
See basegui.py for the exact licensing terms.

ABOUT
-----

This package contains applications for editing savegames in
the games Eschalon Book I and Book II, by Basilisk Games.

   http://basiliskgames.com/eschalon-book-i
   http://basiliskgames.com/eschalon-book-ii

There are four separate utilities: a character editor and a map editor
for both Book I and Book II.  The map editor can edit maps stored as
part of your savegame, and the global maps included in the game
distribution, though for Book II there is no direct way to get at the
global map files.

Right now the utilities support just about everything you'd want to edit,
though there's still plenty of values in the file of whose purpose I'm
unaware.  See the TODO file for information on what needs to be done with
the app still, which is quite a bit.

The app seems stable enough for me, but use your head and keep a backup of
any file that you use this on.  Do let me know if it ends up eating your
character or map, because I'd like to fix the bug.  Just don't get upset
if it does.  :)  The Character Editor's been around rather longer than the
map editor, so be especially careful when editing maps.  Note that the map
files (which end in .map) also have an associated file with a ".ent"
extension.  As you make backups of the maps you're editing, be sure to back up
that file as well.

This was developed on Linux, and it uses Python, GTK+, and PyGTK to do
its stuff.  The application also runs perfectly fine on Windows (see the
Windows section, below).  I know that the required Python/GTK+ packages
are supposed to be available on OSX, but I don't have easy access to that
platform, so I'm not sure what needs to be done to package it up and get it
running.  If you're familiar with those kinds of things, let me know and
I'll get going on it.

INSTALLATION, GENERAL
---------------------

The map editor component of this package requires that an Eschalon install
directory be present on your system, to load the map graphics.  The application
will try to locate it on its own, but if the installation directory isn't found,
you'll be prompted to provide the location.  The character editor can also
use the Eschalon game directory to do image lookups of its own, but it
doesn't actually require the directory to be present.

Both the map editor and the character editor have a preferences screen (which
write to the same config file, so the same configuration applies to both
programs) where the game directory can be set, in addition to your savefile
directory (which the program will also try to auto-detect).  The savefile
directory is basically just used as the directory the "Open" dialog will
default to.  The setting doesn't currently control anything else.

INSTALLATION, LINUX
-------------------

There's no official installation scripts for the app.  What I'd recommend on a
Linux system is just leaving it untarred wherever you untarred it, and make
a symlink to eschalon_b1_char.py, eschalon_b1_map.py, and eschalon_b2_char.py
into somewhere in your $PATH (~/bin is probably the best location).  For example:

   $ cd ~/bin
   $ ln -s /path/to/eschalon_b1_char.py .
   $ ln -s /path/to/eschalon_b1_map.py .
   $ ln -s /path/to/eschalon_b2_char.py .
   $ ln -s /path/to/eschalon_b2_map.py .

At that point you should be able to just run "eschalon_b1_char.py" from the
command prompt, for instance.  Setting up shortcuts through your window
manager of choice should work fine, as well.  Failing that, just run them
from the directory you untarred them into.

NOTE ABOUT BOOK II MAP EDITING: To edit Book II map files, you'll need two
other packages installed which may not be present on your system.  The first
is PyCrypto: http://www.dlitz.net/software/pycrypto/  This tends to be
packaged as "python-crypto" by most distributions.  Gentoo uses "pycrypto."
The second package is czipfile, available here: http://pypi.python.org/pypi/czipfile
This is probably not packaged by your distribution yet.  The easiest way to
install it would be via either easy_install or pip:

  # easy_install czipfile
 or
  # pip install czipfile

If those methods don't work for you, you should be able to just download it
from the above link.  Note that czipfile isn't ACTUALLY required to edit Book
II maps, but without czipfile, loading maps can take an absurdly long time.
Trust me, you will want to have it installed.  Note once again that this only
affects Book II map editing.  The character editors, and the Book I map editor
are not affected.

As of 0.5.0, the minimum gtk+ required MIGHT be 2.18.0, though you may have
success with earlier versions.  If there are problems with older versions,
please let me know so I can take a look and possibly get a workaround
in place.  The app will show a warning if your gtk+ doesn't meet this
requirement, but allow you to continue regardless.

INSTALLATION, WINDOWS
---------------------

The recommended way to install these utilities on Windows is through the install
EXE which is provided as of version 0.5.0.  Theoretically, you should be able
to just double-click on the installer, go through the usual installer screens,
and you'll have both the map editor and the charater editor in a folder in
your start menu.  Please be sure to let me know if there are problems with
that process, as I hardly spend any time in Windows, and the Windows side is
far less tested than the Linux side.

You're welcome to run the Python scripts directly (as the Linux folks do), if
you want, in which case you will need a gtk+ runtime (I recommend a recent one
directly from gtk.org), Python (2.6), and all three PyGTK components installed
(PyCairo, PyGObject, and PyGTK).  Additionally, to edit Book II maps, you'll
want PyCrypto and czipfile.  Some direct links can be found on the website.

INSTALLATION, OSX
-----------------

I don't know.  If anyone gets this running, let me know so I can update the
documentation.

USAGE
-----

The applications are mostly designed to be run via their GUIs, which you
can launch simply by double-clicking or running eschalon_b1_char.py,
eschalon_b1_map.py or eschalon_b2_char.py.  There are commandline options for
both, though, and you can get help for those options by running
"eschalon_b1_char.py -h", for instance, to get help with the character editor.
A few of the character editor commandline options may be useful.  The options
available on the map editor are far less useful.

The drawing features on the map editor are fairly new still, and I expect that
bugs will eventually be found.  Let me know!

Some more documentation on various aspects of the Eschalon map that I've
discovered, see http://apocalyptech.com/eschalon/

CONTACT
-------

Feel free to email me at pez@apocalyptech.com if you've got questions /
concerns.  I'm also logged in to irc.freenode.net as the user "sekhmet" if
you'd prefer that.
