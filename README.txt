Eschalon Book 1 Savefile Editor
Copyright (C) 2008, 2009 CJ Kucera

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

ABOUT
-----

This package contains two little applications for editing savegames in
the game Eschalon Book I, by Basilisk Games.

   http://basiliskgames.com/book1.html
   http://www.playgreenhouse.com/game/BASLX-000001-01/

The first is eschalon_b1_char.py, which can edit saved character
information, and the other is eschalon_b1_map.py, which can be used to
edit maps (both the maps stored in your savegame, and the stock maps
which are included in Eschalon's "data" directory).

Right now it supports just about everything you'd want to edit, though
there's still plenty of values in the file of whose purpose I'm unaware.
See the TODO file for information on what needs to be done with the app
still, which is quite a bit.

The app seems stable enough for me, but use your head and keep a backup of
any file that you use this on.  Do let me know if it ends up eating your
character or map, because I'd like to fix the bug.  Just don't get upset
if it does.  :)  The Character Editor's been around rather longer than the
map editor, so be especially careful when editing maps.  Note that the map
files (which end in .map) also have an associated file with a ".ent"
extension.  As you make backups of the maps you're editing, be sure to back up
that file as well.

This was developed on Linux, and it uses Python, GTK+, and PyGTK/Glade to do
its stuff.  The application also runs perfectly fine on Windows (see the
Windows section, below).  I know that the required Python/GTK+/PyGTK packages
are available on OSX, but I don't have easy access to that platform, so I'm
not sure what needs to be done to package it up and get it running.  If
you're familiar with those kinds of things, let me know and I'll get going
on it.

One other note: Certainly let me know if you use this on other architectures
(I'm just on x86) and see funky values through the GUI.  I'm not sure if the
game has a set endianness to its values or not, which could possibly weird
some stuff out.

INSTALLATION, GENERAL
---------------------

The map editor component of this package requires that an Eschalon install
directory be present on your system.  The application will try to locate it
on its own, but if the installation directory isn't found, you'll be
prompted to provide the location.  The character editor can now use the
Eschalon game directory to do image lookups of its own, but it doesn't
actually require the directory to be present.

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
a symlink to eschalon_b1_char.py and eschalon_b1_map.py into somewhere in
your $PATH (~/bin is probably the best location).  For example:

   $ cd ~/bin
   $ ln -s /path/to/eschalon_b1_char.py .
   $ ln -s /path/to/eschalon_b1_map.py .

At that point you should be able to just run "eschalon_b1_char.py" from the
command prompt, for instance.  Setting up shortcuts through your window
manager of choice should work fine, as well.  Failing that, just run them
from the directory you untarred them into.

INSTALLATION, WINDOWS
---------------------

As with the Linux version, there's no actual installation script or anything
like that.  If you have gtk+, Python, and PyGTK installed, though, you should
be able to just run it from wherever you unzipped it.  The various pieces of
software you'll need to run the program are:

gtk+ Runtime:
  http://sourceforge.net/project/showfiles.php?group_id=98754&package_id=121281
  Note that this version, from the gladewin32 Sourceforge project, is the
  main officially-blessed gtk+ runtime endorsed by PyGTK, so it's the best to
  use.  It includes Cairo, so a separate Cairo installation is not required.
  You can get it working with other gtk+ runtime packages, but you'll
  have to do more work for not a lot of gain.  If you DO have other gtk+
  runtimes installed, certainly be careful about installing this one
  side-by-side.  You probably only want one active at any given time.

Python:
  http://python.org/download/releases/2.6.1/
  I've tested the app on both Python 2.5 and 2.6.  It doesn't really matter
  which one you use, though you may as well use 2.6, which is the latest.
  (Don't use the 3.x releases, though.)

PyGTK:
  http://www.pygtk.org/downloads.html
  Be sure to install all three of PyCairo, PyGObject, and PyGTK.  You *need*
  all three, otherwise it won't work.  Note that the files you download will
  be labeled with either "py2.5" or "py2.6."  Be sure to download the
  appropriate package for the version of Python that you installed.

Once you've got those components installed, you should be able to just
double-click on either eschalon_b1_char.py or eschalon_b1_map.py, and
it'll give you an "Open" dialog to choose the file.

I'll look into distributing the required packages as one bundle, eventually.

INSTALLATION, OSX
-----------------

I don't know.  If anyone gets this running, let me know so I can update the
documentation.

USAGE
-----

The applications are mostly designed to be run via their GUIs, which you
can launch simply by double-clicking or running either eschalon_b1_char.py or
eschalon_b1_map.py.  There are commandline options for both, though, and you
can get help for those options by running "eschalon_b1_char.py -h", for
instance, to get help with the character editor.  A few of the character
editor commandline options may be useful.  The options available on the map
editor are far less useful.

Note that the map editor currently isn't really useful for doing larger tasks
like building a new map from scratch, or even doing "mass" editing on existing
maps (such as possibly adding new rooms, or clearing new paths through the
forest, etc).  The editor currently operates on a square-by-square basis, so
you click on one square and edit its properties, then click on the next, etc.
This is fine for introspection or doing simple things (like adding/removing
enemies, changing chest contents, etc), but there's no real "drawing" type
features yet.  I expect that I'll probably be implementing those sooner or
later, but they're not present in the utility yet.

Some more documentation on various aspects of the Eschalon map that I've
discovered, see http://apocalyptech.com/eschalon/

CONTACT
-------

Feel free to email me at pez@apocalyptech.com if you've got questions /
concerns.  I'm also logged in to irc.freenode.net as the user "sekhmet" if
you'd prefer that.  Note that Freenode requires that you register a nick
before it'll send privmsgs to other users.
